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

Never commit API keys to version control. OpenDivine reads keys from environment variables only:
- `QBERT_API_KEY`
- `ANU_API_KEY`
- `OUTSHIFT_API_KEY`
