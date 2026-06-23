# Security Policy

StackSleuth is currently in the planning stage. Do not use it against production systems until the implementation, tests, and guardrails are complete.

## Secret Handling

- Never commit `.env`.
- Commit `.env.example` only.
- Never commit OpenAI API keys, database passwords, GitHub tokens, or service credentials.
- Do not place real user data in sample logs, seed data, or trace examples.

## Reporting Issues

If this repository becomes public and you find a security issue, open a GitHub issue with a minimal reproduction that does not include secrets or private data.

