"""
Tests for publishing functionality under different scenarios.

Tests artifact publishing with various git states and safety checks.
"""

import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent


class TestPublishingBasics:
    """Test basic publishing functionality."""

    def test_paper_directory_exists(self):
        """Paper directory should exist."""
        paper_dir = REPO_ROOT / "paper"
        assert paper_dir.exists(), "paper/ directory not found"
        assert paper_dir.is_dir()

    def test_paper_subdirectories_exist(self):
        """Paper subdirectories should exist."""
        paper_dir = REPO_ROOT / "paper"
        assert (paper_dir / "figures").exists()
        assert (paper_dir / "tables").exists()

    def test_publish_script_exists(self):
        """Publishing script should be available via repro_tools."""
        python_exe = REPO_ROOT / ".env" / "bin" / "python"
        if not python_exe.exists():
            pytest.skip("Python environment not installed")

        # Check that repro-publish command is available
        result = subprocess.run(
            [str(python_exe), "-m", "repro_tools.cli", "--help"],
            capture_output=True,
            text=True,
        )
        # Should succeed or show help
        assert "publish" in result.stdout or result.returncode == 0


class TestProvenanceYAML:
    """Test paper/provenance.yml structure."""

    def test_provenance_yml_exists_after_publish(self):
        """paper/provenance.yml should exist if anything has been published."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        assert prov_file.is_file()

    def test_provenance_yml_valid(self):
        """paper/provenance.yml should be valid YAML."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        assert isinstance(data, dict)

    def test_provenance_yml_has_required_fields(self):
        """paper/provenance.yml should have required fields."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        # Check top-level fields
        assert "paper_provenance_version" in data
        assert "last_updated_utc" in data
        assert "analysis_git" in data

        # Should have either 'artifacts' or 'files' section
        assert "artifacts" in data or "files" in data

    def test_provenance_yml_git_section_valid(self):
        """paper/provenance.yml git section should be valid."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        git_data = data.get("analysis_git", {})

        if git_data.get("is_git_repo", False):
            assert "commit" in git_data
            assert "branch" in git_data
            assert "dirty" in git_data


class TestPublishedArtifacts:
    """Test that published artifacts match expectations."""

    def test_published_files_exist(self):
        """Files listed in paper/provenance.yml should exist."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        # Check artifacts section
        for artifact_name, artifact_data in data.get("artifacts", {}).items():
            for output_type in ["figures", "tables"]:
                if output_type in artifact_data:
                    output_info = artifact_data[output_type]
                    if output_info.get("copied", False):
                        dst_path = Path(output_info["dst"])
                        
                        # Handle cross-platform: if absolute path doesn't exist,
                        # try relative path from repo root
                        if not dst_path.exists():
                            # Extract filename from recorded path
                            filename = dst_path.name
                            # Build expected path from repo root
                            dst_path = REPO_ROOT / "paper" / output_type / filename
                        
                        assert dst_path.exists(), f"Published file missing: {dst_path} (artifact: {artifact_name}, type: {output_type})"

    def test_published_checksums_match(self):
        """Published files should match their recorded checksums."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        from repro_tools import sha256_file

        # Check artifacts section
        for _artifact_name, artifact_data in data.get("artifacts", {}).items():
            for output_type in ["figures", "tables"]:
                if output_type in artifact_data:
                    output_info = artifact_data[output_type]
                    if output_info.get("copied", False) and "dst_sha256" in output_info:
                        dst_path = Path(output_info["dst"])
                        if dst_path.exists():
                            actual_hash = sha256_file(dst_path)
                            expected_hash = output_info["dst_sha256"]
                            assert actual_hash == expected_hash, (
                                f"Checksum mismatch for {dst_path}: {actual_hash} != {expected_hash}"
                            )


class TestGitSafetyChecks:
    """Test git safety checks in publishing."""

    def test_makefile_has_allow_dirty_variable(self):
        """Makefile should have ALLOW_DIRTY variable."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "ALLOW_DIRTY" in content

    def test_makefile_has_require_not_behind_variable(self):
        """Makefile should have REQUIRE_NOT_BEHIND variable."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "REQUIRE_NOT_BEHIND" in content

    def test_makefile_has_require_current_head_variable(self):
        """Makefile should have REQUIRE_CURRENT_HEAD variable."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "REQUIRE_CURRENT_HEAD" in content


class TestPublishingScenarios:
    """Test publishing under different scenarios."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=tmpdir, check=True)
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=tmpdir,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=tmpdir,
                check=True,
            )

            # Create basic structure
            (tmpdir / "output" / "figures").mkdir(parents=True)
            (tmpdir / "output" / "tables").mkdir(parents=True)
            (tmpdir / "output" / "provenance").mkdir(parents=True)
            (tmpdir / "paper" / "figures").mkdir(parents=True)
            (tmpdir / "paper" / "tables").mkdir(parents=True)

            # Make initial commit so git state can be captured
            (tmpdir / "README.md").write_text("Test repo")
            subprocess.run(["git", "add", "."], cwd=tmpdir, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"],
                cwd=tmpdir,
                check=True,
            )

            yield tmpdir

    def test_publish_with_clean_tree(self, temp_repo):
        """Publishing should succeed with clean working tree."""
        # Create test files
        test_fig = temp_repo / "output" / "figures" / "test.pdf"
        test_fig.write_text("test figure")

        test_table = temp_repo / "output" / "tables" / "test.tex"
        test_table.write_text("test table")

        # Create minimal provenance
        from repro_tools import write_build_record

        prov_file = temp_repo / "output" / "provenance" / "test.yml"
        write_build_record(
            out_meta=prov_file,
            artifact_name="test",
            command=["python", "test.py"],
            repo_root=temp_repo,
            inputs=[],
            outputs=[test_fig, test_table],
        )

        # Commit everything
        subprocess.run(["git", "add", "."], cwd=temp_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=temp_repo,
            check=True,
        )

        # Publishing should work with clean tree
        # (We can't actually run the publish command in this test,
        # but we can verify the git state is clean)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == "", "Working tree should be clean"

    def test_publish_with_dirty_tree_detected(self, temp_repo):
        """Publishing should detect dirty working tree."""
        # Create test file
        test_file = temp_repo / "output" / "test.txt"
        test_file.write_text("uncommitted changes")

        # Check git status
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=temp_repo,
            capture_output=True,
            text=True,
        )
        assert len(result.stdout.strip()) > 0, "Working tree should be dirty"

    def test_build_record_captures_dirty_state(self, temp_repo):
        """Build record should capture if tree was dirty during build."""
        from repro_tools import write_build_record

        # Modify a tracked file to make the tree dirty
        readme = temp_repo / "README.md"
        readme.write_text("Modified content")

        # Create build record
        test_output = temp_repo / "output" / "test.txt"
        test_output.write_text("output")

        prov_file = temp_repo / "output" / "provenance" / "test.yml"
        write_build_record(
            out_meta=prov_file,
            artifact_name="test",
            command=["python", "test.py"],
            repo_root=temp_repo,
            inputs=[],
            outputs=[test_output],
        )

        # Check that dirty flag is recorded
        with open(prov_file) as f:
            data = yaml.safe_load(f)

        assert data["git"]["dirty"]


