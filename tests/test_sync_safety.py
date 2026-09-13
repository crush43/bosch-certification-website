from __future__ import annotations

import shutil
import sys
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = PROJECT_ROOT / "temp_sync" / "unit-tests"
TEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from excel_reader import snapshot_excel  # noqa: E402
from sync_excel import E1_FILE, check_lock_files, resolve_sync_settings  # noqa: E402


@contextmanager
def test_directory():
    root = TEST_TEMP_ROOT / uuid.uuid4().hex
    root.mkdir(parents=False, exist_ok=False)
    try:
        yield root
    finally:
        shutil.rmtree(root, ignore_errors=True)


class SnapshotSafetyTests(unittest.TestCase):
    def test_source_change_during_snapshot_is_rejected(self) -> None:
        with test_directory() as root:
            source = root / "source.xlsx"
            destination = root / "snapshot.xlsx"
            source.write_bytes(b"original workbook bytes")
            real_copy2 = shutil.copy2

            def copy_then_change(source_path: Path, destination_path: Path):
                result = real_copy2(source_path, destination_path)
                with Path(source_path).open("ab") as handle:
                    handle.write(b"changed while snapshotting")
                return result

            with patch("excel_reader.shutil.copy2", side_effect=copy_then_change):
                with self.assertRaisesRegex(RuntimeError, "Source changed while being copied"):
                    snapshot_excel(source, destination)

    def test_excel_lock_file_blocks_sync(self) -> None:
        with test_directory() as root:
            (root / ("~$" + E1_FILE)).touch()
            with self.assertRaisesRegex(RuntimeError, "Excel lock file detected"):
                check_lock_files(root)

    def test_production_mode_rejects_project_test_excel(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Production mode cannot publish from ./excel"):
            resolve_sync_settings(PROJECT_ROOT, PROJECT_ROOT / "excel", True)


if __name__ == "__main__":
    unittest.main()
