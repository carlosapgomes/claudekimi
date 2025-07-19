import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from rich import print
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text

load_dotenv()

# Initialize console and logging
console = Console()
DEBUG = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")


def setup_logging():
    level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=True)],
    )
    return logging.getLogger("proxy")


logger = setup_logging()


class ProxyLogger:
    """Beautiful logging utilities for the proxy server"""

    @staticmethod
    def startup_banner(config):
        """Display a beautiful startup banner"""
        print("\n" * 2)
        banner = Panel.fit(
            f"[bold cyan]🚀 ClaudeKimi Proxy Server v0.1.0[/bold cyan]",
            border_style="bright_cyan",
            subtitle="[dim]Anthropic <-> OpenAI Proxy[/dim]",
        )
        console.print(banner)

        # Provider configuration panel
        config_table = Panel(
            f"[bold blue]Provider:[/] [bold white]{config.provider_name.title()}[/bold white]\n"
            f"[bold green]Base URL:[/] [white]{config.base_url}[/white]\n"
            f"[bold magenta]Model:[/] [white]{config.model_name}[/white]\n"
            f"[bold yellow]Max Tokens:[/] [white]{config.max_output_tokens:,}[/white]\n"
            f"[dim]Host: {config.host}:{config.port}[/dim]",
            title="Configuration",
            border_style="bright_blue",
        )
        console.print(config_table)

        # Ready message
        console.print(
            f"\n[bold green]✅ Server ready → http://{config.host}:{config.port}[/bold green]"
        )
        console.print(
            f"[dim]→ Connected to {config.provider_name.title()} via OpenAI-compatible API[/dim]\n"
        )

    @staticmethod
    def request_log(provider, method, endpoint="/v1/messages"):
        """Log incoming requests with consistent formatting"""
        if DEBUG:
            timestamp = datetime.now().strftime("%H:%M:%S")
            console.print(
                f"[dim][{timestamp}][/] [cyan]▶[/cyan] {provider.upper()} {method} {endpoint}"
            )

    @staticmethod
    def response_log(provider, status_code, tokens_in=0, tokens_out=0, duration=""):
        """Log responses with duration and token counts"""
        if DEBUG:
            timestamp = datetime.now().strftime("%H:%M:%S")
            color = "green" if status_code < 400 else "red"
            tokens_str = f" ({tokens_in}→{tokens_out} tokens)" if tokens_in > 0 else ""
            console.print(
                f"[dim][{timestamp}][/] [bold {color}]✓[/bold {color}] {provider.upper()} HTTP {status_code}{tokens_str}"
            )

    @staticmethod
    def tool_usage(name, params):
        """Log tool usage in a clean format"""
        if DEBUG:
            console.print(f"[bold green]🔧 Tool[/] {name}")
            if len(str(params)) < 200:
                console.print(f"  [dim]{json.dumps(params, indent=2)[:150]}[/dim]")
            else:
                console.print(f"  [dim]{json.dumps(params, indent=2)[:80]}...[/dim]")

    @staticmethod
    def tool_result(tool_id, result):
        """Log tool results in a clean format"""
        if DEBUG:
            console.print(f"[bold yellow]📥 Result[/] {tool_id[:8]}")
            result_str = str(result)
            if len(result_str) < 100:
                console.print(f"  [dim]{result_str[:80]}[/dim]")
            else:
                console.print(f"  [dim]{result_str[:60]}...[/dim]")

    @staticmethod
    def error(error_msg, provider_name="proxy"):
        """Log errors cleanly"""
        console.print(f"[bold red]❌ Error[/] {provider_name}: {error_msg}")

    @staticmethod
    def warning(msg):
        """Log warnings"""
        console.print(f"[bold yellow]⚠️ Warning[/] {msg}")

    @staticmethod
    def info(msg):
        """Log info messages"""
        console.print(f"[bold blue]ℹ️[/] {msg}")

    @staticmethod
    def shutdown():
        """Log shutdown message"""
        console.print(f"[bold red]🛑 Proxy Server Shutting Down[/bold red]")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ProxyLogger.startup_banner(config)
    yield
    # Shutdown
    ProxyLogger.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="ClaudeKimi Proxy",
    description="FastAPI proxy for Anthropic <--> OpenAI API conversion",
)


