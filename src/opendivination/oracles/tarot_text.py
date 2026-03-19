"""Tarot card text rendering helpers."""

from __future__ import annotations

from opendivination.config import OpenDivinationConfig
from opendivination.types import ResonanceAssetTextProfile, TarotCard

_SUPPORTED_TAROT_TEXT_PROFILES = (
    ResonanceAssetTextProfile.DESCRIPTIVE,
)


def _resolve_asset_text_profile(
    profile: ResonanceAssetTextProfile,
) -> ResonanceAssetTextProfile:
    if profile is ResonanceAssetTextProfile.AUTO:
        return ResonanceAssetTextProfile.DESCRIPTIVE
    return profile


def _card_template_context(card: TarotCard) -> dict[str, str | int]:
    suit = card.suit if card.suit is not None else "major arcana"
    return {
        "name": card.name,
        "number": card.number,
        "suit": suit,
        "arcana": card.arcana,
        "keywords": ", ".join(card.keywords),
        "visual_caption": card.visual_caption or "",
    }


def _configured_card_text(
    card: TarotCard,
    *,
    profile: ResonanceAssetTextProfile,
    config: OpenDivinationConfig | None,
) -> str | None:
    if config is None:
        return None
    profile_config = config.tarot.card_text.profiles.get(profile.value)
    if profile_config is None:
        return None
    if card.name in profile_config.overrides:
        return profile_config.overrides[card.name]
    if profile_config.template is None:
        return None
    return profile_config.template.format(**_card_template_context(card))


def build_tarot_card_text(
    card: TarotCard,
    profile: ResonanceAssetTextProfile = ResonanceAssetTextProfile.DESCRIPTIVE,
    *,
    config: OpenDivinationConfig | None = None,
) -> str:
    """Build the text representation for a tarot card."""

    resolved_profile = _resolve_asset_text_profile(profile)
    configured = _configured_card_text(card, profile=resolved_profile, config=config)
    if configured is not None:
        return configured

    context = _card_template_context(card)
    name = str(context["name"])
    suit = str(context["suit"])
    arcana = str(context["arcana"])
    keywords = str(context["keywords"])
    parts = [
        f"Tarot card: {name}.",
        f"Arcana: {arcana}.",
        f"Suit: {suit}.",
        f"Keywords: {keywords}.",
    ]
    if card.description:
        parts.append(card.description)
    return " ".join(parts)


def build_tarot_card_text_views(
    card: TarotCard,
    *,
    config: OpenDivinationConfig | None = None,
) -> dict[str, str]:
    """Build all supported symbolic text views for one tarot card."""

    return {
        profile.value: build_tarot_card_text(card, profile, config=config)
        for profile in _SUPPORTED_TAROT_TEXT_PROFILES
    }


def configured_tarot_text_profiles(
    config: OpenDivinationConfig | None,
) -> set[str]:
    """Return the configured tarot text profile ids."""

    if config is None:
        return set()
    return set(config.tarot.card_text.profiles)


__all__ = [
    "build_tarot_card_text",
    "build_tarot_card_text_views",
    "configured_tarot_text_profiles",
]
