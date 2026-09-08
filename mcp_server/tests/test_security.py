import tempfile
import unittest
from pathlib import Path

from local_ai_mcp.security import WorkspacePolicy, WorkspaceSecurityError


class WorkspacePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.policy = WorkspacePolicy(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resolves_path_inside_workspace(self) -> None:
        path = self.policy.resolve_path("src/example.py")
        self.assertEqual(path, self.root / "src" / "example.py")

    def test_rejects_path_traversal(self) -> None:
        with self.assertRaises(WorkspaceSecurityError):
            self.policy.resolve_path("../outside.txt")

    def test_rejects_absolute_path(self) -> None:
        with self.assertRaises(WorkspaceSecurityError):
            self.policy.resolve_path(str(self.root / "file.txt"))

    def test_rejects_sensitive_names(self) -> None:
        for path in (".env", ".env.local", ".git/config", "src/private.key"):
            with self.subTest(path=path):
                with self.assertRaises(WorkspaceSecurityError):
                    self.policy.resolve_path(path)

    def test_rejects_files_over_limit(self) -> None:
        file_path = self.root / "large.txt"
        file_path.write_text("12345", encoding="utf-8")
        policy = WorkspacePolicy(self.root, max_file_bytes=4)

        resolved = policy.resolve_path("large.txt", must_exist=True, expect_file=True)
        with self.assertRaises(WorkspaceSecurityError):
            policy.validate_file_size(resolved)


if __name__ == "__main__":
    unittest.main()
