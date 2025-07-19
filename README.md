# FastAPI Proxy for Claude Code with OpenAI-Compatible APIs

A FastAPI proxy server that enables using any OpenAI-compatible API (Groq, OpenRouter, Ollama, etc.) with Claude Code by translating between Anthropic's API format and OpenAI's format.

## Quick start (uv)

```bash
# Set your API credentials (example with Groq)
export OPENAI_API_KEY=YOUR_GROQ_API_KEY
export OPENAI_BASE_URL=https://api.groq.com/openai/v1
export OPENAI_MODEL_NAME=moonshotai/kimi-k2-instruct

# one-time setup
brew install astral-sh/uv/uv   # or pipx install uv

# project setup
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# run the proxy (default: http://0.0.0.0:7187)
python proxy.py

# Or with custom host/port:
# PROXY_HOST=127.0.0.1 PROXY_PORT=8080 python proxy.py
```

Set the Anthropic Base URL to point to your proxy:

```bash
export ANTHROPIC_BASE_URL=http://localhost:7187
# Or use your custom host:port if configured differently
```

If you're not already authenticated with Anthropic you may need to run:

```
export ANTHROPIC_API_KEY=NOT_NEEDED
```

Run Claude Code:

```bash
claude
```

## Configuration

The proxy supports multiple OpenAI-compatible providers through environment variables:

### Primary Environment Variables
- `OPENAI_API_KEY` - API key for your provider (required)
- `OPENAI_BASE_URL` - Base URL for the OpenAI-compatible API (required)
- `OPENAI_MODEL_NAME` - Model name to use (required)
- `OPENAI_MAX_OUTPUT_TOKENS` - Maximum output tokens (optional, default: 16384)
- `PROVIDER_NAME` - Human-readable provider name (optional, auto-detected)
- `PROXY_HOST` - Host/IP address for the proxy server (optional, default: 0.0.0.0)
- `PROXY_PORT` - Port number for the proxy server (optional, default: 7187)

### Legacy Environment Variables (Groq-specific, still supported)
- `GROQ_API_KEY` - Groq API key (fallback for OPENAI_API_KEY)
- `GROQ_BASE_URL` - Groq base URL (fallback for OPENAI_BASE_URL)
- `GROQ_MODEL` - Groq model name (fallback for OPENAI_MODEL_NAME)
- `GROQ_MAX_OUTPUT_TOKENS` - Groq max tokens (fallback for OPENAI_MAX_OUTPUT_TOKENS)

### Example Configurations

**OpenRouter**
```bash
export OPENAI_API_KEY=your_openrouter_api_key
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
export OPENAI_MODEL_NAME=anthropic/claude-3-haiku
```

**Local Ollama**
```bash
export OPENAI_API_KEY=dummy_key
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_MODEL_NAME=llama3.1
```

**Custom Host/Port**
```bash
export PROXY_HOST=127.0.0.1
export PROXY_PORT=8080
```

## If you use this:

If you use this, I'd love to hear about your experience with different providers and how they compared! Please open an Issue to share your experience.

## Acknowledgements

Inspired by [claude-code-proxy](https://github.com/1rgs/claude-code-proxy)

## License

[MIT](LICENSE.md)
