"""User-facing configuration models and loaders for OpenDivination."""

from __future__ import annotations

import os
from contextlib import suppress
from pathlib import Path
from string import Formatter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from opendivination.types import DEFAULT_ENTROPY_SOURCE

_TAROT_TEMPLATE_FIELDS = {
    "name",
    "number",
    "suit",
    "arcana",
    "keywords",
    "visual_caption",
}


def _validate_template_fields(template: str) -> str:
    for _, field_name, _, _ in Formatter().parse(template):
        if field_name is None:
            continue
        if field_name not in _TAROT_TEMPLATE_FIELDS:
            allowed = ", ".join(sorted(_TAROT_TEMPLATE_FIELDS))
            raise ValueError(
                f"Unsupported tarot text template field '{field_name}'. "
                f"Allowed fields: {allowed}"
            )
    return template


class TarotCardTextProfileConfig(BaseModel):
    """Configurable text template and per-card overrides for one tarot profile."""

    model_config = ConfigDict(extra="forbid")

    template: str | None = None
    overrides: dict[str, str] = Field(default_factory=dict)

    @field_validator("template")
    @classmethod
    def validate_template(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_template_fields(value)


class TarotCardTextConfig(BaseModel):
    """Configured card-text profiles keyed by profile id."""

    model_config = ConfigDict(extra="forbid")

    profiles: dict[str, TarotCardTextProfileConfig] = Field(default_factory=dict)


class TarotConfig(BaseModel):
    """Tarot-specific user configuration."""

    model_config = ConfigDict(extra="forbid")

    card_text: TarotCardTextConfig = Field(default_factory=TarotCardTextConfig)


class RemoteSourceConfig(BaseModel):
    """Configurable settings for one remote QRNG provider."""

    model_config = ConfigDict(extra="forbid")

    api_key: str | None = None


class SourcesConfig(BaseModel):
    """Configured entropy-source defaults and remote-provider credentials."""

    model_config = ConfigDict(extra="forbid")

    default: str = DEFAULT_ENTROPY_SOURCE
    anu: RemoteSourceConfig = Field(default_factory=RemoteSourceConfig)
    outshift: RemoteSourceConfig = Field(default_factory=RemoteSourceConfig)


class ResonanceDefaultsConfig(BaseModel):
    """Optional defaults for resonance provider selection."""

    model_config = ConfigDict(extra="forbid")

    provider: str = "local"
    model: str | None = "nomic-embed-text"


class DefaultsConfig(BaseModel):
    """Top-level UX defaults written by guided setup."""

    model_config = ConfigDict(extra="forbid")

    resonance: ResonanceDefaultsConfig = Field(default_factory=ResonanceDefaultsConfig)


class OpenDivinationConfig(BaseModel):
    """Root user configuration for OpenDivination."""

    model_config = ConfigDict(extra="forbid")

    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    tarot: TarotConfig = Field(default_factory=TarotConfig)


def default_config_path() -> Path:
    """Return the default JSON config path for OpenDivination."""

    configured = os.getenv("OPENDIVINE_CONFIG")
    if configured:
        return Path(configured).expanduser()
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    base_dir = Path(xdg_config_home).expanduser() if xdg_config_home else Path.home() / ".config"
    return base_dir / "opendivination" / "config.json"


def load_config(
    path: str | Path | None = None,
    *,
    allow_missing: bool = True,
) -> OpenDivinationConfig:
    """Load user config from JSON, or return an empty config if missing."""

    resolved_path = Path(path).expanduser() if path is not None else default_config_path()
    if not resolved_path.exists():
        if allow_missing:
            return OpenDivinationConfig()
        raise FileNotFoundError(f"OpenDivination config not found: {resolved_path}")
    return OpenDivinationConfig.model_validate_json(resolved_path.read_text(encoding="utf-8"))


def save_config(
    config: OpenDivinationConfig,
    path: str | Path | None = None,
) -> Path:
    """Persist config JSON and tighten file permissions for stored credentials."""

    resolved_path = Path(path).expanduser() if path is not None else default_config_path()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_path.write_text(
        config.model_dump_json(indent=2, exclude_none=True) + "\n",
        encoding="utf-8",
    )
    with suppress(OSError):
        resolved_path.chmod(0o600)
    return resolved_path


def configured_default_source(path: str | Path | None = None) -> str:
    """Return configured default source, or csprng when unset."""

    return load_config(path, allow_missing=True).sources.default


def configured_remote_source_api_key(
    source_name: Literal["anu", "outshift"],
    path: str | Path | None = None,
) -> str | None:
    """Return configured API key for a supported remote QRNG provider."""

    config = load_config(path, allow_missing=True)
    if source_name == "anu":
        return config.sources.anu.api_key
    return config.sources.outshift.api_key


__all__ = [
    "DefaultsConfig",
    "OpenDivinationConfig",
    "RemoteSourceConfig",
    "ResonanceDefaultsConfig",
    "SourcesConfig",
    "configured_default_source",
    "configured_remote_source_api_key",
    "TarotCardTextConfig",
    "TarotCardTextProfileConfig",
    "TarotConfig",
    "default_config_path",
    "load_config",
    "save_config",
]
