#!/bin/bash

#############################################################
# Code Cleaning and Security Scanning Script
# 
# This script automates code formatting, optimization, and
# security scanning for Python files in the agent-guard project.
# It performs the following operations:
# - Code formatting with yapf
# - Removing unused imports and variables with autoflake
# - Sorting imports with isort
# - Detecting unused functions with vulture
# - Security scanning with bandit
# - Detecting secrets with gitleaks
# - Linting with pylint
#############################################################

# Define list of files to scan
echo "🔍 Finding Python files to process..."
python_files=$(find agent_guard_core examples servers -name "*.py" -not -path "*/.venv/*" | tr '\n' ' ')
python_tests=$(find tests -name "*.py" -not -path "*/.venv/*" | tr '\n' ' ')
echo "Found these files to process:"
echo $python_files

# Ask for confirmation before proceeding
echo ""
echo "⚠️  This script will modify your files. Continue? (Y/n)"
read -r confirm
confirm=${confirm:-Y}
if [[ $confirm != "y" && $confirm != "Y" ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Run yapf to format Python code
echo ""
echo "📝 Formatting Python code with yapf..."
yapf -ir $python_files $python_tests
echo "✅ Code formatting complete."

# Remove unused imports and variables
echo ""
echo "🧹 Removing unused imports and variables with autoflake..."
autoflake --remove-all-unused-imports --remove-unused-variables --in-place $python_files $python_tests
echo "✅ Unused code removal complete."

# Run isort to sort imports in Python code
echo ""
echo "📊 Sorting imports with isort..."
isort -l 120 -ir --float-to-top $python_files $python_tests
echo "✅ Import sorting complete."

# Remove unused functions using vulture
echo ""
echo "🦅 Detecting unused functions with vulture..."
vulture $python_files
echo "✅ Unused function detection complete. Review the output above."

# Perform a security scan of the code
echo ""
echo "🔒 Running security scan with bandit..."
bandit -r $python_files
echo "✅ Security scan complete. Review the output above."

# Run gitleaks
echo ""
echo "🔐 Scanning for leaked secrets with gitleaks..."
gitleaks -v git --no-banner
echo "✅ Secret scan complete. Review the output above."

# Add pylint
echo ""
echo "🔍 Running pylint for code quality checks..."
pylint $python_files
echo "✅ Pylint check complete. Review the output above."

echo ""
echo "📦 Compiling requirements-dev.txt for development dependencies..."
uv pip compile pyproject.toml -o requirements-dev.txt --extra dev

echo ""
echo "📦 Compiling requirements.txt for all optional dependencies (servers, examples)..."
uv pip compile pyproject.toml -o requirements.txt --extra servers --extra examples

echo ""
echo "🎉 Code cleaning and security scanning complete!"


