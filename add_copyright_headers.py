#!/usr/bin/env python3
"""
Script to add copyright headers to all Python source files.
Copyright (c) 2024 VoiceLessQ
Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
"""

import os
import sys
from pathlib import Path

COPYRIGHT_HEADER = '''"""
MCP Multi-Context Memory System
Copyright (c) 2024 VoiceLessQ
https://github.com/VoiceLessQ/multi-context-memory

This file is part of the MCP Multi-Context Memory System.
Licensed under the MIT License. See LICENSE file in the project root.

Project Fingerprint: 7a8f9b3c-mcpmem-voicelessq-2024
Original Author: VoiceLessQ
"""

'''

def has_copyright(content: str) -> bool:
    """Check if file already has a copyright notice."""
    return 'Copyright (c) 2024 VoiceLessQ' in content or 'Copyright (c) 2024' in content[:500]

def add_copyright_to_file(file_path: Path) -> bool:
    """Add copyright header to a Python file if it doesn't have one."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip if already has copyright
        if has_copyright(content):
            return False

        # Handle shebang and encoding declarations
        lines = content.split('\n')
        header_lines = []
        code_start = 0

        # Preserve shebang
        if lines and lines[0].startswith('#!'):
            header_lines.append(lines[0])
            code_start = 1

        # Preserve encoding declaration
        if code_start < len(lines) and 'coding' in lines[code_start]:
            header_lines.append(lines[code_start])
            code_start += 1

        # Build new content
        new_content = '\n'.join(header_lines)
        if header_lines:
            new_content += '\n'
        new_content += COPYRIGHT_HEADER
        new_content += '\n'.join(lines[code_start:])

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}", file=sys.stderr)
        return False

def main():
    """Add copyright headers to all Python files in src/ directory."""
    src_dir = Path(__file__).parent / 'src'

    if not src_dir.exists():
        print(f"Error: {src_dir} does not exist", file=sys.stderr)
        return 1

    # Find all Python files
    py_files = list(src_dir.rglob('*.py'))

    print(f"Found {len(py_files)} Python files")

    updated = 0
    skipped = 0

    for py_file in py_files:
        if add_copyright_to_file(py_file):
            print(f"✓ Added copyright to: {py_file.relative_to(src_dir.parent)}")
            updated += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print(f"Updated: {updated} files")
    print(f"Skipped: {skipped} files (already have copyright)")
    print(f"Total:   {len(py_files)} files")
    print(f"{'='*60}")

    return 0

if __name__ == '__main__':
    sys.exit(main())
