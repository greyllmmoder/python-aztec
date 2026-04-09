"""High-volume preset profiles for common Aztec integration flows."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AztecPreset:
    """Preset defaults for common production issuance workflows."""

    name: str
    description: str
    ec_percent: int
    charset: str
    module_size: int
    border: int


PRESETS: dict[str, AztecPreset] = {
    "boarding_pass": AztecPreset(
        name="boarding_pass",
        description="Mobile/print boarding pass payloads with stronger correction defaults.",
        ec_percent=33,
        charset="UTF-8",
        module_size=4,
        border=0,
    ),
    "transit_ticket": AztecPreset(
        name="transit_ticket",
        description="Transit gate/validator payloads optimized for scan reliability.",
        ec_percent=33,
        charset="UTF-8",
        module_size=4,
        border=0,
    ),
    "event_entry": AztecPreset(
        name="event_entry",
        description="Event and venue entry payloads balanced for size and speed.",
        ec_percent=23,
        charset="UTF-8",
        module_size=4,
        border=0,
    ),
    "gs1_label": AztecPreset(
        name="gs1_label",
        description="GS1-style label payloads with ISO-8859-1 compatibility defaults.",
        ec_percent=23,
        charset="ISO-8859-1",
        module_size=4,
        border=0,
    ),
}


def list_presets() -> tuple[str, ...]:
    """Return known preset names sorted for stable UX."""
    return tuple(sorted(PRESETS))


def get_preset(name: str) -> AztecPreset:
    """Resolve a preset by name.

    Raises:
        ValueError: If the preset name is unknown.
    """
    try:
        return PRESETS[name]
    except KeyError as exc:
        known = ", ".join(list_presets())
        raise ValueError(f"Unknown preset '{name}'. Available presets: {known}") from exc

