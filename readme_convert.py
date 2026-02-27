import json

# Читаем JSON
with open('readme.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

lines = []

# Обрабатываем все узлы
for node in data['nodes']:
    if node['type'] == 'markdown':
        if 'level' in node['content']:
            lines.append('#' * node['content']['level'] + ' ' + node['content']['text'])
        elif 'raw' in node['content']:
            lines.append(node['content']['raw'])
    
    elif node['type'] == 'quote':
        lines.append(f"> {node['content']['text']}")
        lines.append(f"> — {node['content']['author']}")
    
    elif node['type'] == 'paragraph':
        lines.append(node['content']['text'])
        lines.append('')
    
    elif node['type'] == 'code':
        lines.append('```' + node['content']['language'])
        lines.append(node['content']['code'])
        lines.append('```')
        lines.append('')
    
    elif node['type'] == 'feature':
        lines.append(f"- **{node['content']['name']}:** {node['content']['description']}")
    
    elif node['type'] == 'component':
        lines.append(f"- **{node['content']['path']}** — {node['content']['description']}")
        lines.append(f"  `{node['content']['usage']}`")
        lines.append('')
    
    elif node['type'] == 'list_item':
        indent = '  ' * node['content'].get('level', 0)
        lines.append(f"{indent}- {node['content']['text']}")
    
    elif node['type'] == 'list':
        for item in node['content']['items']:
            lines.append(f"- {item}")
        lines.append('')
    
    elif node['type'] == 'principle_full':
        lines.append(f"- **{node['content']['name']}:** {node['content']['statement']}")

# Записываем README.md
with open('README.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("✅ README.md успешно создан!")
print(f"📄 Размер: {len('\n'.join(lines))} байт")