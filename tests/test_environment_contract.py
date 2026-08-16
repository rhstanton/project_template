"""The environment invariants, as runnable checks.

    pytest tests/test_environment_contract.py -v

Each test here pins a property that was once violated in this repository, and
several of them are the only reason the violation was noticed. They are grouped
so a failure names the property rather than the file.

The design rule they share: **assert the outcome, not the mechanism.** The test
this file replaces read a wrapper's source and checked that four variable names
appeared in it. It passed for months while `runnotebook` was missing
JULIA_LOAD_PATH -- because JULIA_LOAD_PATH was not one of the four names it
looked for. A check that inspects the mechanism can only ever verify the part of
the mechanism it was told about.

Tests needing Stata or a built environment skip rather than fail, so this file is
useful on a laptop as well as in CI.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_SH = REPO_ROOT / "env" / "env.sh"
SHARED_ENV_SH = (
    REPO_ROOT / "lib" / "repro-tools" / "src" / "repro_tools" / "lib" / "env.sh"
)


def source_env(extra: dict[str, str] | None = None, root: Path | None = None) -> dict:
    """Source env/env.sh in a clean subshell and return the resulting variables.

    Running it and reading the result is the point: it cannot miss a variable the
    way a source-grep can.
    """
    names = [
        "REPRO_PROJECT_ROOT",
        "REPRO_PYTHON",
        "PYTHON_JULIACALL_HANDLE_SIGNALS",
        "PYTHON_JULIAPKG_PROJECT",
        "PYTHON_JULIAPKG_EXE",
        "JULIA_PROJECT",
        "JULIA_DEPOT_PATH",
        "JULIA_LOAD_PATH",
        "JULIA_CONDAPKG_BACKEND",
        "JULIA_PYTHONCALL_EXE",
        "JULIA_NUM_THREADS",
        "PYTHONPATH",
        "DATA_DIR",
        "PATH",
    ]
    probe = "; ".join(f'echo "{n}=${{{n}:-}}"' for n in names)
    target = (root or REPO_ROOT) / "env" / "env.sh"
    result = subprocess.run(
        ["bash", "-c", f"source '{target}' >/dev/null 2>&1; {probe}"],
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **(extra or {})},
    )
    return dict(
        line.split("=", 1) for line in result.stdout.splitlines() if "=" in line
    )


class TestOneSourceOfTruth:
    """The environment is declared once, and the wrappers only source it."""

    def test_env_sh_exists_and_sources_the_shared_half(self):
        assert ENV_SH.is_file(), f"missing {ENV_SH}"
        assert (
            SHARED_ENV_SH.is_file()
        ), f"missing {SHARED_ENV_SH} -- run: git submodule update --init --recursive"
        assert "repro_tools/lib/env.sh" in ENV_SH.read_text(), (
            "env/env.sh must source the shared toolchain from the submodule, "
            "or environment fixes cannot reach projects generated earlier"
        )

    def test_every_bridge_variable_is_set(self):
        env = source_env()
        required = [
            "REPRO_PROJECT_ROOT",
            "PYTHON_JULIACALL_HANDLE_SIGNALS",
            "PYTHON_JULIAPKG_PROJECT",
            "JULIA_PROJECT",
            "JULIA_DEPOT_PATH",
            "JULIA_LOAD_PATH",
            "JULIA_CONDAPKG_BACKEND",
            "JULIA_NUM_THREADS",
            "PYTHONPATH",
            "DATA_DIR",
        ]
        missing = [k for k in required if not env.get(k)]
        assert not missing, f"env/env.sh left unset: {', '.join(missing)}"

    def test_no_wrapper_declares_its_own_environment(self):
        """The anti-drift invariant.

        Four wrappers once each carried their own copy and disagreed: one omitted
        JULIA_LOAD_PATH, another exported JULIAPKG_PROJECT (a name juliapkg does
        not read) pointing somewhere else again.
        """
        bridge = [
            "PYTHON_JULIACALL_HANDLE_SIGNALS",
            "PYTHON_JULIAPKG_PROJECT",
            "PYTHON_JULIAPKG_EXE",
            "JULIA_PROJECT",
            "JULIA_DEPOT_PATH",
            "JULIA_LOAD_PATH",
            "JULIA_CONDAPKG_BACKEND",
            "JULIA_PYTHONCALL_EXE",
            "JULIA_NUM_THREADS",
        ]
        wrappers = sorted(
            p for p in (REPO_ROOT / "env" / "scripts").glob("run*") if p.is_file()
        )
        assert wrappers, "no run* wrappers found"
        for w in wrappers:
            text = w.read_text()
            assert "env.sh" in text, f"{w.name} does not source env/env.sh"
            for var in bridge:
                assert (
                    f"export {var}=" not in text
                ), f"{w.name} exports {var} itself; it belongs in env/env.sh"

    def test_all_wrappers_agree(self):
        """Every wrapper must yield the same environment, not merely have one."""
        env = source_env()
        assert env["JULIA_PROJECT"].endswith("/env")
        assert env["JULIA_DEPOT_PATH"].endswith("/.julia")
        # JULIA_LOAD_PATH must contain both the project and the juliapkg project;
        # a notebook that resolved packages differently from a script is exactly
        # the bug this encodes.
        assert env["JULIA_PROJECT"] in env["JULIA_LOAD_PATH"]
        assert env["PYTHON_JULIAPKG_PROJECT"] in env["JULIA_LOAD_PATH"]


class TestNoAmbientLeakage:
    """Project-scoped values must not be inherited from the calling shell."""

    def test_data_dir_ignores_the_ambient_environment(self):
        """Written as ${DATA_DIR:-...} this once pointed a run here at another
        repository's licensed data, inherited from that repo's direnv."""
        env = source_env({"DATA_DIR": "/somewhere/else/entirely"})
        assert env["DATA_DIR"] != "/somewhere/else/entirely", (
            "DATA_DIR was inherited from the environment. Reading the wrong "
            "project's data is the worst thing env.sh could cause; the "
            "sanctioned override is env/local.sh, sourced last."
        )
        assert env["DATA_DIR"].startswith(env["REPRO_PROJECT_ROOT"])

    def test_julia_thread_count_is_pinned(self):
        env = source_env({"JULIA_NUM_THREADS": "32"})
        assert env["JULIA_NUM_THREADS"] == "1", (
            "JULIA_NUM_THREADS was inherited. Thread count changes "
            "floating-point reduction order, so results would depend on "
            f"whatever shell launched them (got {env['JULIA_NUM_THREADS']})"
        )

    def test_juliapkg_exe_is_never_inherited(self, tmp_path):
        """The sharpest case: a project with no bundled Julia must UNSET it.

        Leaving an inherited value silently builds a fresh clone against another
        checkout's Julia, and reports success -- GPU check included.
        """
        foreign = "/some/other/repo/.julia/pyjuliapkg/install/bin/julia"
        probe = 'echo "PYTHON_JULIAPKG_EXE=${PYTHON_JULIAPKG_EXE:-}"'
        result = subprocess.run(
            [
                "bash",
                "-c",
                f"REPRO_PROJECT_ROOT='{tmp_path}' source '{SHARED_ENV_SH}' "
                f">/dev/null 2>&1; {probe}",
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHON_JULIAPKG_EXE": foreign},
        )
        value = result.stdout.split("=", 1)[1].strip()
        assert value == "", (
            f"PYTHON_JULIAPKG_EXE kept an inherited value ({value}) for a project "
            "with no bundled Julia. It must be this project's Julia, or nothing."
        )

    def test_juliaup_is_stripped_from_path(self):
        env = source_env({"PATH": f"/opt/juliaup/bin:{os.environ.get('PATH', '')}"})
        assert not any(
            "juliaup" in part.lower() for part in env["PATH"].split(":")
        ), "juliaup survived on PATH; a second Julia is then one lookup away"


class TestCdpathDiscipline:
    """Executed scripts unset CDPATH; sourced files must not."""

    def test_executed_scripts_unset_cdpath(self):
        scripts = sorted((REPO_ROOT / "env" / "scripts").glob("run*"))
        scripts += [
            REPO_ROOT / "scripts" / "check_prerequisites.sh",
            REPO_ROOT / "scripts" / "init-private.sh",
            REPO_ROOT / "scripts" / "make_instance.sh",
        ]
        for s in scripts:
            if not s.is_file() or s.suffix == ".py":
                continue
            text = s.read_text()
            if "cd " not in text:
                continue
            assert "unset CDPATH" in text, (
                f"{s.name} uses cd without unsetting CDPATH. When cd resolves "
                "through CDPATH it echoes the directory, so $(cd ... && pwd) "
                "silently returns two newline-separated paths."
            )

    def test_sourced_files_do_not_unset_cdpath(self):
        """`unset` in a sourced file mutates the caller's interactive shell.

        Comments are stripped first. The first version of this test matched the
        comment in env.sh that *explains why we do not do this* -- a text search
        finding the prose about the rule rather than a violation of it, which is
        the same mistake this file's docstring warns about.
        """
        for f in (ENV_SH, SHARED_ENV_SH):
            code = [
                line
                for line in f.read_text().splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            offenders = [ln for ln in code if re.search(r"\bunset\s+CDPATH\b", ln)]
            assert not offenders, (
                f"{f.name} is sourced, so it must clear CDPATH inside the command "
                f"substitution (CDPATH= cd -- ...), not unset it globally. "
                f"Offending line(s): {offenders}"
            )

    def test_repo_root_resolves_to_one_path_under_cdpath(self):
        """The failure this guards against, reproduced."""
        polluted = f".:{REPO_ROOT.parent}:{Path.home()}"
        env = source_env({"CDPATH": polluted})
        root = env["REPRO_PROJECT_ROOT"]
        assert (
            "\n" not in root and root.count("/home") <= 1
        ), f"REPRO_PROJECT_ROOT contains more than one path under CDPATH: {root!r}"
        assert Path(root).is_dir(), f"REPRO_PROJECT_ROOT is not a directory: {root!r}"


class TestJuliaPinning:
    """Project.toml alone admits any 1.x; the Manifest is the real pin."""

    def test_manifest_is_committed(self):
        manifest = REPO_ROOT / "env" / "Manifest.toml"
        if not manifest.is_file():
            pytest.skip("no Julia in this project")
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "env/Manifest.toml"],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        assert tracked.returncode == 0, (
            "env/Manifest.toml is not tracked. Project.toml admits any "
            "FixedEffectModels 1.x, so without the Manifest nothing is pinned -- "
            "one real project's Julia stack moved 61 packages under such bounds."
        )

    def test_juliapkg_pins_an_exact_julia_version(self):
        path = REPO_ROOT / "env" / "juliapkg.json"
        if not path.is_file():
            pytest.skip("no Julia in this project")
        import json

        spec = json.loads(path.read_text())
        julia = spec.get("julia", "")
        assert julia.startswith("="), (
            f"env/juliapkg.json pins julia as {julia!r}; without an exact '=' pin "
            "juliapkg takes whatever satisfies PythonCall's loose compat bound"
        )

    def test_juliapkg_matches_the_installed_julia(self):
        path = REPO_ROOT / "env" / "juliapkg.json"
        binary = REPO_ROOT / ".julia" / "pyjuliapkg" / "install" / "bin" / "julia"
        if not path.is_file() or not binary.is_file():
            pytest.skip("Julia not installed here")
        import json

        want = json.loads(path.read_text())["julia"].lstrip("=")
        got = subprocess.run(
            [str(binary), "--version"], capture_output=True, text=True
        ).stdout.split()[-1]
        assert got == want, f"juliapkg.json pins {want}, installed Julia is {got}"


class TestStataVendoring:
    """The pin is the committed ado files, never a version passed to SSC."""

    def test_package_list_carries_no_versions(self):
        path = REPO_ROOT / "env" / "stata-packages.txt"
        if not path.is_file():
            pytest.skip("no Stata in this project")
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            assert len(line.split()) == 1, (
                f"stata-packages.txt line {line!r} carries a version. SSC has no "
                "versioned install -- `ssc install estout 3.1.2` is r(101), not a "
                "version request -- so a version here cannot be enforced by "
                "anything. Versions belong in stata-requirements.txt."
            )

    def test_no_makefile_rule_passes_a_version_to_ssc(self):
        """`ssc install pkg 1.2.3` is r(101), not a version request.

        Checks the arguments between `ssc install` and the comma (Stata options
        follow the comma) for anything version-shaped. Comment lines are excluded
        so the prose explaining the rule cannot trip it.
        """
        for line in (REPO_ROOT / "env" / "Makefile").read_text().splitlines():
            stripped = line.strip().lstrip("#").strip()
            if line.lstrip().startswith("#") or "ssc install" not in line:
                continue
            m = re.search(r"ssc install\s+([^,\n]*)", stripped)
            if not m:
                continue
            args = m.group(1).split()
            versionish = [a for a in args[1:] if re.fullmatch(r"[\d.]+", a)]
            assert not versionish, (
                f"env/Makefile passes a version to ssc install: {line.strip()!r}. "
                "SSC has no versioned install; the pin is the committed ado files."
            )

    def test_vendored_packages_are_committed(self):
        plus = REPO_ROOT / ".stata" / "ado" / "plus"
        if not (REPO_ROOT / "env" / "stata-packages.txt").is_file():
            pytest.skip("no Stata in this project")
        assert plus.is_dir(), (
            ".stata/ado/plus is missing. The vendored packages ARE the pin; "
            "run `make stata-env`."
        )
        tracked = subprocess.run(
            ["git", "ls-files", ".stata/ado/plus"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        ).stdout.split()
        assert tracked, (
            ".stata/ado/plus exists but nothing in it is tracked. Check the "
            ".gitignore allowlist rules -- without them the rules install into a "
            "directory git refuses to track and the pin never leaves this machine."
        )

    def test_requirements_record_matches_the_package_list(self):
        req = REPO_ROOT / "env" / "stata-requirements.txt"
        pkgs = REPO_ROOT / "env" / "stata-packages.txt"
        if not req.is_file() or not pkgs.is_file():
            pytest.skip("no Stata pin record yet; run `make stata-requirements`")
        listed = {
            line.split()[0]
            for line in pkgs.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        }
        recorded = {
            line.split()[0]
            for line in req.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        }
        assert listed == recorded, (
            f"stata-packages.txt and stata-requirements.txt disagree: "
            f"only in packages={listed - recorded}, only in requirements={recorded - listed}. "
            "Regenerate with `make stata-requirements`."
        )

    @pytest.mark.slow
    def test_stata_check_actually_fails_on_a_bad_pin(self, tmp_path):
        """A check that cannot fail is worse than no check.

        Falsifies one version and asserts `make stata-check` errors. Skipped
        without Stata, which is most machines.
        """
        if not shutil.which("stata-mp"):
            pytest.skip("stata-mp not on PATH")
        req = REPO_ROOT / "env" / "stata-requirements.txt"
        if not req.is_file():
            pytest.skip("no stata-requirements.txt")

        original = req.read_text()
        falsified = re.sub(
            r"^(\w+) == .*$", r"\1 == 9.99.9", original, count=1, flags=re.M
        )
        assert falsified != original, "could not falsify a requirement line"
        try:
            req.write_text(falsified)
            result = subprocess.run(
                ["make", "stata-check"],
                cwd=REPO_ROOT / "env",
                capture_output=True,
                text=True,
            )
            assert result.returncode != 0, (
                "make stata-check PASSED against a falsified requirement. "
                "Note Stata exits 0 even when a do-file aborts, so the rule must "
                "judge by the log, not by $?."
            )
        finally:
            req.write_text(original)


class TestTemplateOrigin:
    """Provenance for template updates, and the rule that it must not guess."""

    def test_origin_file_is_valid_if_present(self):
        path = REPO_ROOT / "template-origin.toml"
        if not path.is_file():
            pytest.skip("this IS the template; generated projects carry the file")
        with path.open("rb") as f:
            data = tomllib.load(f)
        assert data["template"]["commit"], "template-origin.toml records no commit"
        assert re.fullmatch(
            r"[0-9a-f]{40}", data["template"]["commit"]
        ), "template.commit is not a full git SHA"

    def test_bootstrap_refuses_to_guess_the_commit(self):
        """git searches UPWARDS for a repo, so a tree with no history of its own
        gets an ancestor's HEAD. That once stamped an unrelated repository's
        commit as a project's template origin."""
        src = (REPO_ROOT / "bootstrap.py").read_text()
        assert "_own_git_repo" in src, (
            "bootstrap.py must verify rev-parse --show-toplevel resolves to the "
            "project root before trusting any git answer"
        )
        assert "--template-commit" in src, (
            "bootstrap.py must accept an explicit --template-commit for trees "
            "exported without history"
        )
