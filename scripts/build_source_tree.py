import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def save(rel_path, content):
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    print(f'Created {rel_path} ({len(content)} bytes)')
