import tempfile
import unittest
from pathlib import Path

from local_ai_mcp.security import WorkspacePolicy, WorkspaceSecurityError
from local_ai_mcp.workspace import (
    list_workspace_files,
    read_workspace_file,
    workspace_info,
)


class WorkspaceToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
        (self.root / ".git").mkdir()
        (self.root / ".git" / "config").write_text("secret", encoding="utf-8")
        self.policy = WorkspacePolicy(self.root)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_workspace_info_exposes_active_limits(self) -> None:
        result = workspace_info(self.policy)
        self.assertEqual(result["root"], str(self.root.resolve()))
        self.assertEqual(result["max_file_bytes"], 1_048_576)

    def test_list_files_hides_protected_paths(self) -> None:
        result = list_workspace_files(self.policy)
        paths = {item["path"] for item in result}
        self.assertIn("src", paths)
        self.assertNotIn(".git", paths)

    def test_list_files_recursive_returns_files(self) -> None:
        result = list_workspace_files(self.policy, recursive=True)
        paths = {item["path"] for item in result}
        self.assertIn("src/main.py", paths)

    def test_list_files_rejects_file_as_root(self) -> None:
        with self.assertRaises(WorkspaceSecurityError):
            list_workspace_files(self.policy, path="src/main.py")

    def test_list_files_limits_results(self) -> None:
        result = list_workspace_files(self.policy, recursive=True, max_entries=1)
        self.assertEqual(len(result), 1)

    def test_read_file_returns_text_and_metadata(self) -> None:
        result = read_workspace_file(self.policy, "src/main.py")
        self.assertEqual(result["path"], "src/main.py")
        self.assertEqual(result["content"], "print('ok')")
        self.assertEqual(result["encoding"], "utf-8")

    def test_read_file_rejects_protected_file(self) -> None:
        with self.assertRaises(WorkspaceSecurityError):
            read_workspace_file(self.policy, ".git/config")

    def test_read_file_rejects_binary_content(self) -> None:
        binary_path = self.root / "image.bin"
        binary_path.write_bytes(b"\xff\xfe\x00")
        with self.assertRaises(WorkspaceSecurityError):
            read_workspace_file(self.policy, "image.bin")


if __name__ == "__main__":
    unittest.main()