# Configuration with clean, provider-agnostic variable names
class Config:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = os.getenv("BASE_URL", "https://api.groq.com/openai/v1")
        self.model_name = os.getenv("MODEL_NAME", "moonshotai/kimi-k2-instruct")
        self.max_output_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "16384"))
        self.provider_name = os.getenv("PROVIDER_NAME", self._infer_provider_name())
        self.host = os.getenv("PROXY_HOST", "localhost")
        self.port = int(os.getenv("PROXY_PORT", "7187"))

        if not self.api_key:
            raise ValueError("API key is required. Set API_KEY environment variable.")
        if not self.base_url:
            raise ValueError("Base URL is required. Set BASE_URL environment variable.")

    def _infer_provider_name(self) -> str:
        base_lower = self.base_url.lower()
        if "groq.com" in base_lower:
            return "groq"
        elif "openai.com" in base_lower:
            return "openai"
        elif "openrouter.ai" in base_lower:
            return "openrouter"
        elif "ollama" in base_lower:
            return "ollama"
        elif "anthropic.com" in base_lower or "claude" in base_lower:
            return "anthropic"
        elif "novita" in base_lower:
            return "novita"
        elif "baseten" in base_lower:
            return "baseten"
        else:
            return "custom"


config = Config()

client = OpenAI(api_key=config.api_key, base_url=config.base_url)


# ---------- Anthropic Schema ----------
class ContentBlock(BaseModel):
    type: Literal["text"]
    text: str


class ToolUseBlock(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: Dict[str, Union[str, int, float, bool, dict, list]]


class ToolResultBlock(BaseModel):
    type: Literal["tool_result"]
    tool_use_id: str
    content: Union[str, List[Dict[str, Any]], Dict[str, Any], List[Any], Any]


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[Union[ContentBlock, ToolUseBlock, ToolResultBlock]]]


class Tool(BaseModel):
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]


class MessagesRequest(BaseModel):
    model: str
    messages: List[Message]
    max_tokens: Optional[int] = 1024
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False
    tools: Optional[List[Tool]] = None
    tool_choice: Optional[Union[str, Dict[str, str]]] = "auto"


# ---------- Conversion Helpers ----------
def convert_messages(messages: List[Message]) -> List[dict]:
    converted = []
    for m in messages:
        if isinstance(m.content, str):
            converted.append({"role": m.role, "content": m.content})
        else:
            # Handle mixed content blocks
            text_parts = []
            tool_calls = []
            tool_results = []

            for block in m.content:
                if block.type == "text":
                    text_parts.append(block.text)
                elif block.type == "tool_use":
                    # Convert to OpenAI tool call format
                    tool_calls.append(
                        {
                            "id": block.id,
                            "type": "function",
                            "function": {
                                "name": block.name,
                                "arguments": json.dumps(block.input),
                            },
                        }
                    )
                elif block.type == "tool_result":
                    # Convert to OpenAI tool result format
                    result = block.content

                    # Handle different result types
                    if isinstance(result, str):
                        content = result
                    elif isinstance(result, (dict, list)):
                        content = json.dumps(result, ensure_ascii=False)
                    else:
                        content = str(result)

                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.tool_use_id,
                            "content": content,
                        }
                    )

            # Build the message based on content type
            if tool_calls and m.role == "assistant":
                # Assistant message with tool calls
                message = {
                    "role": "assistant",
                    "content": "\n".join(text_parts) if text_parts else None,
                    "tool_calls": tool_calls,
                }
                converted.append(message)
            elif tool_results and m.role in ["user", "tool"]:
                # Tool result messages
                for tool_result in tool_results:
                    converted.append(tool_result)
            else:
                # Regular text message
                converted.append({"role": m.role, "content": "\n".join(text_parts)})
    return converted


