# ClaudeKimi

ClaudeKimi is an enhanced proxy for AI-assisted coding, based on [fakerybakery/claude-code-kimi-groq](https://github.com/fakerybakery/claude-code-kimi-groq). It enables Claude Code to work with Kimi K2 and adds support for multiple inference providers, including DeepInfra and BaseTen. Licensed under the MIT License (see [LICENSE.md](LICENSE.md) for details).

## Features

- Seamless integration of Claude Code with Kimi K2.
- Tested with additional inference providers (DeepInfra, BaseTen).
- Improvements to tool-calling functionality.

## Quick start (uv)

Install [uv](https://github.com/astral-sh/uv) (Unix Virtualenv) to manage the proxy's dependencies.

The recommended way to configure the proxy is copying `.env.example` to `.env` and editing it with your API credentials.

```bash
# one-time setup
# project setup
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# run the proxy (default: http://127.0.0.1:7187)
python proxy.py

```

## Running Claude Code

### One-liner

```bash
env ANTHROPIC_BASE_URL=http://localhost:7187 ANTHROPIC_API_KEY=not_needed CLAUDE_CODE_MAX_OUTPUT_TOKENS=16384  claude
```

### Custom script

You may create a bash script like this and save it to you `~/.local/bin` as `cckimi`:

```bash
#!/bin/bash
env ANTHROPIC_BASE_URL=http://localhost:7187 ANTHROPIC_API_KEY=not_needed CLAUDE_CODE_MAX_OUTPUT_TOKENS=16384  claude "$@"
```

Call it with any ClaudeCode parameters you want.

## Configuration

The proxy uses clean, provider-agnostic environment variables for any OpenAI-compatible API provider.

### **Required Configuration**

- `API_KEY` - API key for your provider (required)
- `BASE_URL` - Base URL for your OpenAI-compatible API provider (required)
- `MODEL_NAME` - Model name to use with your provider (required)

### **Optional Configuration**

- `MAX_OUTPUT_TOKENS` - Maximum output tokens (default: 16384)
- `PROVIDER_NAME` - Human-readable provider name (auto-detected if not provided)
- `PROXY_HOST` - Host/IP address for the proxy server (default: localhost)
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
export MAX_OUTPUT_TOKENS=16384
export PROVIDER_NAME=deepinfra
```

**DeppInfra**

```bash
export API_KEY=your_deepinfra_api_key_here
export BASE_URL=https://api.deepinfra.com/v1/openai
export MODEL_NAME=moonshotai/Kimi-K2-Instruct
export MAX_OUTPUT_TOKENS=16384
export PROVIDER_NAME=deepinfra
```

**BaseTen**

```bash
export API_KEY=your_baseten_api_key_here
export BASE_URL=https://inference.baseten.co/v1
export MODEL_NAME=moonshotai/Kimi-K2-Instruct
export MAX_OUTPUT_TOKENS=16384
export PROVIDER_NAME=baseten
```

**Custom Host/Port**

```bash
export PROXY_HOST=127.0.0.1
export PROXY_PORT=8080
```

## If you use this

If you use this, I'd love to hear about your experience with different providers and how they compared! Please open an Issue to share your experience.

## Acknowledgements

Based on [fakerybakery/claude-code-kimi-groq](https://github.com/fakerybakery/claude-code-kimi-groq)

## License

[MIT](LICENSE.md)
