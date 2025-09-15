#!/usr/bin/env python3
"""
Project Audit Script - Identifies current vs archived files
"""

import os
import json
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

def analyze_project_structure():
    """Analyze the project and recommend what to keep vs archive"""
    
    audit_results = {
        'current': [],
        'archive': [],
        'uncertain': [],
        'config': []
    }
    
    # Get current directory
    root_dir = Path('.')
    
    # Define patterns for identification
    current_indicators = [
        'kai_link_click_agent.py',
        'missing_intents.json', 
        'enhanced_',
        'debug_screenshots',
        'strategy_stats.json'
    ]
    
    archive_indicators = [
        'legacy',
        'kai5',
        'old_',
        'backup_',
        'test_',
        'coordinate_finder.py'
    ]
    
    # Analyze all Python files
    for py_file in root_dir.rglob('*.py'):
        if any(indicator in str(py_file).lower() for indicator in current_indicators):
            audit_results['current'].append(str(py_file))
        elif any(indicator in str(py_file).lower() for indicator in archive_indicators):
            audit_results['archive'].append(str(py_file))
        else:
            # Check modification time (less than 7 days = likely current)
            try:
                mod_time = datetime.fromtimestamp(py_file.stat().st_mtime)
                if datetime.now() - mod_time < timedelta(days=7):
                    audit_results['current'].append(str(py_file))
                else:
                    audit_results['uncertain'].append(str(py_file))
            except:
                audit_results['uncertain'].append(str(py_file))
    
    # Analyze JSON config files
    for json_file in root_dir.rglob('*.json'):
        audit_results['config'].append(str(json_file))
    
    return audit_results

def test_python_file_syntax(file_path):
    """Test if a Python file has valid syntax"""
    try:
        with open(file_path, 'r') as f:
            compile(f.read(), file_path, 'exec')
        return True, "Valid syntax"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_imports_availability(file_path):
    """Check if required imports are available"""
    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        if spec is None:
            return False, "Could not create module spec"
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True, "All imports available"
    except ImportError as e:
        return False, f"Missing import: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def main():
    print("🔍 AUTONOMOUS NAVIGATOR PROJECT AUDIT")
    print("=" * 50)
    
    # Analyze structure
    results = analyze_project_structure()
    
    print("\n📁 PROJECT STRUCTURE ANALYSIS:")
    print(f"Current files: {len(results['current'])}")
    print(f"Archive candidates: {len(results['archive'])}")
    print(f"Uncertain: {len(results['uncertain'])}")
    print(f"Config files: {len(results['config'])}")
    
    print("\n✅ CURRENT FILES (Keep these):")
    for file in results['current']:
        print(f"  • {file}")
    
    print("\n📦 ARCHIVE CANDIDATES (Move to archive/):")
    for file in results['archive']:
        print(f"  • {file}")
    
    print("\n❓ UNCERTAIN FILES (Need manual review):")
    for file in results['uncertain']:
        print(f"  • {file}")
    
    print("\n⚙️ CONFIG FILES:")
    for file in results['config']:
        print(f"  • {file}")
    
    # Test key current files
    print("\n🧪 TESTING CURRENT FILES:")
    for file in results['current']:
        if file.endswith('.py'):
            syntax_ok, syntax_msg = test_python_file_syntax(file)
            imports_ok, imports_msg = check_imports_availability(file)
            
            status = "✅" if syntax_ok else "❌"
            print(f"  {status} {file}")
            if not syntax_ok:
                print(f"    Syntax: {syntax_msg}")
            if not imports_ok:
                print(f"    Imports: {imports_msg}")
    
    # Recommended folder structure
    print("\n📂 RECOMMENDED CLEANUP:")
    print("""
    autonomous_navigator/
    ├── README.md
    ├── config/
    │   ├── missing_intents.json     # Your sophisticated intents
    │   └── strategy_stats.json      # Performance tracking
    ├── agents/
    │   └── kai_link_click_agent.py  # Main production agent
    ├── debug_screenshots/           # Keep for debugging
    ├── logs/                        # Keep for monitoring
    ├── archive/                     # Move old files here
    │   ├── legacy_scripts/
    │   ├── kai5_scripts/
    │   └── experiments/
    └── tests/
        └── test_autonomous_cycle.py # Test the main workflow
    """)
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run this audit to identify current vs old files")
    print("2. Test kai_link_click_agent.py with missing_intents.json")
    print("3. Move legacy files to archive/ folder")
    print("4. Create simple README.md explaining current state")
    print("5. Test the complete autonomous cycle")

if __name__ == "__main__":
    main()
