#!/bin/bash

echo "📁 Checking files in the project directory..."
echo "=" * 50

# List all Python files
echo "🐍 Python files:"
ls -la *.py 2>/dev/null || echo "No .py files found"

echo ""

# List all files
echo "📄 All files:"
ls -la

echo ""

# Check if there's a web_navigator.py file specifically
echo "🔍 Looking for web_navigator related files:"
ls -la | grep -i navigator || echo "No navigator files found"

echo ""

# Check if there are any Python files that might contain the AutonomousWebNavigator class
echo "🔎 Searching for AutonomousWebNavigator class in Python files:"
grep -r "class AutonomousWebNavigator" . 2>/dev/null || echo "AutonomousWebNavigator class not found"