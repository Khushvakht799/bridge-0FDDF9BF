import json
import sys

def jvgr_to_md(jvgr_file, md_file):
    with open(jvgr_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    lines = []
    for node in data['nodes']:
        t = node['type']
        c = node['content']
        
        if t == 'markdown_h1':
            lines.append(f"# {c}")
        elif t == 'markdown_h2':
            lines.append(f"## {c}")
        elif t == 'markdown_raw':
            lines.append(c)
        elif t == 'quote':
            lines.append(f"> {c['text']}\n> — {c['author']}\n")
        elif t == 'paragraph':
            lines.append(c + "\n")
        elif t == 'feature':
            lines.append(f"- **{c['name']}:** {c['description']}")
        elif t == 'component':
            lines.append(f"- **{c['path']}** — {c['description']}")
            lines.append(f"  `{c['usage']}`\n")
        elif t == 'list_item':
            indent = '  ' * c.get('level', 0)
            lines.append(f"{indent}- {c['text']}")
        elif t == 'code':
            lines.append(f"```{c['language']}")
            lines.append(c['code'])
            lines.append("```\n")
        elif t == 'principle':
            lines.append(f"- **{c['name']}:** {c['statement']}")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ README.md создан: {md_file}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Использование: python jvgr_to_md.py input.jvgr.json output.md")
        sys.exit(1)
    jvgr_to_md(sys.argv[1], sys.argv[2])