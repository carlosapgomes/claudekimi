# ClaudeKimi
ClaudeKimi is an enhanced proxy for AI-assisted coding, based on [fakerybakery/claude-code-kimi-groq](https://github.com/fakerybakery/claude-code-kimi-groq). It enables Claude Code to work with Kimi K2 and adds support for multiple inference providers, including DeepInfra and BaseTen. Licensed under the MIT License (see [LICENSE.md](LICENSE.md) for details).

## Features
- Seamless integration of Claude Code with Kimi K2.
- Extended support for additional inference providers (DeepInfra, BaseTen).
- Improvements to tool-calling functionality.

## Quick start (uv)

```bash
# Set your API credentials (example with Groq)
export API_KEY=YOUR_GROQ_API_KEY
export BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=moonshotai/kimi-k2-instruct

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

The proxy uses clean, provider-agnostic environment variables for any OpenAI-compatible API provider.

### **Required Configuration**

- `API_KEY` - API key for your provider (required)
- `BASE_URL` - Base URL for your OpenAI-compatible API provider (required)
- `MODEL_NAME` - Model name to use with your provider (required)

### **Optional Configuration**

- `MAX_OUTPUT_TOKENS` - Maximum output tokens (default: 16384)
- `PROVIDER_NAME` - Human-readable provider name (auto-detected if not provided)
- `PROXY_HOST` - Host/IP address for the proxy server (default: 0.0.0.0)
- `PROXY_PORT` - Port number for the proxy server (default: 7187)

### **Claude Code Integration Variables**

- `ANTHROPIC_BASE_URL` - Set to <http://localhost:7187> when using the proxy
- `ANTHROPIC_API_KEY` - Can be set to any value when using the proxy (optional)

### **Example Configurations**

**Quick Start (Groq default)**

```bash
export API_KEY=your_groq_api_key_here
export BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=moonshotai/kimi-k2-instruct
```

**OpenRouter**

```bash
export API_KEY=your_openrouter_api_key
export BASE_URL=https://openrouter.ai/api/v1
export MODEL_NAME=anthropic/claude-3-haiku
export PROVIDER_NAME=openrouter
```

**Local Ollama**

```bash
export API_KEY=dummy_key
export BASE_URL=http://localhost:11434/v1
export MODEL_NAME=llama3.1
export PROVIDER_NAME=ollama
```

**Custom Host/Port**

```bash
export PROXY_HOST=127.0.0.1
export PROXY_PORT=8080
```

## If you use this

If you use this, I'd love to hear about your experience with different providers and how they compared! Please open an Issue to share your experience.

## Acknowledgements

Inspired by [claude-code-proxy](https://github.com/1rgs/claude-code-proxy)

## License

[MIT](LICENSE.md)
