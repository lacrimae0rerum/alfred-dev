"""Alfred Codex flow definitions, gates, and state transitions."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .optional_agents import get_optional_integrations
from .paths import ensure_state_root, state_path

GATE_LIBRE = "libre"
GATE_USUARIO = "usuario"
GATE_AUTOMATICO = "automatico"
GATE_USUARIO_SEGURIDAD = "usuario+seguridad"
GATE_AUTOMATICO_SEGURIDAD = "automatico+seguridad"

KNOWN_GATE_TYPES = {
    GATE_LIBRE,
    GATE_USUARIO,
    GATE_AUTOMATICO,
    GATE_USUARIO_SEGURIDAD,
    GATE_AUTOMATICO_SEGURIDAD,
}

MAX_PHASE_ITERATIONS = 5

FLOWS: dict[str, dict[str, Any]] = {
    "feature": {
        "nombre": "feature",
        "fases": [
            {
                "nombre": "producto",
                "agentes": ["product-owner"],
                "paralelo": False,
                "gate": "gate_producto",
                "gate_tipo": GATE_USUARIO,
                "descripcion": "Requirements, scope, user stories, and acceptance criteria.",
            },
            {
                "nombre": "estilo_visual",
                "agentes": ["selina"],
                "paralelo": False,
                "gate": "gate_estilo",
                "gate_tipo": GATE_USUARIO,
                "condicion": "tiene_frontend",
                "descripcion": "Visual direction for projects with a user interface.",
            },
            {
                "nombre": "arquitectura",
                "agentes": ["architect", "security-officer"],
                "paralelo": True,
                "gate": "gate_arquitectura",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "descripcion": "Technical design and threat model.",
            },
            {
                "nombre": "desarrollo",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_desarrollo",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": "Implementation with behavior tests.",
            },
            {
                "nombre": "calidad",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_calidad",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": "Quality review, regression checks, and security review.",
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion",
                "gate_tipo": GATE_LIBRE,
                "descripcion": "Technical and user documentation.",
            },
            {
                "nombre": "entrega",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_entrega",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "descripcion": "Delivery preparation, changelog, and final security signoff.",
            },
        ],
    },
    "fix": {
        "nombre": "fix",
        "fases": [
            {
                "nombre": "diagnostico",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_diagnostico",
                "gate_tipo": GATE_USUARIO,
                "descripcion": "Reproduce the bug and identify root cause.",
            },
            {
                "nombre": "correccion",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_correccion",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": "Add regression test and implement the fix.",
            },
            {
                "nombre": "validacion",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_validacion",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": "Regression suite and security validation.",
            },
        ],
    },
    "quick": {
        "nombre": "quick",
        "fases": [
            {
                "nombre": "ejecucion_acotada",
                "agentes": ["senior-dev"],
                "paralelo": False,
                "gate": "gate_ejecucion_acotada",
                "gate_tipo": GATE_AUTOMATICO,
                "descripcion": "Small local implementation with scoped tests.",
            },
            {
                "nombre": "validacion_rapida",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_validacion_rapida",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": "Focused regression and security validation.",
            },
        ],
    },
    "spike": {
        "nombre": "spike",
        "fases": [
            {
                "nombre": "exploracion",
                "agentes": ["architect", "senior-dev"],
                "paralelo": True,
                "gate": "gate_exploracion",
                "gate_tipo": GATE_LIBRE,
                "descripcion": "Explore alternatives, prototypes, and evidence.",
            },
            {
                "nombre": "conclusiones",
                "agentes": ["architect"],
                "paralelo": False,
                "gate": "gate_conclusiones",
                "gate_tipo": GATE_USUARIO,
                "descripcion": "Document findings, recommendation, risks, and next step.",
            },
        ],
    },
    "ship": {
        "nombre": "ship",
        "fases": [
            {
                "nombre": "auditoria_final",
                "agentes": ["qa-engineer", "security-officer"],
                "paralelo": True,
                "gate": "gate_auditoria_final",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": "Final quality and security audit.",
            },
            {
                "nombre": "documentacion",
                "agentes": ["tech-writer"],
                "paralelo": False,
                "gate": "gate_documentacion_ship",
                "gate_tipo": GATE_LIBRE,
                "descripcion": "Release notes, changelog, and updated docs.",
            },
            {
                "nombre": "empaquetado",
                "agentes": ["devops-engineer", "security-officer"],
                "paralelo": False,
                "gate": "gate_empaquetado",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": "Build, version, tag, and prepare deploy artifact.",
            },
            {
                "nombre": "despliegue",
                "agentes": ["devops-engineer"],
                "paralelo": False,
                "gate": "gate_despliegue",
                "gate_tipo": GATE_USUARIO_SEGURIDAD,
                "autopilot_force_user_confirmation": True,
                "descripcion": "Production deployment with explicit user confirmation.",
            },
        ],
    },
    "audit": {
        "nombre": "audit",
        "fases": [
            {
                "nombre": "auditoria_paralela",
                "agentes": ["qa-engineer", "security-officer", "architect", "tech-writer"],
                "paralelo": True,
                "gate": "gate_auditoria",
                "gate_tipo": GATE_AUTOMATICO_SEGURIDAD,
                "descripcion": "Parallel audit of quality, security, architecture, and docs.",
            },
        ],
    },
}

OPTIONAL_INTEGRATIONS = get_optional_integrations()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _phase_enabled(phase: dict[str, Any], context: dict[str, Any]) -> bool:
    condition = phase.get("condicion")
    if condition == "tiene_frontend":
        return bool(context.get("has_frontend", True))
    return True


def _advance_skipping_phases(session: dict[str, Any], next_index: int) -> int:
    phases = FLOWS[session["comando"]]["fases"]
    context = session.get("context", {})
    while next_index < len(phases) and not _phase_enabled(phases[next_index], context):
        session["fases_completadas"].append(
            {
                "nombre": phases[next_index]["nombre"],
                "resultado": "saltada",
                "artefactos": [],
                "completada_en": _now(),
                "iteraciones": 0,
            }
        )
        next_index += 1
    return next_index


def create_session(
    command: str,
    description: str,
    *,
    context: dict[str, Any] | None = None,
    autopilot: bool = False,
    equipo_sesion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new flow session."""
    if command not in FLOWS:
        raise ValueError(f"Unknown flow: {command}")
    session = {
        "comando": command,
        "descripcion": description,
        "fase_actual": FLOWS[command]["fases"][0]["nombre"],
        "fase_numero": 0,
        "fases_completadas": [],
        "artefactos": [],
        "autopilot": bool(autopilot),
        "equipo_sesion": equipo_sesion,
        "context": dict(context or {}),
        "iteraciones_fase": 0,
        "max_iteraciones_fase": MAX_PHASE_ITERATIONS,
        "creado_en": _now(),
        "actualizado_en": _now(),
    }
    first_index = _advance_skipping_phases(session, 0)
    if first_index >= len(FLOWS[command]["fases"]):
        session["fase_actual"] = "completado"
        session["fase_numero"] = first_index
    elif first_index != 0:
        session["fase_numero"] = first_index
        session["fase_actual"] = FLOWS[command]["fases"][first_index]["nombre"]
    return session


