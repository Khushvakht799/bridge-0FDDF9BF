import sys
import json
import re

def text_to_jvgr(text):
    lines = text.split('\n')
    nodes = []
    vectors = []
    
    # Простой парсер: ищем "узел:", "связь:"
    for line in lines:
        line = line.lower().strip()
        if 'узел:' in line or 'node:' in line:
            # Парсим узел
            match = re.search(r'[узелnode]:\s*(\w+)', line)
            if match:
                nodes.append({"id": match.group(1)})
        
        if 'связь:' in line or 'vector:' in line or '->' in line:
            # Парсим связь
            match = re.search(r'(\w+)\s*[->,]\s*(\w+)', line)
            if match:
                vectors.append({
                    "from": match.group(1),
                    "to": match.group(2),
                    "strength": 1.0,
                    "prob": 1.0
                })
    
    return {"nodes": nodes, "vectors": vectors}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python text_to_jvgr.py input.txt output.json")
        sys.exit(1)
    
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()
    
    graph = text_to_jvgr(text)
    
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JVGr сохранен в {sys.argv[2]}")
