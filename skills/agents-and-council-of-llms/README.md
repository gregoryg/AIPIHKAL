# Council of LLMs - Setup & Configuration

This skill enables multi-LLM deliberation for complex problems. Before using it, you must configure which models your Council will use.

## Prerequisites

1. **opencode CLI**: Must be installed and configured with at least one provider (OpenRouter, Anthropic, OpenAI, etc.)
2. **API Keys**: Configured in `opencode` (see `opencode` documentation)

## Step 1: Discover Your Available Models

Run this command to see what models you have access to:

```bash
opencode models
```

This lists all models configured for your `opencode` installation. Note the full model identifiers (e.g., `openrouter/anthropic/claude-3.5-haiku`).

## Step 2: Configure Your Council Models

Create a configuration file at `~/.config/council/models.conf`:

```bash
mkdir -p ~/.config/council
cat > ~/.config/council/models.conf << 'EOF'
# Council of LLMs Model Configuration
# Format: One model per line, full opencode model identifier
# Lines starting with # are comments

# Recommended: Use 3-5 diverse models for good coverage
# Mix providers and model families for varied perspectives

openrouter/openai/gpt-4o-mini
openrouter/anthropic/claude-3.5-haiku
openrouter/google/gemini-2.0-flash-001
EOF
```

### Model Selection Tips

- **Diversity**: Mix model families (OpenAI, Anthropic, Google, open-source) for varied perspectives
- **Cost**: Smaller/faster models work well for council members; save large models for synthesis
- **Speed**: Flash/mini variants keep council sessions under 60 seconds
- **Free tiers**: Some providers offer free models, but they may not support all features

### Example Configurations

**Budget-friendly (free/cheap models):**
```
openrouter/google/gemini-2.0-flash-001
openrouter/openai/gpt-4o-mini
openrouter/mistralai/mistral-small-3.1-24b-instruct
```

**High-quality deliberation:**
```
openrouter/anthropic/claude-3.5-sonnet
openrouter/openai/gpt-4o
openrouter/google/gemini-2.0-pro
```

**Maximum diversity (5 models):**
```
openrouter/anthropic/claude-3.5-haiku
openrouter/openai/gpt-4o-mini
openrouter/google/gemini-2.0-flash-001
openrouter/mistralai/mistral-small-3.1-24b-instruct
openrouter/deepseek/deepseek-chat
```

## Step 3: Test Your Configuration

```bash
# Verify config file exists and is readable
cat ~/.config/council/models.conf

# Test a simple council session
./skills/agents-and-council-of-llms/council-convene.sh \
  --problem "What is 2+2? Explain your reasoning." \
  --count 3
```

## Alternative: Environment Variable

Instead of a config file, you can set models via environment variable:

```bash
export COUNCIL_MODELS="openrouter/openai/gpt-4o-mini,openrouter/anthropic/claude-3.5-haiku,openrouter/google/gemini-2.0-flash-001"
```

## Alternative: Command-Line Override

You can always override models per-session:

```bash
./council-convene.sh \
  --problem "..." \
  --models "openrouter/openai/gpt-4o,openrouter/anthropic/claude-3.5-sonnet"
```

## Troubleshooting

### "Model not found" errors
- Run `opencode models` to verify the exact model identifier
- Check your API keys are configured in `opencode`
- OpenRouter models use format: `openrouter/provider/model-name`

### Sessions timing out
- Council sessions typically take 30-90 seconds
- If your shell tool has a short timeout, use `--prompt-file` mode (see below)
- Consider using faster models (flash/mini variants)

### Complex prompts failing (shell escaping issues)
Use file-based or base64 input:

```bash
# Write prompt to file
echo "Your complex prompt here..." > /tmp/prompt.txt
./council-convene.sh --prompt-file /tmp/prompt.txt --count 3

# Or use base64
prompt_b64=$(echo "Your prompt" | base64 -w0)
./council-convene.sh --prompt-b64 "$prompt_b64" --count 3
```

### Debugging
Enable verbose output:
```bash
COUNCIL_DEBUG=1 ./council-convene.sh --problem "test" --count 2
```

## Environment Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Shell timeout | 120 seconds | 300 seconds |
| Parallel processes | 3 | 5 |
| Disk space | 10 MB | 100 MB (for transcripts) |

## File Locations

| File | Purpose |
|------|---------|
| `~/.config/council/models.conf` | Model configuration |
| `./transcripts/` | Session transcripts (gitignored) |
| `./prompts/` | Prompt templates |
| `council_logs.org` | Session log (created by Council Head) |
