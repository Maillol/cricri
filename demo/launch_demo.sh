#!/bin/bash

echo "python3 -m unittest -v test_statemachine"
PYTHONPATH="$PWD/../" python3 -m unittest -v test_statemachine
