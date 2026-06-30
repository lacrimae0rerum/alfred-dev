from __future__ import annotations

import unittest

from alfred_core.flows import (
    FLOWS,
    GATE_AUTOMATICO,
    GATE_AUTOMATICO_SEGURIDAD,
    GATE_LIBRE,
    GATE_USUARIO,
    GATE_USUARIO_SEGURIDAD,
    advance_phase,
    check_gate,
    create_session,
    should_auto_approve_user_gate,
    should_retry_phase,
)


class FlowDefinitionTest(unittest.TestCase):
    def test_mvp_flows_are_defined(self) -> None:
        self.assertEqual(set(FLOWS), {"feature", "quick", "fix", "spike", "audit", "ship"})
        allowed_gates = {
            GATE_LIBRE,
            GATE_USUARIO,
            GATE_AUTOMATICO,
            GATE_USUARIO_SEGURIDAD,
            GATE_AUTOMATICO_SEGURIDAD,
        }
        for flow in FLOWS.values():
            self.assertGreaterEqual(len(flow["fases"]), 1)
            for phase in flow["fases"]:
                self.assertIn(phase["gate_tipo"], allowed_gates)
                self.assertIsInstance(phase["agentes"], list)
                self.assertIn("descripcion", phase)

    def test_quick_flow_advances_through_two_phases(self) -> None:
        session = create_session("quick", "bounded change")
        self.assertEqual(session["fase_actual"], "ejecucion_acotada")
        advance_phase(session, resultado="aprobado", tests_ok=True, artefactos=["test-local"])
        self.assertEqual(session["fase_actual"], "validacion_rapida")
        advance_phase(session, resultado="aprobado", tests_ok=True, security_ok=True)
        self.assertEqual(session["fase_actual"], "completado")

    def test_gate_blocks_failed_tests(self) -> None:
        session = create_session("quick", "bounded change")
        result = check_gate(session, resultado="aprobado", tests_ok=False)
        self.assertFalse(result["passed"])
        self.assertIn("Tests", result["reason"])

    def test_user_approval_does_not_override_rejected_result(self) -> None:
        session = create_session("feature", "bad product phase")
        result = check_gate(session, resultado="rechazado", user_approved=True)
        self.assertFalse(result["passed"])
        self.assertIn("Result", result["reason"])

    def test_retry_then_escalate(self) -> None:
        session = create_session("quick", "bounded change")
        session["max_iteraciones_fase"] = 1
        first = should_retry_phase(session, resultado="rechazado", tests_ok=False)
        second = should_retry_phase(session, resultado="rechazado", tests_ok=False)
        self.assertEqual(first["action"], "retry")
        self.assertEqual(second["action"], "escalate")

    def test_autopilot_auto_approves_user_gate_but_not_deploy(self) -> None:
        feature = create_session("feature", "new thing", autopilot=True)
        self.assertTrue(should_auto_approve_user_gate(feature))
        advance_phase(feature, resultado="aprobado")
        self.assertIn(feature["fase_actual"], {"estilo_visual", "arquitectura"})

        ship = create_session("ship", "release", autopilot=True)
        advance_phase(ship, resultado="aprobado", tests_ok=True, security_ok=True)
        advance_phase(ship, resultado="aprobado")
        advance_phase(ship, resultado="aprobado", tests_ok=True, security_ok=True)
        self.assertEqual(ship["fase_actual"], "despliegue")
        self.assertFalse(should_auto_approve_user_gate(ship))
        with self.assertRaises(RuntimeError):
            advance_phase(ship, resultado="rechazado", security_ok=True)

    def test_feature_skips_visual_phase_when_no_frontend(self) -> None:
        session = create_session("feature", "backend feature", context={"has_frontend": False}, autopilot=True)
        advance_phase(session, resultado="aprobado")
        self.assertEqual(session["fase_actual"], "arquitectura")
        skipped = [phase for phase in session["fases_completadas"] if phase["resultado"] == "saltada"]
        self.assertEqual(skipped[0]["nombre"], "estilo_visual")


if __name__ == "__main__":
    unittest.main()
