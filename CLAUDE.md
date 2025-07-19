# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI proxy server that enables using any OpenAI-compatible API with Claude Code. It translates between Anthropic's API format and OpenAI's format, supporting providers like Groq, OpenRouter, local models, and more.

## Commands

### Setup and Development
```bash
# Install uv package manager (if not already installed)
brew install astral-sh/uv/uv  # or: pipx install uv

# Create virtual environment and install dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# Set up environment variables (see Configuration section)
cp .env.example .env  # Create .env file with your settings

# Run the proxy server
python proxy.py

# The proxy will start on http://0.0.0.0:7187 by default
# Or customize the host and port:
# PROXY_HOST=127.0.0.1 PROXY_PORT=8080 python proxy.py
```

### Using with Claude Code
```bash
# Set environment variables to redirect Claude Code to the proxy
export ANTHROPIC_BASE_URL=http://localhost:7187
export ANTHROPIC_API_KEY=NOT_NEEDED  # if not already authenticated

# Run Claude Code as normal
claude
```

## Configuration

The proxy supports multiple OpenAI-compatible providers through environment variables:

### Primary Environment Variables (New Format)
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

**Groq (default)**
```bash
export OPENAI_API_KEY=your_groq_api_key
export OPENAI_BASE_URL=https://api.groq.com/openai/v1
export OPENAI_MODEL_NAME=moonshotai/kimi-k2-instruct
export OPENAI_MAX_OUTPUT_TOKENS=16384
```

**OpenRouter**
```bash
export OPENAI_API_KEY=your_openrouter_api_key
export OPENAI_BASE_URL=https://openrouter.ai/api/v1
export OPENAI_MODEL_NAME=anthropic/claude-3-haiku
export OPENAI_MAX_OUTPUT_TOKENS=4096
```

**Local Ollama**
```bash
export OPENAI_API_KEY=dummy_key
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_MODEL_NAME=llama3.1
export OPENAI_MAX_OUTPUT_TOKENS=2048
```

**OpenAI Official**
```bash
export OPENAI_API_KEY=your_openai_api_key
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL_NAME=gpt-4
export OPENAI_MAX_OUTPUT_TOKENS=4096
```

## Architecture

### Core Components

1. **proxy.py** - Main proxy server implementation
   - FastAPI application that intercepts Anthropic API calls
   - Converts Anthropic message format to OpenAI format for any provider
   - Handles tool use blocks and converts between formats
   - Streams responses back in Anthropic's expected format

### Key Technical Details

- **Host/Port**: Configurable via `PROXY_HOST` and `PROXY_PORT` environment variables (defaults: 0.0.0.0:7187)
- **Authentication**: Requires API key through environment variables
- **Message Conversion**: Handles system prompts, user messages, assistant responses, and tool use blocks
- **Provider Support**: Any OpenAI-compatible API (Groq, OpenRouter, Ollama, etc.)
- **Auto-detection**: Automatically detects provider from base URL

### Claude Code Integration

- `ANTHROPIC_BASE_URL` - Set to http://localhost:7187 when using the proxy (or your custom host:port)
- `ANTHROPIC_API_KEY` - Can be set to any value when using the proxy