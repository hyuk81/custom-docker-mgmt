#!/bin/bash

echo "🔧 Git Configuration Setup"

# Set Git configuration
git config --global user.name "hyuk81"
git config --global user.email "hyuk@parktec.com"

echo "✅ Git configuration set"
echo "Current Git config:"
echo "  User: $(git config --global user.name)"
echo "  Email: $(git config --global user.email)" 