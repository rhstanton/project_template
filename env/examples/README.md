# Examples

Sample scripts demonstrating how to use different components of the project.

## Files

- **`sample_python.py`** - Example Python script
- **`sample_julia.jl`** - Example Julia script
- **`sample_juliacall.py`** - Example Python script using juliacall (Python/Julia interop)
- **`sample_stata.do`** - Example Stata script (if Stata is installed)

## Usage

These are minimal examples for testing and learning. For complete analyses, see the scripts in `analysis/`.

## Running Examples

```bash
# Python example
env/scripts/runpython env/examples/sample_python.py
pure Julia)
env/scripts/runjulia env/examples/sample_julia.jl

# Python/Julia interop example
# Julia example (via juliacall from Python)
env/scripts/runpython env/examples/sample_juliacall.py

# Stata example (if Stata installed)
env/scripts/runstata env/examples/sample_stata.do
```

Or run all at once:

```bash
make examples
```
