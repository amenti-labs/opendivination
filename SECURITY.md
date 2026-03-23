# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please do not report security vulnerabilities through public GitHub issues.

Send a description of the vulnerability to: security@amentilabs.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 72 hours. If the issue is confirmed, we will release a patch as soon as possible.

## API Key Security

Never commit API keys to version control. OpenDivination reads keys from environment variables only.

### QRNG source keys
- `ANU_API_KEY`
- `OUTSHIFT_API_KEY`

### Embedding provider keys
- `OPENAI_API_KEY`
- `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- `OPENAI_COMPATIBLE_API_KEY`

### Data handling

When using cloud embedding providers (`openai`, `gemini`, `openai_compatible`), your question text
and symbol descriptions are sent to external APIs for embedding. Use `local`, `ollama`, or
`sentence_transformers` providers to keep all data on your machine.
