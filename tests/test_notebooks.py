"""Static notebook checks; CI never executes live cells."""

import ast
import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1] / "notebooks"
REQUIRED = {
    "00_token_factory_quickstart.ipynb",
    "01_benchmark_evidence.ipynb",
    "02_nemotron_diagnosis.ipynb",
    "03_closed_loop_experiment.ipynb",
    "04_offline_replay_and_audit.ipynb",
}


def test_required_notebooks_exist():
    assert {path.name for path in ROOT.glob("*.ipynb")} == REQUIRED


@pytest.mark.parametrize("name", sorted(REQUIRED))
def test_notebook_json_python_safety_and_gates(name):
    path = ROOT / name
    notebook = json.loads(path.read_text(encoding="utf-8"))
    assert notebook["nbformat"] == 4
    assert notebook["metadata"]["language_info"]["name"] == "python"
    assert "widgets" not in notebook["metadata"]
    code = []
    for cell in notebook["cells"]:
        assert cell["cell_type"] in {"code", "markdown"}
        assert isinstance(cell["source"], list)
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        compile(source, str(path), "exec", flags=ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)
        assert cell["execution_count"] is None
        assert cell["outputs"] == []
        assert not any(line.lstrip().startswith(("%", "!")) for line in source.splitlines())
        code.append(source)
    joined = "\n".join(code)
    assert not re.search(r"\bsk-[A-Za-z0-9]{16,}\b", joined)
    assert not re.search(r"NEBIUS_API_KEY\s*=\s*['\"]", joined)
    assert not re.search(r"(?i)bearer\s+[A-Za-z0-9]{12,}", joined)
    if name.startswith(("00", "01", "02", "03")):
        assert 'os.getenv("INFERDOC_RUN_LIVE_TESTS") == "1"' in joined
        assert "bool(settings.api_key)" in joined
    else:
        for provider_path in (
            "NebiusClient", "DoctorAgent", "inferdoc.chat", "inferdoc.benchmark",
            ".achat", "run_closed_loop",
        ):
            assert provider_path not in joined
