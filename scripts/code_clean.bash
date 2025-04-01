#!/bin/bash

# Define list of files to scan
python_files=$(find secure_ai_toolset scripts examples -name "*.py" -not -path "*/.venv/*" | tr '\n' ' ')
python_tests=$(find tests -name "*.py" -not -path "*/.venv/*" | tr '\n' ' ')
echo $python_files

# Run yapf to format Python code
yapf -ir $python_files $python_tests

# Remove unused imports and variables
autoflake --remove-all-unused-imports --remove-unused-variables --in-place $python_files $python_tests

# Run isort to sort imports in Python code
isort -l 120 -ir $python_files $python_tests

# Perform a security scan of the code
bandit -r $python_files
