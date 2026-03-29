#!/bin/bash
# Visualize Git History
git log --graph --oneline --all --decorate --color=always -n "${1:-20}"
