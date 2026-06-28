"""Regression tests for the pure flow/gate state machine of the orchestrator.

These cover the host-agnostic behaviour extracted in phase 0: flow catalog,
session creation, gate evaluation and phase advancement. They deliberately
avoid the continuity/kanban/UAT integration paths (those belong to the Claude
Code shell, not to alfred_core), and they exercise the fail-open import of
``continuity`` in ``save_state``.
"""

import os
import tempfile
import unittest

from alfred_core.orchestrator import (
    FLOWS,
    MAX_PHASE_ITERATIONS,
    advance_phase,
    check_gate,
    create_session,
    load_state,
    save_state,
)


class TestFlowCatalog(unittest.TestCase):
    def test_six_flows_present(self):
        self.assertEqual(
            set(FLOWS.keys()),
            {"feature", "fix", "quick", "spike", "ship", "audit"},
        )

    def test_every_flow_has_well_formed_phases(self):
        for name, flow in FLOWS.items():
            self.assertIn("fases", flow, f"{name} sin fases")
            self.assertGreater(len(flow["fases"]), 0, f"{name} con 0 fases")
            for phase in flow["fases"]:
                self.assertIn("nombre", phase)
                self.assertIn("agentes", phase)
                self.assertIn("gate_tipo", phase)
                self.assertIsInstance(phase["agentes"], list)


class TestSessionCreation(unittest.TestCase):
    def test_session_starts_at_first_phase(self):
        session = create_session("spike", "investigar X")
        self.assertEqual(session["comando"], "spike")
        self.assertEqual(session["fase_actual"], "exploracion")
        self.assertEqual(session["fase_numero"], 0)
        self.assertEqual(session["fases_completadas"], [])

    def test_unknown_flow_raises(self):
        with self.assertRaises(ValueError):
            create_session("does-not-exist", "x")


class TestGateEvaluation(unittest.TestCase):
    def test_free_gate_passes_when_approved(self):
        session = create_session("spike", "x")  # fase exploracion: GATE_LIBRE
        result = check_gate(session, resultado="aprobado")
        self.assertTrue(result["passed"], result["reason"])

    def test_gate_blocks_when_not_approved(self):
        session = create_session("spike", "x")
        result = check_gate(session, resultado="rechazado")
        self.assertFalse(result["passed"])

    def test_completed_session_has_no_pending_gate(self):
        session = create_session("spike", "x")
        session["fase_actual"] = "completado"
        result = check_gate(session, resultado="")
        self.assertTrue(result["passed"])

    def test_automatic_gate_requires_passing_tests(self):
        # quick -> primera fase ejecucion_acotada es GATE_AUTOMATICO.
        session = create_session("quick", "x")
        blocked = check_gate(session, resultado="aprobado", tests_ok=False)
        self.assertFalse(blocked["passed"])
        passed = check_gate(session, resultado="aprobado", tests_ok=True)
        self.assertTrue(passed["passed"], passed["reason"])


class TestPhaseAdvancement(unittest.TestCase):
    def test_walk_spike_flow_to_completion(self):
        def completed_names(s):
            return [p["nombre"] if isinstance(p, dict) else p for p in s["fases_completadas"]]

        session = create_session("spike", "x")
        # fase 1: exploracion (libre)
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "conclusiones")
        self.assertIn("exploracion", completed_names(session))
        # fase 2: conclusiones (usuario) -> completado
        session = advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "completado")
        self.assertIn("conclusiones", completed_names(session))

    def test_advance_raises_when_gate_fails(self):
        session = create_session("quick", "x")
        with self.assertRaises(RuntimeError):
            advance_phase(session, resultado="aprobado", tests_ok=False)


class TestStatePersistenceFailOpen(unittest.TestCase):
    def test_save_and_load_roundtrip_under_claude_dir(self):
        # Exercises the canonical ``.claude/`` path, which triggers the
        # fail-open import of ``continuity`` (absent in alfred_core).
        with tempfile.TemporaryDirectory() as tmp:
            claude_dir = os.path.join(tmp, ".claude")
            os.makedirs(claude_dir)
            state_path = os.path.join(claude_dir, "alfred-dev-state.json")
            session = create_session("spike", "x")
            save_state(session, state_path)  # must not raise despite no continuity
            self.assertTrue(os.path.exists(state_path))
            loaded = load_state(state_path)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["comando"], "spike")

    def test_constants_exposed(self):
        self.assertIsInstance(MAX_PHASE_ITERATIONS, int)
        self.assertGreater(MAX_PHASE_ITERATIONS, 0)


if __name__ == "__main__":
    unittest.main()
