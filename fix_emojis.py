import os

replacements = {
    '[WAIT]': '[WAIT]',
    '[OK]': '[OK]',
    '[ERROR]': '[ERROR]',
    '[INFO]': '[INFO]',
    '[WARN]': '[WARN]'
}

for root, dirs, files in os.walk(r'C:\Users\Dell\Desktop\Segmento-app-website-dev\backend'):
    if '.venv' in root or '__pycache__' in root: continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for emoji, text in replacements.items():
                    new_content = new_content.replace(emoji, text)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")
            except Exception as e:
                pass
