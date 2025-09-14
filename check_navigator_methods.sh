#!/bin/bash

echo "🔍 Checking AutonomousNavigator class methods..."
echo "=" * 50

# Look for method definitions in the autonomous_navigator_with_clicking.py file
echo "📋 Methods in AutonomousNavigator class:"
grep -n "def " autonomous_navigator_with_clicking.py | head -20

echo ""
echo "🔎 Looking for async def methods:"
grep -n "async def " autonomous_navigator_with_clicking.py

echo ""
echo "📄 Class definition line:"
grep -n "class AutonomousNavigator" autonomous_navigator_with_clicking.py