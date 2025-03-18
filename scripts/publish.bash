#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# calculate bash dir 
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Increment the version number in pyproject.toml
python $SCRIPT_DIR/increment_version.py

# Build the package as a wheel from the src/security directory with a specific set of dependencies
poetry build --clean 

# Upload the package to the test PyPI repository using credentials from ~/.pypirc
twine upload --verbose --config-file ~/.pypirc --repository pypi dist/*