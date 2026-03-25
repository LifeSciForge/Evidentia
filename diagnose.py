#!/usr/bin/env python3
import re
import sys

# Find app file
app_file = None
for fname in ["streamlit_app.py", "app.py", "app_current.py"]:
    try:
        with open(fname): 
            app_file = fname
            break
    except: pass

if not app_file:
    print("❌ No app file found")
    sys.exit(1)

print("=" * 70)
print("EVIDENTIA DIAGNOSTIC REPORT")
print("=" * 70)
print(f"\nFile: {app_file}\n")

# Read file
with open(app_file, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
    content = ''.join(lines)

# Test 1: Syntax check
print("[TEST 1] Python Syntax Check")
try:
    compile(content, app_file, 'exec')
    print("✅ Syntax valid\n")
except SyntaxError as e:
    print(f"❌ Syntax Error at line {e.lineno}: {e.msg}\n")

# Test 2: F-string issues
print("[TEST 2] F-String Vulnerability Scan")
issues = []
for line_num, line in enumerate(lines, 1):
    if 'f"' in line or "f'" in line:
        if re.search(r'f["\'][^"\']*\{[^}]*(if|else)[^}]*\}', line):
            issues.append((line_num, line.strip()))

if issues:
    print(f"❌ FOUND {len(issues)} CRITICAL ISSUES:\n")
    for line_num, code in issues:
        print(f"  Line {line_num}: {code[:80]}")
else:
    print("✅ No f-string issues\n")

# Test 3: Session state
print("[TEST 3] Session State Initialization")
session_vars = re.findall(r"if '(\w+)' not in st\.session_state:", content)
if session_vars:
    print(f"✅ Found {len(session_vars)} variables initialized:\n")
    for var in session_vars:
        print(f"  • {var}")
else:
    print("⚠️  No session state initialization found\n")

# Test 4: Code stats
print("\n[TEST 4] Code Statistics")
print(f"  Total lines: {len(lines)}")
print(f"  Functions: {len(re.findall(r'^def ', content, re.MULTILINE))}")
print(f"  Classes: {len(re.findall(r'^class ', content, re.MULTILINE))}")

print("\n" + "=" * 70)
if not issues:
    print("✅ DIAGNOSTIC COMPLETE - App is ready")
else:
    print(f"⚠️  FOUND {len(issues)} ISSUES - See fixed version")
print("=" * 70)

