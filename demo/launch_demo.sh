#!/bin/bash

echo "python3 -m unittest -v test"
PYTHONPATH="$PWD/../" python3 -m unittest test -v
