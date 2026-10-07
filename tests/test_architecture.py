import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "lagscope"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_core_package_never_imports_streamlit():
    for path in PACKAGE.glob("*.py"):
        assert "streamlit" not in imported_modules(path), path.name


def test_repository_holds_no_raw_corpus():
    data = PACKAGE.parent / "data"
    assert sorted(p.name for p in data.iterdir()) == ["synthetic_274.csv"]
