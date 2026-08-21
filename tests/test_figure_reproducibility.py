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

WHY THESE RUN IN A SUBPROCESS

The regression test used to assert that SOURCE_DATE_EPOCH was set *in the pytest
process*, which made it a test of how the suite happened to be launched rather
than of anything in the repository. Under `env/scripts/runpython` it passed;
under the bare `pytest` the docs also advertise it failed, because direnv had not
handed the variable down. Inheritance was standing in for configuration -- the
same defect found in `runjulia` on 2026-08-19.

These now read the constant out of `env/env.sh` and apply it themselves, so they
test the configured value and give the same answer however pytest was started.
That the *wrappers* export it is a separate question, and belongs to the tests
that run them with the environment stripped.

These tests read no data and do not import the analysis.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENV_SH = REPO / "env" / "env.sh"

# Writes two figures 1.2 s apart -- crossing a second boundary is the whole
# point -- and prints their two sha256 digests.
_TWO_FIGURES = """
import hashlib, sys, time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def write(path):
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])
    fig.savefig(path)
    plt.close(fig)

def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()

a, b = sys.argv[1], sys.argv[2]
write(a)
time.sleep(1.2)
write(b)
sys.stdout.write(sha(a) + " " + sha(b))
"""


def epoch_from_env_sh() -> str:
    """The literal SOURCE_DATE_EPOCH that env/env.sh exports."""
    m = re.search(
        r"^export SOURCE_DATE_EPOCH=(\d+)\s*$", ENV_SH.read_text(), re.MULTILINE
    )
    assert m, "env/env.sh must export a fixed SOURCE_DATE_EPOCH"
    return m.group(1)


def two_figure_hashes(epoch: str | None) -> tuple[str, str]:
    """Hash two identical figures written a second apart, under a given epoch.

    `epoch=None` means the variable is absent, which is the unfixed behavior.
    """
    env = {k: v for k, v in os.environ.items() if k != "SOURCE_DATE_EPOCH"}
    if epoch is not None:
        env["SOURCE_DATE_EPOCH"] = epoch
    with tempfile.TemporaryDirectory() as d:
        proc = subprocess.run(
            [sys.executable, "-c", _TWO_FIGURES, f"{d}/a.pdf", f"{d}/b.pdf"],
            capture_output=True,
            text=True,
            env=env,
        )
    assert proc.returncode == 0, proc.stderr
    first, second = proc.stdout.split()
    return first, second


def test_env_sh_sets_a_fixed_source_date_epoch():
    """It must live in env.sh, which runpython and .envrc both source."""
    # Digits only: a value computed at runtime would defeat the purpose. The
    # regex already refuses anything else; this states why.
    assert int(epoch_from_env_sh()) > 0


def test_figures_identical_across_a_second_boundary():
    """THE REGRESSION. Same content, different second, same bytes."""
    first, second = two_figure_hashes(epoch_from_env_sh())
    assert first == second, (
        "identical figures produced different bytes one second apart -- the "
        "SOURCE_DATE_EPOCH in env/env.sh is not taking effect, and every figure "
        "hash in output/provenance/ is meaningless"
    )


def test_the_check_can_fail_without_the_fix():
    """Guard against passing for the wrong reason.

    If matplotlib ever stopped embedding a timestamp, the test above would pass
    whether or not SOURCE_DATE_EPOCH worked. Confirm the timestamp is still what
    makes the difference: without the variable, two figures a second apart must
    differ.
    """
    first, second = two_figure_hashes(None)
    assert first != second, (
        "without SOURCE_DATE_EPOCH the two figures were still identical, so the "
        "test above proves nothing about the fix -- matplotlib's behavior has "
        "changed"
    )
