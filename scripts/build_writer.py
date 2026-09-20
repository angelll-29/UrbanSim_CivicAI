
import os, json

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write_file(path, content):
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Wrote: {path} ({len(content)} bytes)')
