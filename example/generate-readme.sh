#!/bin/bash

example_dir="$(dirname "$0")"
repo_root="${example_dir}/.."
eepyc="${repo_root}/eepyc.py"

# Pass the eepyc source file as an argument to Python,
# then pass it as an argument to itself.
python "${eepyc}" "${eepyc}" "${example_dir}/README.md.eepyc" > "${repo_root}/README.md"
