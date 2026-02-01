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
pytest tests/test_integration.py -v
pytest tests/test_environment.py -v
pytest tests/test_publishing.py -v
pytest tests/test_notebook_integration.py -v

# Run specific test class
pytest tests/test_environment.py::TestPythonEnvironment -v
pytest tests/test_publishing.py::TestGitSafetyChecks -v
pytest tests/test_notebook_integration.py::TestJuliaIntegration -v

# Run specific test
pytest tests/test_provenance.py::TestSHA256::test_sha256_file_consistent -v
```

## Test Organization

### `test_provenance.py` - Unit Tests (12 tests)

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

### `test_notebook_integration.py` - Notebook Tests (36 tests)

Comprehensive tests for Jupyter notebook integration:

- **TestNotebookEnvironment** (6 tests): Environment configuration
  - Runnotebook wrapper exists and is executable
  - CDPATH is unset (prevents path pollution bug)
  - PYTHONPATH configured correctly
  - Julia/Python bridge environment variables set
  - Papermill execution configured

- **TestNotebookStructure** (5 tests): Notebook file structure
  - Example notebooks exist (correlation, julia_demo)
  - Proper kernel metadata present
  - Parameters cell tagged correctly
  - Required variables defined in parameters

- **TestNotebookExecution** (4 tests): Execution via papermill
  - Sample notebooks execute successfully
  - Parameters injected correctly
  - Correlation and julia_demo build via make
  - Executed notebooks saved to output/

- **TestNotebookProvenance** (5 tests): Provenance generation
  - Provenance files created for notebook builds
  - Correct structure with all required fields
  - Command records papermill execution
  - Input and output files tracked with SHA256 hashes

- **TestJuliaIntegration** (4 tests): Julia via juliacall
  - juliacall imports successfully
  - Julia Statistics package loads
  - Julia functions callable from Python
  - julia_demo notebook uses juliacall

- **TestNotebookOutputs** (5 tests): Output verification
  - Executed notebooks saved with cell outputs
  - PDF figures created
  - LaTeX tables created
  - Build logs generated

- **TestMakefileIntegration** (5 tests): Makefile integration
  - Notebooks in ANALYSES list
  - Makefile variables defined correctly
  - $(NOTEBOOK) runner used for .ipynb files
  - make correlation/julia_demo succeed

- **TestNotebookErrorHandling** (2 tests): Error handling
  - Notebooks with errors fail build
  - Missing parameters cell detected
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

### `test_environment.py` - Environment Tests

Tests for environment setup and configuration:

- **TestPythonEnvironment**: Python installation
  - Environment directory existence
  - Python version verification (3.11)
  - Required packages (pandas, matplotlib, pyyaml, juliacall)
  - repro_tools installation
  - python.yml validation

- **TestJuliaEnvironment**: Julia setup via juliacall
  - Julia depot existence
  - Julia binary availability
  - Julia version check (1.10+)
  - Project.toml validation
  - Required packages (PythonCall, DataFrames)
  - CondaPkg disabled verification

- **TestEnvironmentWrappers**: Environment wrapper scripts
  - runpython/runjulia/runstata existence and executability
  - PYTHONPATH configuration
  - repro_tools import capability

- **TestSubmodules**: Git submodule setup
  - repro-tools submodule existence
  - Submodule content verification
  - .gitmodules file validation

- **TestEnvironmentUpdate**: Update scenarios
  - Python environment update capability
  - Makefile update targets
  
- **TestEnvironmentIsolation**: Local environment verification
  - Python environment is local to repo
  - Julia depot is local
  - Stata packages are local

- **TestEnvironmentReproducibility**: Version pinning
  - Python version pinning
  - Julia compat section validation

### `test_publishing.py` - Publishing Tests

Tests for publishing functionality and safety:

- **TestPublishingBasics**: Basic setup
  - Paper directory structure
  - Publishing script availability

- **TestProvenanceYAML**: paper/provenance.yml validation
  - File existence and validity
  - Required fields
  - Git section validation

- **TestPublishedArtifacts**: Published file verification
  - Published files exist
  - SHA256 checksums match

- **TestGitSafetyChecks**: Safety variables
  - ALLOW_DIRTY, REQUIRE_NOT_BEHIND, REQUIRE_CURRENT_HEAD

- **TestPublishingScenarios**: Different scenarios
  - Clean working tree
  - Dirty tree detection
  - Build record captures dirty state

- **TestPublishingModes**: Publishing modes
  - PUBLISH_ANALYSES support
  - PUBLISH_FILES support
  - Provenance structure for each mode

- **TestPublishingIdempotency**: Idempotent publishing
  - Publish stamp tracking
  - publish-force target

- **TestPublishingDocumentation**: Documentation
  - docs/publishing.md existence
  - Coverage of safety checks and scenarios

- **TestPublishingIntegration**: End-to-end publishing
  - Artifact identification
  - Build-publish consistency

## Test Requirements

Tests require:
- Python 3.11+
- pytest and pytest-cov (installed via `make environment`)
- tomli (for parsing TOML files)
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
