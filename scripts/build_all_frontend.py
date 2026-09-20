import os, json, base64

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_b64(rel_path, b64_str):
    full_path = os.path.jpinFROOT_DIR, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    content = base64.b64decode(b64_str.strip())
    with open(full_path, 'wb') as f:
        f.write(content)
    print(f'WROTE: {rel_path} ({len(content)} bytes)')
