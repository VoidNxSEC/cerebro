# cerebro setup

Interactive configuration and setup wizard.

## Commands

### `cerebro setup wizard`

Start the interactive Cerebro setup wizard. Configures your LLM provider, API keys, and writes them to a local `.env` file.

```bash
cerebro setup wizard
```

**Prompts for:**
- LLM provider (`azure`, `llamacpp`, `vertex-ai`, `gemini`)
- Provider-specific credentials (endpoint, API key, deployment names)
- Vector store (`chroma` or `elasticsearch`) and connection details

**Output:** Writes configuration to `.env` in the current directory.

**Alternative:** Copy `.env.example` to `.env` and fill in values manually.
