import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, Optional, Union

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from rich import print

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[bold green]🚀 Proxy Server Starting[/bold green]")
    print(f"[bold blue]📡 Provider: {config.provider_name.title()}[/bold blue]")
    print(f"[bold blue]🔗 Base URL: {config.base_url}[/bold blue]")
    print(f"[bold blue]🤖 Model: {config.model_name}[/bold blue]")
    print(f"[bold blue]🎯 Max Output Tokens: {config.max_output_tokens}[/bold blue]")
    print(f"[bold blue]🌐 Listening on: http://{config.host}:{config.port}[/bold blue]")
    print(f"[bold yellow]💡 Ready to proxy Anthropic API calls to {config.provider_name.title()}![/bold yellow]")
    yield
    # Shutdown
    print(f"[bold red]🛑 Proxy Server Shutting Down[/bold red]")


app = FastAPI(lifespan=lifespan)

# Configuration with defaults
class Config:
    def __init__(self):
        self.api_key = (os.getenv("OPENAI_COMPATIBLE_API_KEY") or 
                       os.getenv("OPENAI_API_KEY") or 
                       os.getenv("GROQ_API_KEY"))
        self.base_url = (os.getenv("OPENAI_COMPATIBLE_BASE_URL") or 
                        os.getenv("OPENAI_BASE_URL") or 
                        os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))
        self.model_name = (os.getenv("OPENAI_COMPATIBLE_MODEL_NAME") or 
                          os.getenv("OPENAI_MODEL_NAME") or 
                          os.getenv("GROQ_MODEL", "moonshotai/kimi-k2-instruct"))
        self.max_output_tokens = int(os.getenv("OPENAI_COMPATIBLE_MAX_OUTPUT_TOKENS") or 
                                   os.getenv("OPENAI_MAX_OUTPUT_TOKENS") or 
                                   os.getenv("GROQ_MAX_OUTPUT_TOKENS", "16384"))
        self.provider_name = os.getenv("OPENAI_COMPATIBLE_PROVIDER_NAME") or os.getenv("PROVIDER_NAME", self._infer_provider_name())
        self.host = os.getenv("PROXY_HOST", "0.0.0.0")
        self.port = int(os.getenv("PROXY_PORT", "7187"))
        
        if not self.api_key:
            raise ValueError("API key is required. Set OPENAI_API_KEY environment variable.")
        if not self.base_url:
            raise ValueError("Base URL is required. Set OPENAI_BASE_URL environment variable.")
    
    def _infer_provider_name(self) -> str:
        if "groq.com" in self.base_url:
            return "groq"
        elif "openai.com" in self.base_url:
            return "openai"
        elif "openrouter.ai" in self.base_url:
            return "openrouter"
        else:
            return "custom"

config = Config()

client = OpenAI(
    api_key=config.api_key, 
    base_url=config.base_url
)


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
                    tool_calls.append({
                        "id": block.id,
                        "type": "function",
                        "function": {
                            "name": block.name,
                            "arguments": json.dumps(block.input)
                        }
                    })
                    print(f"[bold green]🛠 Tool Call: {block.name}({json.dumps(block.input, indent=2)})[/bold green]")
                elif block.type == "tool_result":
                    # Convert to OpenAI tool result format
                    result = block.content
                    print(f"[bold yellow]📥 Tool Result for {block.tool_use_id}: {json.dumps(result, indent=2)}[/bold yellow]")
                    
                    # Handle different result types and ensure JSON-safe content
                    if isinstance(result, str):
                        content = result
                    elif isinstance(result, (dict, list)):
                        content = json.dumps(result, ensure_ascii=False)
                    else:
                        content = str(result)
                    
                    # Ensure content is JSON-safe by removing/escaping control characters
                    if isinstance(content, str):
                        content = content.encode('unicode_escape').decode('ascii')
                    
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": block.tool_use_id,
                        "content": content
                    })
            
            # Build the message based on content type
            if tool_calls:
                # Assistant message with tool calls
                message = {
                    "role": "assistant",
                    "content": "\n".join(text_parts) if text_parts else None,
                    "tool_calls": tool_calls
                }
                converted.append(message)
            elif tool_results:
                # Add tool result messages
                for tool_result in tool_results:
                    converted.append(tool_result)
            else:
                # Regular text message
                converted.append({
                    "role": m.role,
                    "content": "\n".join(text_parts)
                })
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

        print(f"[bold green]🛠 Tool Call: {fn.name}({json.dumps(arguments, indent=2)})[/bold green]")

        content.append(
            {"type": "tool_use", "id": call.id, "name": fn.name, "input": arguments}
        )
    return content


# ---------- Main Proxy Route ----------


@app.post("/v1/messages")
async def proxy(request: MessagesRequest):
    print(f"[bold cyan]🚀 Anthropic → {config.provider_name.title()} | Model: {request.model} → {config.model_name}[/bold cyan]")

    try:
        openai_messages = convert_messages(request.messages)
        tools = convert_tools(request.tools) if request.tools else None
        
        max_tokens = min(request.max_tokens or config.max_output_tokens, config.max_output_tokens)
        
        if request.max_tokens and request.max_tokens > config.max_output_tokens:
            print(f"[bold yellow]⚠️  Capping max_tokens from {request.max_tokens} to {config.max_output_tokens}[/bold yellow]")


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
        print(f"[bold red]❌ Error calling {config.provider_name} API: {str(e)}[/bold red]")
        raise HTTPException(status_code=500, detail=f"Error calling {config.provider_name} API: {str(e)}")


@app.get("/")
def root():
    return {
        "message": f"OpenAI-to-Anthropic Proxy is alive 💡", 
        "provider": config.provider_name,
        "model": config.model_name,
        "base_url": config.base_url
    }



if __name__ == "__main__":
    uvicorn.run(app, host=config.host, port=config.port)
