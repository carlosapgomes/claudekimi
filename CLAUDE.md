# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClaudeKimi is a proxy server that enables Claude Code to work with any OpenAI-compatible API. It is a FastAPI proxy server that enables using any OpenAI-compatible API with Claude Code, translating between Anthropic's API format and OpenAI's format. It supports any OpenAI-compatible provider including Groq, DeepInfra, Baseten.

## Quick Start

### Setup and Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit .env with your settings

# Run the proxy
python proxy.py
```

The proxy will start on <http://localhost:7187> by default.

### Using with Claude Code with a one-liner

```bash
env ANTHROPIC_BASE_URL=http://localhost:7187 ANTHROPIC_API_KEY=not_needed CLAUDE_CODE_MAX_OUTPUT_TOKENS=16384  claude
```

You may create a bash script like this and save it to you `~/.local/bin` as `cckimi`:

```bash
#!/bin/bash
env ANTHROPIC_BASE_URL=http://localhost:7187 ANTHROPIC_API_KEY=not_needed CLAUDE_CODE_MAX_OUTPUT_TOKENS=16384  claude "$@"
```

And call it with any ClaudeCode parameters you want.

## Configuration

### Environment Variables (Required)

```bash
# Core configuration
API_KEY=your_api_key                 # API key for your provider
BASE_URL=https://api.groq.com/openai/v1    # OpenAI-compatible endpoint URL
MODEL_NAME=moonshotai/kimi-k2-instruct     # Model name to use

# Optional
MAX_OUTPUT_TOKENS=16384              # Max output tokens (default: 16384)
PROXY_HOST=0.0.0.0                  # Server host (default: localhost)
PROXY_PORT=7187                     # Server port (default: 7187)
```

### Popular Provider Examples

**Groq (Recommended)**

```bash
export API_KEY=gqa_your_key_here
export BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=moonshotai/kimi-k2-instruct
export MAX_OUTPUT_TOKENS=16384
export PROVIDER_NAME=groq
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

## Architecture

### Core Components

- `proxy.py` - Main FastAPI server with request/response transformation
- Anthropic-compliant endpoint at `/v1/messages`
- Tool call support (assistant → tool use → assistant interactions)
- Real-time streaming support planned

### Key Features

- **Provider Agnostic**: Works with any OpenAI-compatible API
- **Tool Support**: Full Claude Code tool integration
- **Auto Detection**: Automatically detects provider from base URL
- **Low Latency**: Direct proxy with minimal overhead
- **Simple Configuration**: 3 required environment variables

## Usage Patterns

### Basic Usage

```bash
# Start proxy
python proxy.py

# In another terminal with claude installed
export ANTHROPIC_BASE_URL=http://localhost:7187
export ANTHROPIC_API_KEY=x
code .  # or claude your-project
```

### Docker Usage

```bash
# Build and run
docker build -t claude-proxy .
docker run -p 7187:7187 \
  -e API_KEY=your_key \
  -e BASE_URL=https://api.groq.com/openai/v1 \
  -e MODEL_NAME=moonshotai/kimi-k2-instruct \
  claude-proxy
```

## Troubleshooting

### Common Issues

- **413 Request Entity Too Large**: Increase `MAX_OUTPUT_TOKENS`
- **Authentication Error**: Verify `API_KEY` is set and valid
- **Model Not Found**: Check exact model name from provider docs

### Debug Mode

```bash
# Enable debug logging
DEBUG=true python proxy.py
```
