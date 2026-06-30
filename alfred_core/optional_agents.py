"""Optional-agent catalog adapted from Alfred Dev for Codex role routing."""

from __future__ import annotations

from typing import Any, Iterable

OPTIONAL_AGENT_CATALOG: dict[str, dict[str, Any]] = {
    "data-engineer": {
        "group": "technical",
        "label": "Data Engineer",
        "specialty": "Data modeling, migrations, queries, and persistence",
        "integration": {
            "fases": ["arquitectura", "desarrollo", "ejecucion_acotada", "diagnostico", "correccion"],
            "posicion": "paralelo",
        },
    },
    "performance-engineer": {
        "group": "technical",
        "label": "Performance Engineer",
        "specialty": "Profiling, latency, bundles, memory, and bottlenecks",
        "integration": {
            "fases": ["calidad", "validacion_rapida", "diagnostico", "validacion"],
            "posicion": "paralelo",
        },
    },
    "github-manager": {
        "group": "technical",
        "label": "GitHub Manager",
        "specialty": "PRs, releases, issues, labels, and repository coordination",
        "integration": {
            "fases": ["entrega", "empaquetado", "despliegue"],
            "posicion": "secuencial",
        },
    },
    "librarian": {
        "group": "technical",
        "label": "Librarian",
        "specialty": "Persistent memory, prior decisions, and project chronology",
        "runtime_mode": "on_demand",
        "integration": {
            "fases": [],
            "posicion": "none",
        },
    },
    "ux-reviewer": {
        "group": "content",
        "label": "UX Reviewer",
        "specialty": "Accessibility, usability, and interface flows",
        "integration": {
            "fases": ["calidad", "producto", "ejecucion_acotada", "validacion_rapida", "diagnostico", "validacion"],
            "posicion": "paralelo",
        },
    },
    "seo-specialist": {
        "group": "content",
        "label": "SEO Specialist",
        "specialty": "Technical SEO, structured data, and Core Web Vitals",
        "integration": {
            "fases": ["calidad", "validacion_rapida", "validacion"],
            "posicion": "paralelo",
        },
    },
    "copywriter": {
        "group": "content",
        "label": "Copywriter",
        "specialty": "Microcopy, CTAs, tone, and visible user text",
        "integration": {
            "fases": ["documentacion", "ejecucion_acotada", "correccion"],
            "posicion": "paralelo",
        },
    },
    "i18n-specialist": {
        "group": "content",
        "label": "i18n Specialist",
        "specialty": "Internationalization, locales, and hardcoded strings",
        "integration": {
            "fases": ["desarrollo", "calidad", "ejecucion_acotada", "validacion_rapida", "correccion", "validacion"],
            "posicion": "paralelo",
        },
    },
    "lucius": {
        "group": "audit",
        "label": "Lucius",
        "specialty": "External technical second opinion and closing audit",
        "integration": {
            "fases": ["calidad", "validacion_rapida", "validacion", "auditoria_final", "auditoria_paralela"],
            "posicion": "secuencial",
        },
    },
}


def get_optional_agent_names() -> tuple[str, ...]:
    """Return canonical optional-agent names."""
    return tuple(OPTIONAL_AGENT_CATALOG.keys())


def build_optional_agent_flags(default: bool = False) -> dict[str, bool]:
    """Build a config block with every optional agent enabled or disabled."""
    return {name: bool(default) for name in get_optional_agent_names()}


def get_optional_integrations() -> dict[str, dict[str, Any]]:
    """Return phase integration metadata."""
    return {
        name: {
            "fases": list(meta["integration"]["fases"]),
            "posicion": meta["integration"]["posicion"],
        }
        for name, meta in OPTIONAL_AGENT_CATALOG.items()
    }


def order_optional_agent_names(names: Iterable[str]) -> list[str]:
    """Order optional agents using the catalog order, preserving unknowns last."""
    unique = []
    for raw in names:
        name = str(raw).strip()
        if name and name not in unique:
            unique.append(name)
    known = [name for name in get_optional_agent_names() if name in unique]
    unknown = sorted(name for name in unique if name not in OPTIONAL_AGENT_CATALOG)
    return known + unknown