def current_phase(session: dict[str, Any]) -> dict[str, Any]:
    """Return the current phase or raise for invalid session state."""
    command = session.get("comando")
    if command not in FLOWS:
        raise ValueError(f"Unknown flow: {command}")
    if session.get("fase_actual") == "completado":
        raise ValueError("Session is complete")
    index = session.get("fase_numero")
    if not isinstance(index, int):
        raise ValueError("fase_numero must be an int")
    phases = FLOWS[command]["fases"]
    if index < 0 or index >= len(phases):
        raise ValueError(f"Phase index out of range: {index}")
    phase = phases[index]
    if phase["nombre"] != session.get("fase_actual"):
        raise ValueError("fase_actual and fase_numero are inconsistent")
    return phase


def check_gate(
    session: dict[str, Any],
    *,
    resultado: str = "",
    security_ok: bool = True,
    tests_ok: bool = True,
    user_approved: bool | None = None,
) -> dict[str, Any]:
    """Evaluate the gate for the current phase."""
    if session.get("fase_actual") == "completado":
        return {"passed": True, "reason": "Session complete"}

    try:
        phase = current_phase(session)
    except ValueError as exc:
        return {"passed": False, "reason": str(exc)}

    gate_type = phase["gate_tipo"]
    if gate_type not in KNOWN_GATE_TYPES:
        return {"passed": False, "reason": f"Unknown gate type: {gate_type}"}

    favorable = resultado == "aprobado"
    requires_tests = "automatico" in gate_type
    requires_security = "seguridad" in gate_type
    requires_user = gate_type in {GATE_USUARIO, GATE_USUARIO_SEGURIDAD}

    if not favorable:
        return {"passed": False, "reason": "Result is not favorable"}
    if requires_tests and not tests_ok:
        return {"passed": False, "reason": "Tests are not green"}
    if requires_security and not security_ok:
        return {"passed": False, "reason": "Security review is not favorable"}
    if requires_user:
        approved = user_approved if user_approved is not None else favorable
        if not approved:
            return {"passed": False, "reason": "User approval required"}

    return {"passed": True, "reason": ""}


