#!/bin/bash

# This script checks the code formatting using yapf and isort

# Run yapf to format Python code
yapf -ir ./secure_ai_toolset

# Run isort to sort imports in Python code
isort -ir ./secure_ai_toolset
