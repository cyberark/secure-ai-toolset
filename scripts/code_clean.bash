#!/bin/bash
MAX_LINE_WIDTH=150

# Define list of files to scan
python_files=$(find secure_ai_toolset tests scripts examples -name "*.py" -not -path "*/.venv/*" | tr '\n' ' ')

echo $python_files

# Run yapf to format Python code
yapf -ir $python_files

# Remove unused imports and variables
autoflake --in-place --remove-all-unused-imports --remove-unused-variables  $python_files

# Run isort to sort imports in Python code
isort -l $MAX_LINE_WIDTH -ir $python_files

# run pylint 
pylint $python_files --max-line-length=$MAX_LINE_WIDTH