def should_auto_approve_user_gate(session: dict[str, Any]) -> bool:
    """Return whether autopilot may auto-approve the current user gate."""
    if not session.get("autopilot"):
        return False
    try:
        phase = current_phase(session)
    except ValueError:
        return False
    if phase.get("autopilot_force_user_confirmation"):
        return False
    return phase["gate_tipo"] in {GATE_USUARIO, GATE_USUARIO_SEGURIDAD}


def advance_phase(
    session: dict[str, Any],
    *,
    resultado: str = "aprobado",
    artefactos: list[str] | None = None,
    security_ok: bool = True,
    tests_ok: bool = True,
    user_approved: bool | None = None,
) -> dict[str, Any]:
    """Advance a session if its current gate passes."""
    artefactos = list(artefactos or [])
    if session.get("fase_actual") == "completado":
        return session

    if user_approved is None and should_auto_approve_user_gate(session):
        user_approved = True

    gate = check_gate(
        session,
        resultado=resultado,
        security_ok=security_ok,
        tests_ok=tests_ok,
        user_approved=user_approved,
    )
    if not gate["passed"]:
        raise RuntimeError(f"Cannot advance: {gate['reason']}")

    phase = current_phase(session)
    session["fases_completadas"].append(
        {
            "nombre": phase["nombre"],
            "resultado": resultado,
            "artefactos": artefactos,
            "completada_en": _now(),
            "iteraciones": session.get("iteraciones_fase", 0),
        }
    )
    session["artefactos"].extend(artefactos)
    next_index = _advance_skipping_phases(session, session["fase_numero"] + 1)
    phases = FLOWS[session["comando"]]["fases"]
    if next_index < len(phases):
        session["fase_numero"] = next_index
        session["fase_actual"] = phases[next_index]["nombre"]
    else:
        session["fase_numero"] = next_index
        session["fase_actual"] = "completado"
    session["iteraciones_fase"] = 0
    session["actualizado_en"] = _now()
    return session


def should_retry_phase(
    session: dict[str, Any],
    *,
    resultado: str = "",
    security_ok: bool = True,
    tests_ok: bool = True,
    user_approved: bool | None = None,
) -> dict[str, Any]:
    """Decide whether to advance, retry, or escalate a failed phase."""
    gate = check_gate(
        session,
        resultado=resultado,
        security_ok=security_ok,
        tests_ok=tests_ok,
        user_approved=user_approved,
    )
    iteration = int(session.get("iteraciones_fase", 0))
    max_iterations = int(session.get("max_iteraciones_fase", MAX_PHASE_ITERATIONS))
    if gate["passed"]:
        return {
            "action": "advance",
            "reason": "Gate passed",
            "iteration": iteration,
            "max_iterations": max_iterations,
        }
    if iteration < max_iterations:
        session["iteraciones_fase"] = iteration + 1
        return {
            "action": "retry",
            "reason": gate["reason"],
            "iteration": iteration + 1,
            "max_iterations": max_iterations,
        }
    return {
        "action": "escalate",
        "reason": gate["reason"],
        "iteration": iteration,
        "max_iterations": max_iterations,
    }


def get_effective_optional_agents(
    phase_name: str,
    active_optionals: dict[str, bool] | None = None,
) -> dict[str, list[str]]:
    """Return active optional agents for a phase grouped by execution mode."""
    result = {"paralelo": [], "secuencial": []}
    if not active_optionals:
        return result
    for agent, integration in OPTIONAL_INTEGRATIONS.items():
        if not active_optionals.get(agent):
            continue
        if phase_name not in integration.get("fases", []):
            continue
        position = integration.get("posicion")
        if position in result:
            result[position].append(agent)
    return result


def save_state(session: dict[str, Any], project_dir: str | os.PathLike[str] | None = None) -> Path:
    """Persist a session to `.codex/alfred/state.json` atomically."""
    ensure_state_root(project_dir)
    target = state_path(project_dir)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(session, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


def load_state(project_dir: str | os.PathLike[str] | None = None) -> dict[str, Any] | None:
    """Load and minimally validate a persisted session."""
    target = state_path(project_dir)
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if not {"comando", "fase_actual", "fase_numero"}.issubset(data):
        return None
    if data["comando"] not in FLOWS:
        return None
    return data
