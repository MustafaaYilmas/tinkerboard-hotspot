#!/bin/bash

while true; do
    if ! ping -c 1 8.8.8.8 &>/dev/null; then
        python3 your_python_script.py
    fi
    sleep 60
done
