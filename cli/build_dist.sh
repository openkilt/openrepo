#!/bin/bash

pyinstaller main.py -F -n openrepo
echo "CLI utility available in dist/openrepo"
