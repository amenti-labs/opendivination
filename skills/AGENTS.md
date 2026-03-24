# OpenDivination Skills

This directory contains portable agent skills for OpenDivination.

## Quickstart

```bash
npx skills add amenti-labs/opendivination --skill divination-setup --skill divination
```

Use the skills in this order:

1. Use `divination-setup` first to bootstrap the CLI and write persistent source configuration.
2. Use `divination` after setup for actual oracle calls and interpretation.

## Skills

- `divination-setup` installs or updates OpenDivination, runs first-run setup, stores QRNG
  credentials, and prepares the persistent source configuration.
- `divination` performs tarot draws, I Ching casts, source inspection, and provenance-aware result
  handling.

## References

- `skills/divination-setup/SKILL.md` for install, upgrade, and persistent source setup
- `skills/divination/SKILL.md` for tarot, I Ching, provenance, and runtime behavior
- `skills/divination/references/cli.md` for command examples, QRNG notes, and resonance examples

## Supported Agents

These skills are intended for any coding agent that supports the `SKILL.md` format.