def convert_tools(tools: List[Tool]) -> List[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.input_schema,
            },
        }
        for t in tools
    ]


def convert_tool_calls_to_anthropic(tool_calls) -> List[dict]:
    content = []
    for call in tool_calls:
        fn = call.function
        arguments = json.loads(fn.arguments)

        ProxyLogger.tool_usage(fn.name, arguments)

        content.append(
            {"type": "tool_use", "id": call.id, "name": fn.name, "input": arguments}
        )
    return content


# ---------- Request Logging Middleware ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time

    start_time = time.time()
    response = await call_next(request)

    if request.url.path == "/v1/messages" and request.method == "POST":
        duration = f"{time.time() - start_time:.2f}s"
        ProxyLogger.response_log(
            config.provider_name, response.status_code, duration=duration
        )

    return response


# ---------- Main Proxy Route ----------
@app.post("/v1/messages")
async def proxy(request: MessagesRequest):
    # Log the request with both requested and real model names
    console.print(
        f"[bold cyan]Anthropic → {config.provider_name.title()}[/bold cyan] | [bold white]Model:[/bold white] [cyan]{request.model}[/cyan] → [green]{config.model_name}[/green]"
    )

    try:
        openai_messages = convert_messages(request.messages)
        tools = convert_tools(request.tools) if request.tools else None

        max_tokens = min(
            request.max_tokens or config.max_output_tokens, config.max_output_tokens
        )

        if request.max_tokens and request.max_tokens > config.max_output_tokens:
            ProxyLogger.warning(
                f"Capping max_tokens from {request.max_tokens} to {config.max_output_tokens}"
            )

        # Build completion parameters
        completion_params = {
            "model": config.model_name,
            "messages": openai_messages,
            "temperature": request.temperature,
            "max_tokens": max_tokens,
        }

        # Only add tools and tool_choice if tools are provided
        if tools:
            completion_params["tools"] = tools
            completion_params["tool_choice"] = request.tool_choice

        completion = client.chat.completions.create(**completion_params)

        choice = completion.choices[0]
        msg = choice.message

        # Convert OpenAI response back to Anthropic format
        content = []

        # Add text content if present
        if msg.content:
            content.append({"type": "text", "text": msg.content})

        # Add tool calls if present
        if msg.tool_calls:
            tool_content = convert_tool_calls_to_anthropic(msg.tool_calls)
            content.extend(tool_content)
            stop_reason = "tool_use"
        else:
            # Check if response was truncated due to max_tokens
            if choice.finish_reason == "length":
                stop_reason = "max_tokens"
            else:
                stop_reason = "end_turn"

        # If no content, add empty text block
        if not content:
            content = [{"type": "text", "text": ""}]

        # Log token usage
        ProxyLogger.response_log(
            config.provider_name,
            200,
            tokens_in=completion.usage.prompt_tokens,
            tokens_out=completion.usage.completion_tokens,
        )

        return {
            "id": f"msg_{uuid.uuid4().hex[:12]}",
            "model": f"{config.provider_name}/{config.model_name}",
            "role": "assistant",
            "type": "message",
            "content": content,
            "stop_reason": stop_reason,
            "stop_sequence": None,
            "usage": {
                "input_tokens": completion.usage.prompt_tokens,
                "output_tokens": completion.usage.completion_tokens,
            },
        }
    except Exception as e:
        ProxyLogger.error(str(e), config.provider_name)
        raise HTTPException(
            status_code=500,
            detail=f"Error calling {config.provider_name} API: {str(e)}",
        )


@app.get("/")
def root():
    return {
        "status": "healthy",
        "provider": config.provider_name,
        "model": config.model_name,
        "version": "1.0.0",
        "uptime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    uvicorn.run(app, host=config.host, port=config.port, reload=False)
