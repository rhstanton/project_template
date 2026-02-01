# Contributing to Reproducible Research Template

Thank you for your interest in contributing to this project! This template aims to make reproducible research easier for economists, social scientists, and other researchers.

## Ways to Contribute

### 🐛 Reporting Bugs

Found a bug? Please [open an issue](https://github.com/rhstanton/project_template/issues/new?template=bug_report.md) with:

- Clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Your environment (OS, Python/Julia versions, etc.)
- Relevant error messages or logs

### 💡 Suggesting Enhancements

Have an idea for improvement? [Open a feature request](https://github.com/rhstanton/project_template/issues/new?template=feature_request.md) with:

- Clear description of the proposed feature
- Use case: Why would this be useful?
- Example workflow or implementation ideas

### 📝 Improving Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples or use cases
- Improve troubleshooting guides
- Translate documentation

### 🔧 Contributing Code

#### Before You Start

1. **Check existing issues** - Someone might already be working on it
2. **Discuss major changes** - Open an issue first for significant features
3. **Read the docs** - Familiarize yourself with the project structure

#### Development Workflow

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/project_template.git
   cd project_template
   ```

2. **Set up development environment**
   ```bash
   make environment
   make verify
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

4. **Make your changes**
   - Follow existing code style (ruff, black formatting)
   - Add tests for new functionality
   - Update documentation as needed

5. **Test your changes**
   ```bash
   make check     # Run linter, formatter, type-check, tests
   make test      # Run test suite
   make all       # Build all artifacts to ensure it works
   ```

6. **Commit your changes**
   ```bash
   git add .
   git commit -m "Brief description of your change
   
   - Detailed point 1
   - Detailed point 2
   - Fixes #123 (if applicable)"
   ```

7. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a PR on GitHub with a clear description.

#### Code Style

- **Python**: Follow PEP 8, use `ruff` for linting, `black` for formatting
- **Documentation**: Use Markdown, keep lines under 100 characters
- **Commit messages**: Use clear, descriptive messages (see existing commits)
- **Tests**: Add tests for new features; aim for comprehensive coverage

#### Testing Requirements

All contributions should include tests where applicable:

- **New features**: Add tests in `tests/test_*.py`
- **Bug fixes**: Add regression test to prevent recurrence
- **Documentation**: Verify examples actually work
- **All tests must pass**: `make test` should show all green

#### Pull Request Guidelines

- **One feature per PR** - Keep changes focused
- **Update CHANGELOG.md** - Add entry under [Unreleased]
- **Pass all checks** - Tests, linting, formatting must pass
- **Update docs** - If you change behavior, update documentation
- **Be responsive** - Address review feedback promptly

## Development Setup Details

### Environment

This project uses:
- **Python 3.11** (conda environment in `.env/`)
- **Julia 1.10+** (auto-installed via juliacall)
- **GNU Make 4.3+** (for build orchestration)
- **pytest** (for testing)
- **ruff, black, mypy** (for code quality)

### Project Structure

```
project_template/
├── run_analysis.py         # Main analysis scripts
├── data/                   # Input data
├── output/                 # Build outputs (ephemeral)
├── paper/                  # Published outputs (permanent)
├── env/                    # Environment specifications
├── shared/                 # Configuration and utilities
├── tests/                  # Test suite
├── docs/                   # Documentation
└── lib/repro-tools/        # Git submodule for utilities
```

See [docs/directory_structure.md](docs/directory_structure.md) for details.

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest tests/test_notebook_integration.py -v

# With coverage
make test-cov

# Quick quality check
make check  # Runs lint, format-check, type-check, test
```

### Code Quality Tools

```bash
make lint          # Check code style (ruff)
make format        # Auto-format code (black + ruff)
make type-check    # Type checking (mypy)
make check         # All of the above + tests
```

## Community Guidelines

### Be Respectful

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community

### Be Collaborative

- Help others learn and grow
- Share knowledge generously
- Credit others' work appropriately
- Assume good intentions

### Be Patient

- Remember contributors are volunteers
- Response times may vary
- Complex changes take time to review

## Questions?

- **Documentation**: Check [docs/](docs/) directory
- **Troubleshooting**: See [docs/troubleshooting.md](docs/troubleshooting.md)
- **General questions**: Open a [GitHub Discussion](https://github.com/rhstanton/project_template/discussions)
- **Bugs/Features**: Open an [Issue](https://github.com/rhstanton/project_template/issues)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make reproducible research more accessible!** 🎉
