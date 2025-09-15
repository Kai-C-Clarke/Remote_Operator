#!/bin/bash
# Repository Cleanup Script for Remote_Operator
# Run this from your repository root directory

echo "🧹 Cleaning up Remote_Operator repository..."

# Create new directory structure
echo "📁 Creating directory structure..."
mkdir -p config agents tests utils docs archive/{legacy_scripts,kai5_experiments,prototypes}

# Move current production files
echo "✅ Moving current production files..."
[ -f "kai_link_click_agent.py" ] && mv kai_link_click_agent.py agents/
[ -f "missing_intents.json" ] && mv missing_intents.json config/
[ -f "strategy_stats.json" ] && mv strategy_stats.json config/

# Archive old files
echo "📦 Archiving legacy files..."
[ -d "Legacy scripts" ] && mv "Legacy scripts"/* archive/legacy_scripts/ 2>/dev/null
[ -d "Legacy Modular_Remote_operator" ] && mv "Legacy Modular_Remote_operator"/* archive/prototypes/ 2>/dev/null
[ -d "Kai5 scripts" ] && mv "Kai5 scripts"/* archive/kai5_experiments/ 2>/dev/null

# Move uncertain files to archive for review
echo "❓ Moving uncertain files for review..."
[ -f "autonomous_navigator_with_clicking.py" ] && mv autonomous_navigator_with_clicking.py archive/prototypes/
[ -f "enhanced_cookie_handler.py" ] && mv enhanced_cookie_handler.py archive/prototypes/
[ -f "coordinate_finder.py" ] && mv coordinate_finder.py archive/prototypes/

# Move test files
echo "🧪 Organizing test files..."
[ -f "test_navigator.py" ] && mv test_navigator.py tests/
[ -f "check_navigator_methods.sh" ] && mv check_navigator_methods.sh tests/
[ -f "check_files.sh" ] && mv check_files.sh tests/

# Clean up empty directories
echo "🗑️ Removing empty directories..."
find . -type d -empty -delete 2>/dev/null

# Keep important directories even if empty
mkdir -p logs debug_screenshots
touch logs/.gitkeep debug_screenshots/.gitkeep

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv

# Logs and debug files
logs/*.log
debug_screenshots/*.png
debug_screenshots/*.jpg

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
strategy_stats.json.backup
*.temp
EOF
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "📋 Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# Autonomous Web Navigation Requirements
playwright>=1.40.0
Pillow>=9.0.0
pytesseract>=0.3.10
asyncio
pathlib
requests

# Development
pytest>=7.0.0
black
flake8
EOF
fi

echo "✨ Repository cleanup complete!"
echo ""
echo "📁 New structure:"
echo "  config/     - Configuration files (intents, stats)"
echo "  agents/     - Main navigation agents"  
echo "  tests/      - Test scripts"
echo "  archive/    - Historical code"
echo "  logs/       - Runtime logs (gitignored)"
echo "  debug_screenshots/ - Debug images (gitignored)"
echo ""
echo "🎯 Next steps:"
echo "  1. Review files in archive/ folder"
echo "  2. Test: python agents/kai_link_click_agent.py"
echo "  3. Commit and push cleaned structure"
echo "  4. Update README.md"