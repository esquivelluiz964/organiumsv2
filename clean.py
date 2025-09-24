#!/usr/bin/env python3
"""Remove .pyc files and __pycache__ directories from project tree."""
import os
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.pyc'):
            path = os.path.join(root, f)
            try:
                os.remove(path)
                print('Removed', path)
            except Exception as e:
                print('Error', path, e)
    for d in list(dirs):
        if d == '__pycache__':
            path = os.path.join(root, d)
            try:
                import shutil
                shutil.rmtree(path)
                print('Removed', path)
            except Exception as e:
                print('Error', path, e)
