"""Figure PDFs must be byte-identical when their content is.

WHY THIS EXISTS

This template records the sha256 of every output in `output/provenance/`. For
figures that hash was meaningless until 2026-08-17, because matplotlib stamps the
wall-clock time into every PDF:

    /CreationDate (D:20260817024208)

Two runs producing identical figures produce different bytes if they land in
different seconds, so the recorded hash changed on every build regardless of
content -- the one thing a hash exists not to do. A template that teaches
provenance should not ship a provenance field that means nothing.

`env/env.sh` exports a fixed SOURCE_DATE_EPOCH, which matplotlib honors. The
timestamp moves out of the artifact and into the record, beside the git SHA.

These tests read no data and do not import the analysis.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ENV_SH = REPO / "env" / "env.sh"

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _write_figure(path: Path) -> None:
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    fig.savefig(path)
    plt.close(fig)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_env_sh_exports_a_fixed_source_date_epoch():
    """It must live in env.sh, which runpython and .envrc both source."""
    m = re.search(
        r"^export SOURCE_DATE_EPOCH=(\d+)\s*$", ENV_SH.read_text(), re.MULTILINE
    )
    assert m, "env/env.sh must export a fixed SOURCE_DATE_EPOCH"
    # Digits only: a value computed at runtime would defeat the purpose.
    assert int(m.group(1)) > 0


def test_figures_identical_across_a_second_boundary():
    """THE REGRESSION. Same content, different second, same bytes."""
    assert os.environ.get("SOURCE_DATE_EPOCH"), (
        "SOURCE_DATE_EPOCH not set in this process. Run the suite through "
        "env/scripts/runpython, which sources env/env.sh."
    )
    d = Path(tempfile.mkdtemp())
    a, b = d / "a.pdf", d / "b.pdf"
    _write_figure(a)
    time.sleep(1.2)  # cross a second boundary; that is the whole point
    _write_figure(b)
    assert _sha256(a) == _sha256(b), (
        "identical figures produced different bytes one second apart -- every "
        "figure hash in output/provenance/ is meaningless"
    )


def test_the_check_can_fail_without_the_fix():
    """Guard against passing for the wrong reason.

    If matplotlib ever stopped embedding a timestamp, the test above would pass
    whether or not SOURCE_DATE_EPOCH worked. Confirm the timestamp is still what
    makes the difference: without the variable, two figures a second apart must
    differ.
    """
    d = Path(tempfile.mkdtemp())
    code = (
        "import matplotlib; matplotlib.use('Agg');"
        "import matplotlib.pyplot as plt, hashlib, sys, time;"
        "f=lambda p:(lambda fig,ax:(ax.plot([1,2,3],[1,4,9]),"
        "fig.savefig(p),plt.close(fig)))(*plt.subplots());"
        f"f(r'{d}/x.pdf');time.sleep(1.2);f(r'{d}/y.pdf');"
        "h=lambda p:hashlib.sha256(open(p,'rb').read()).hexdigest();"
        f"sys.stdout.write(h(r'{d}/x.pdf')+' '+h(r'{d}/y.pdf'))"
    )
    env = {k: v for k, v in os.environ.items() if k != "SOURCE_DATE_EPOCH"}
    proc = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, env=env
    )
    assert proc.returncode == 0, proc.stderr
    first, second = proc.stdout.split()
    assert first != second, (
        "without SOURCE_DATE_EPOCH the figures were still identical, so this "
        "proves nothing about the fix -- matplotlib's behavior has changed"
    )
