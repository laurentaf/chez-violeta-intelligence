#!/usr/bin/env python3
"""Validate generated HTML"""
import os
import re

path = 'F:/projects/chez-violeta-intelligence/artifacts/design/dashboard-comprador/index.html'
size = os.path.getsize(path)
print(f'Size: {size:,} bytes ({size/1024:.1f} KB)')

with open(path, encoding='utf-8') as f:
    content = f.read()

print(f'Length: {len(content):,} chars')
print(f'Has doctype: {"<!DOCTYPE html>" in content}')
print(f'Has /html: {"</html>" in content}')
print(f'Has F array: {"var F=[" in content}')
print(f'Has V array: {"var V=[" in content}')

# Count suppliers
f_count = content.count('{n:')
print(f'Fornecedores (F): {f_count}')

# Count vest types
v_count = content.count('{a:')
print(f'Vestuario tipos (V): {v_count}')

# Find overview values
o_match = re.search(r'var O=\{(.*?)\};', content)
if o_match:
    print(f'Overview: {o_match.group(1)}')

# Check size
assert size < 500 * 1024, f'HTML too large: {size} bytes'
assert '<!DOCTYPE html>' in content
assert '</html>' in content
assert 'var F=[' in content
assert 'var V=[' in content
assert f_count > 0
assert v_count > 0

print('ALL CHECKS PASSED')
