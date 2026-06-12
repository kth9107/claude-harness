import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HarnessToolsTest(unittest.TestCase):
    def test_harness_audit_validates_graph_and_agents(self):
        audit = load_script("harness_audit.py")

        result = audit.run_audit(ROOT, write_state=False)

        self.assertGreaterEqual(result["summary"]["agent_files"], 10)
        self.assertGreaterEqual(
            result["summary"]["graph_nodes"], result["summary"]["agent_files"]
        )
        self.assertFalse(result["errors"])
        self.assertIn("test-agent", result["post_processing_agents"])

    def test_feedback_records_repeated_items_as_improvement_candidates(self):
        feedback = load_script("harness_feedback.py")
        with tempfile.TemporaryDirectory() as tempdir:
            state_dir = Path(tempdir) / "state"

            feedback.record_feedback(
                ROOT,
                state_dir=state_dir,
                target_type="agent",
                target="test-agent",
                summary="통합 테스트 기준이 모호함",
            )
            result = feedback.record_feedback(
                ROOT,
                state_dir=state_dir,
                target_type="agent",
                target="test-agent",
                summary="테스트 리포트가 반복적으로 모호함",
            )

        self.assertEqual(result["improvement_candidates"][0]["target"], "test-agent")
        self.assertEqual(result["improvement_candidates"][0]["count"], 2)

    def test_report_includes_cleanup_guidance(self):
        report = load_script("harness_report.py")
        with tempfile.TemporaryDirectory() as tempdir:
            state_dir = Path(tempdir) / "state"
            output = report.generate_report(ROOT, state_dir=state_dir, write_report=False)

        self.assertIn("비활성화 완료", output)
        self.assertIn("삭제 후보", output)
        self.assertIn("다시 활성화", output)

    def test_cli_scripts_run_successfully(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state_dir = Path(tempdir) / "state"
            commands = [
                [sys.executable, "scripts/harness_audit.py", "--root", str(ROOT), "--state-dir", str(state_dir)],
                [
                    sys.executable,
                    "scripts/harness_feedback.py",
                    "--root",
                    str(ROOT),
                    "--state-dir",
                    str(state_dir),
                    "--agent",
                    "test-agent",
                    "--summary",
                    "샘플 피드백",
                ],
                [sys.executable, "scripts/harness_report.py", "--root", str(ROOT), "--state-dir", str(state_dir)],
            ]

            for command in commands:
                completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
                self.assertEqual(completed.returncode, 0, completed.stderr)

            audit_json = json.loads((state_dir / "audit-latest.json").read_text())
            self.assertGreaterEqual(audit_json["summary"]["agent_files"], 10)
            self.assertTrue((state_dir / "harness-report.md").exists())


if __name__ == "__main__":
    unittest.main()
