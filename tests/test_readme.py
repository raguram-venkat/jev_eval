import re
import shlex
from pathlib import Path

import pytest

from jev_eval.cli import build_parser

FENCE = re.compile(r"```\n(.*?)```", re.DOTALL)


def _jev_eval_commands() -> list[str]:
    text = Path("README.md").read_text()
    commands = []
    for block in FENCE.findall(text):
        for line in block.splitlines():
            line = line.split("#", 1)[0].strip()
            if line.startswith("uv run jev-eval"):
                commands.append(line)
    return commands


def test_readme_has_jev_eval_commands():
    assert _jev_eval_commands()  # the cheatsheet must actually contain some


@pytest.mark.parametrize("command", _jev_eval_commands())
def test_readme_command_parses_with_the_real_cli(command, tmp_path, monkeypatch):
    args = shlex.split(command)[2:]  # drop "uv run"
    assert args[0] == "jev-eval"
    args = args[1:]

    # "summarize results/latest" would try to read a real path; point it at an empty tmp dir
    # instead so this stays a pure parse check, no filesystem/network access implied.
    if args and args[0] == "summarize":
        args[1] = str(tmp_path)

    parsed = build_parser().parse_args(args)
    assert parsed.command in ("run", "summarize")


def test_readme_mentions_every_error_behaviour_exit_code():
    text = Path("README.md").read_text()
    table = text.split("## Error behaviour")[1].split("## ")[0]
    # every documented situation must actually list an exit code (2, 1, or the pytest case)
    rows = [line for line in table.splitlines() if line.startswith("|") and "---" not in line and "Situation" not in line]
    assert len(rows) >= 7
    for row in rows:
        assert any(code in row for code in (" 2 ", " 1 ", "pytest failure"))