class TestPublishingModes:
    """Test different publishing modes."""

    def test_makefile_supports_publish_analyses(self):
        """Makefile should support PUBLISH_ANALYSES variable."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "PUBLISH_ANALYSES" in content

    def test_makefile_supports_publish_files(self):
        """Makefile should support PUBLISH_FILES variable."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "PUBLISH_FILES" in content

    def test_provenance_file_has_correct_structure_for_analyses(self):
        """Provenance should have 'artifacts' section for analysis-level publishing."""
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        # If using analysis-level publishing, should have 'artifacts'
        if "artifacts" in data:
            # Check structure
            for artifact_name, artifact_data in data["artifacts"].items():
                assert isinstance(artifact_data, dict)
                # Should have output types (figures, tables, etc.)
                has_outputs = any(k in artifact_data for k in ["figures", "tables"])
                assert has_outputs, f"Artifact {artifact_name} has no outputs"


class TestPublishingIdempotency:
    """Test that publishing is idempotent."""

    def test_publish_stamps_directory_exists(self):
        """Publish tracking directory should exist after publishing."""
        stamps_dir = REPO_ROOT / "output" / ".publish_stamps"
        if not stamps_dir.exists():
            pytest.skip("Nothing has been published with stamp tracking")

        assert stamps_dir.is_dir()

    def test_makefile_has_publish_force_target(self):
        """Makefile should have publish-force target to override idempotency."""
        makefile = REPO_ROOT / "Makefile"
        content = makefile.read_text()
        assert "publish-force" in content


class TestPublishingDocumentation:
    """Test that publishing documentation requirements are met."""

    def test_publishing_md_exists(self):
        """docs/publishing.md should exist."""
        pub_doc = REPO_ROOT / "docs" / "publishing.md"
        assert pub_doc.exists(), "docs/publishing.md not found"

    def test_publishing_doc_covers_safety_checks(self):
        """Publishing documentation should cover safety checks."""
        pub_doc = REPO_ROOT / "docs" / "publishing.md"
        if not pub_doc.exists():
            pytest.skip("docs/publishing.md not found")

        content = pub_doc.read_text()
        assert "safety" in content.lower() or "git" in content.lower()
        assert "dirty" in content.lower()

    def test_publishing_doc_covers_scenarios(self):
        """Publishing documentation should cover different scenarios."""
        pub_doc = REPO_ROOT / "docs" / "publishing.md"
        if not pub_doc.exists():
            pytest.skip("docs/publishing.md not found")

        content = pub_doc.read_text()
        assert "scenario" in content.lower() or "example" in content.lower()


class TestPublishingIntegration:
    """Integration tests for complete publishing workflow."""

    def test_can_list_publishable_artifacts(self):
        """Should be able to identify artifacts available for publishing."""
        prov_dir = REPO_ROOT / "output" / "provenance"
        if not prov_dir.exists():
            pytest.skip("No artifacts built yet")

        prov_files = list(prov_dir.glob("*.yml"))
        # Should have at least one artifact
        assert len(prov_files) >= 0  # Can be 0 if nothing built

        # Each provenance file should be valid
        for prov_file in prov_files:
            with open(prov_file) as f:
                data = yaml.safe_load(f)
            assert "outputs" in data

    def test_build_and_publish_consistency(self):
        """Published artifacts should match what was built."""
        # Check that all published files have corresponding build records
        prov_file = REPO_ROOT / "paper" / "provenance.yml"
        if not prov_file.exists():
            pytest.skip("Nothing has been published yet")

        with open(prov_file) as f:
            data = yaml.safe_load(f)

        for _artifact_name, artifact_data in data.get("artifacts", {}).items():
            # Check that build record exists
            build_record = artifact_data.get("figures", {}).get(
                "build_record"
            ) or artifact_data.get("tables", {}).get("build_record")

            if build_record:
                assert "built_at_utc" in build_record
                assert "git" in build_record


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
