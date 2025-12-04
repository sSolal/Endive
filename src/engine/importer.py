"""
Import Handler

Handles the `Using` directive for importing .end files.
This is not a Helper because it needs access to both Engine (for recursive processing)
and Pipeline (for creating breakpoints after imports).
"""

from typing import Tuple, List, Set
from pathlib import Path
from ..core import Object, Term


class ImportHandler:
    def __init__(self, engine):
        self.engine = engine
        self.imported: Set[str] = set()  # Completed imports (absolute paths)
        self.importing: List[str] = []   # Stack of currently importing paths
        self.base_path: Path = Path.cwd()  # Base path for imports when not in a file

    def set_base_path(self, path: Path) -> None:
        """Set the base path for resolving imports when not inside another import."""
        self.base_path = path

    def handle(self, filename: str) -> Tuple[bool, List[Object]]:
        """Handle a Using directive by importing the specified file.

        Dots in filename are converted to path separators (e.g., 'foo.bar' -> 'foo/bar.end')
        """
        # Resolve path relative to current importing file (or base_path if in CLI)
        if self.importing:
            base_dir = Path(self.importing[-1]).parent
        else:
            base_dir = self.base_path

        # Convert dots to path separators
        filepath = filename.replace(".", "/") + ".end"
        path = (base_dir / filepath).resolve()
        path_str = str(path)

        # Already imported - skip silently
        if path_str in self.imported:
            return True, [Term("Import", data={"result": f"Already imported: {filename}"})]

        # Circular import detection
        if path_str in self.importing:
            return False, [Term("Error", data={"result": f"Circular import: {filename}"})]

        # Check file exists
        if not path.exists():
            return False, [Term("Error", data={"result": f"File not found: {path}"})]

        # Process import
        self.importing.append(path_str)
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        success, results = self.engine.process(line)
                        if not success:
                            self.importing.pop()
                            return False, results

            # Success - mark imported and create breakpoint
            self.importing.pop()
            self.imported.add(path_str)
            self.engine.breakpoint(f"import:{filename}")
            return True, [Term("Import", data={"result": f"Imported: {filename}"})]
        except Exception as e:
            self.importing.pop()
            return False, [Term("Error", data={"result": f"Import error: {e}"})]
