# Test Suite

Automated tests for the reproducible research template.

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with coverage report
make test-cov

# Run specific test file
pytest tests/test_provenance.py -v

# Run specific test
pytest tests/test_provenance.py::TestSHA256::test_sha256_file_consistent -v
```

## Test Organization

### `test_provenance.py` - Unit Tests

Tests for core provenance tracking functionality:

- **TestGitState**: Git repository state detection
  - Validates git info dictionary structure
  - Checks for required keys (commit, branch, dirty)

- **TestSHA256**: File hashing functionality
  - Verifies SHA256 hash format and consistency
  - Tests that different content produces different hashes

- **TestTimestamp**: UTC timestamp generation
  - Validates ISO 8601 format
  - Ensures UTC timezone

- **TestBuildRecord**: Build provenance generation
  - Tests YAML file creation
  - Validates provenance structure
  - Checks required fields (built_at_utc, command, git, inputs, outputs)

### `test_integration.py` - Integration Tests

End-to-end workflow tests:

- **TestBuildWorkflow**: Complete build process
  - Environment availability checks
  - Data file existence
  - Module import validation
  - Example script execution

- **TestProvenanceIntegration**: Provenance in real builds
  - Provenance file validation
  - Required field verification
  - Structure validation

- **TestOutputs**: Output file validation
  - Directory structure checks
  - Output file existence
  - Provenance-output consistency

## Test Requirements

Tests require:
- Python 3.11+
- pytest and pytest-cov (installed via `make environment`)
- Working repository with git initialized
- Sample data files in `data/`

## Coverage

Generate coverage reports:

```bash
make test-cov
```

This creates:
- Terminal summary
- HTML report in `htmlcov/index.html`

View HTML coverage:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Writing New Tests

### Test File Naming

- Name: `test_<module>.py`
- Classes: `Test<Feature>`
- Methods: `test_<specific_behavior>`

### Example Test

```python
import pytest
from scripts.provenance import sha256_file
from pathlib import Path

class TestProvenance:
    """Test provenance functionality."""
    
    def test_sha256_returns_string(self):
        """SHA256 should return a hex string."""
        # Create test file
        test_file = Path("test.txt")
        test_file.write_text("test")
        
        try:
            result = sha256_file(test_file)
            assert isinstance(result, str)
            assert len(result) == 64
        finally:
            test_file.unlink()
```

### Using Fixtures

```python
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def temp_file():
    """Provide a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = Path(f.name)
    
    yield temp_path
    
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()

def test_with_fixture(temp_file):
    """Test using fixture."""
    assert temp_file.exists()
```

## Continuous Integration

Tests can be run in CI/CD pipelines:

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup environment
        run: make environment
      - name: Run tests
        run: make test-cov
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors

If tests can't import `scripts` module:

```bash
# Ensure PYTHONPATH includes repo root
export PYTHONPATH=/path/to/repo:$PYTHONPATH
pytest tests/
```

Or use the Python environment wrapper:
```bash
env/scripts/runpython -m pytest tests/
```

### Git Tests Failing

Some tests require a git repository:

```bash
git init
git add .
git commit -m "Initial commit"
make test
```

### Skipped Tests

Some tests skip if conditions aren't met:
- `pytest.skip()` - Expected behavior (e.g., no Julia installed)
- Check test output for skip reasons

### Slow Tests

Speed up test runs:

```bash
# Run in parallel (requires pytest-xdist)
pytest tests/ -n auto

# Run only fast tests
pytest tests/ -m "not slow"
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Cleanup**: Always cleanup temporary files
3. **Assertions**: Use descriptive assertion messages
4. **Coverage**: Aim for >80% code coverage
5. **Speed**: Keep tests fast (<1s each when possible)

## See Also

- [pytest documentation](https://docs.pytest.org/)
- [../docs/troubleshooting.md](../docs/troubleshooting.md) - General troubleshooting
- [../README.md](../README.md) - Project overview
