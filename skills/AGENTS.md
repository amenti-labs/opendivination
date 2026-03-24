# OpenDivination Skills

This directory contains portable agent skills for OpenDivination.

## Install

```bash
npx skills add amenti-labs/opendivination --skill divination-setup --skill divination
```

## Skills

- `divination-setup` installs or updates OpenDivination, runs first-run setup, stores QRNG
  credentials, and prepares the persistent source configuration.
- `divination` performs tarot draws, I Ching casts, source inspection, and provenance-aware result
  handling.

## Suggested Flow

1. Use `divination-setup` first when the agent needs to bootstrap the CLI or write persistent
   configuration.
2. Use `divination` after setup for actual oracle calls and interpretation.

## Supported Agents

These skills are intended for any coding agent that supports the `SKILL.md` format.
