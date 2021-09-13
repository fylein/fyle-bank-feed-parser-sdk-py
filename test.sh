#!/bin/bash

# Delete older .pyc files
find . -name "*.pyc" -exec rm -rf {} \;

# Run tests
python -m pytest -o log_cli=true --log-cli-level=DEBUG -vv --durations=3
