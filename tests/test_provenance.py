"""
Tests for provenance tracking functionality.
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.provenance import (
    git_state,
    sha256_file,
    now_utc_iso,
    write_build_record,
)


class TestGitState:
    """Test git state detection."""
    
    def test_git_state_returns_dict(self):
        """Git state should return a dictionary."""
        state = git_state()
        assert isinstance(state, dict)
    
    def test_git_state_has_required_keys(self):
        """Git state should have expected keys."""
        state = git_state()
        assert "is_git_repo" in state
        
        if state["is_git_repo"]:
            assert "commit" in state
            assert "branch" in state
            assert "dirty" in state


class TestSHA256:
    """Test SHA256 file hashing."""
    
    def test_sha256_file_returns_string(self):
        """SHA256 should return a hex string."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash_val = sha256_file(Path(temp_path))
            assert isinstance(hash_val, str)
            assert len(hash_val) == 64  # SHA256 is 64 hex chars
            assert all(c in '0123456789abcdef' for c in hash_val)
        finally:
            os.unlink(temp_path)
    
    def test_sha256_file_consistent(self):
        """Same content should produce same hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash1 = sha256_file(Path(temp_path))
            hash2 = sha256_file(Path(temp_path))
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)
    
    def test_sha256_file_different_content(self):
        """Different content should produce different hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("content1")
            temp_path1 = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
            f2.write("content2")
            temp_path2 = f2.name
        
        try:
            hash1 = sha256_file(Path(temp_path1))
            hash2 = sha256_file(Path(temp_path2))
            assert hash1 != hash2
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


class TestTimestamp:
    """Test UTC timestamp generation."""
    
    def test_now_utc_iso_format(self):
        """Timestamp should be ISO 8601 format with UTC timezone."""
        timestamp = now_utc_iso()
        assert isinstance(timestamp, str)
        assert timestamp.endswith('+00:00')
        # Should parse as valid ISO timestamp
        from datetime import datetime
        datetime.fromisoformat(timestamp)


class TestBuildRecord:
    """Test build record generation."""
    
    def test_write_build_record_creates_file(self):
        """Build record should create YAML file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create test input file
            input_file = tmpdir / "input.txt"
            input_file.write_text("test input")
            
            # Create test output file
            output_file = tmpdir / "output.txt"
            output_file.write_text("test output")
            
            # Create metadata file
            metadata_file = tmpdir / "metadata.yml"
            
            # Write build record
            write_build_record(
                metadata_path=metadata_file,
                inputs=[input_file],
                outputs=[output_file],
                script=__file__,
                cmd="test command",
            )
            
            assert metadata_file.exists()
    
    def test_write_build_record_valid_yaml(self):
        """Build record should be valid YAML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            input_file = tmpdir / "input.txt"
            input_file.write_text("test input")
            
            output_file = tmpdir / "output.txt"
            output_file.write_text("test output")
            
            metadata_file = tmpdir / "metadata.yml"
            
            write_build_record(
                metadata_path=metadata_file,
                inputs=[input_file],
                outputs=[output_file],
                script=__file__,
                cmd="test command",
            )
            
            # Should parse as valid YAML
            with open(metadata_file) as f:
                data = yaml.safe_load(f)
            
            assert isinstance(data, dict)
    
    def test_write_build_record_has_required_fields(self):
        """Build record should contain required fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            input_file = tmpdir / "input.txt"
            input_file.write_text("test input")
            
            output_file = tmpdir / "output.txt"
            output_file.write_text("test output")
            
            metadata_file = tmpdir / "metadata.yml"
            
            write_build_record(
                metadata_path=metadata_file,
                inputs=[input_file],
                outputs=[output_file],
                script=__file__,
                cmd="test command",
            )
            
            with open(metadata_file) as f:
                data = yaml.safe_load(f)
            
            # Check required fields
            assert "built_at_utc" in data
            assert "command" in data
            assert "git" in data
            assert "inputs" in data
            assert "outputs" in data
            
            # Check input/output structure
            assert len(data["inputs"]) == 1
            assert "path" in data["inputs"][0]
            assert "sha256" in data["inputs"][0]
            
            assert len(data["outputs"]) == 1
            assert "path" in data["outputs"][0]
            assert "sha256" in data["outputs"][0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
