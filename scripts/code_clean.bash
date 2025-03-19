#!/bin/bash

# Define list of files to scan
python_files=$(find secure_ai_toolset tests scripts examples -name "*.py" -not -path "*/.venv/*" | tr '\n' ' ')

echo $python_files

# Run yapf to format Python code
yapf -ir $python_files

# Remove unused imports and variables
autoflake --remove-all-unused-imports --remove-unused-variables --in-place $python_files

# Run isort to sort imports in Python code
isort -l 120 -ir $python_files
