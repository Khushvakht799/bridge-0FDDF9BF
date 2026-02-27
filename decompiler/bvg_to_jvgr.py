import sys
import struct
import json
import zlib

def bvg_to_jvgr(bvg_file, jvgr_file):
    with open(bvg_file, 'rb') as f:
        # 1. Читаем HEADER
        header = f.read(28)
        magic, version, flags, offset_names, offset_types, offset_data, crc32, reserved = \
            struct.unpack('<4sBBIIII6s', header)
        
        if magic != b'BVG1':
            print("Ошибка: не BVG файл")
            return
        
        # 2. Читаем NAME DICTIONARY
        f.seek(offset_names)
        name_count = struct.unpack('<H', f.read(2))[0]
        names = []
        for _ in range(name_count):
            name_len = struct.unpack('<B', f.read(1))[0]
            name = f.read(name_len).decode('utf-8')
            names.append(name)
        
        # 3. Читаем TYPE DICTIONARY
        f.seek(offset_types)
        type_count = struct.unpack('<H', f.read(2))[0]
        type_dict = []
        
        # ВАЖНО: создаем копию names, потому что type_dict может ссылаться
        # на индексы, которые уже есть в names
        all_names = names.copy()
        
        for _ in range(type_count):
            name_idx = struct.unpack('<H', f.read(2))[0]
            type_id = struct.unpack('<B', f.read(1))[0]
            
            # Проверяем, что индекс в пределах массива
            if name_idx < len(all_names):
                field_name = all_names[name_idx]
            else:
                # Если индекс за пределами, значит это новое имя, которого нет в names
                # Добавляем заглушку
                field_name = f"field_{name_idx}"
                # Расширяем список, если нужно
                while len(all_names) <= name_idx:
                    all_names.append(f"unknown_{len(all_names)}")
                all_names[name_idx] = field_name
            
            type_dict.append((field_name, type_id))
        
        # Обновляем names, включив все имена из type_dict
        names = all_names
        
        # 4. Читаем GRAPH DATA
        f.seek(offset_data)
        graph_data = f.read()
        
        # Проверяем CRC
        crc_calc = zlib.crc32(graph_data) & 0xFFFFFFFF
        if crc_calc != crc32:
            print(f"Предупреждение: CRC не совпадает (файл: {crc32:08X}, вычислено: {crc_calc:08X})")
        
        # 5. Парсим граф (читаем векторы)
        vectors = []
        pos = 0
        vector_size = 12  # 2+2+4+4 = 12 байт на вектор
        
        while pos + vector_size <= len(graph_data):
            from_idx, to_idx, strength, prob = struct.unpack('<HHff', graph_data[pos:pos+vector_size])
            
            # Безопасно получаем имена
            from_name = names[from_idx] if from_idx < len(names) else f"node_{from_idx}"
            to_name = names[to_idx] if to_idx < len(names) else f"node_{to_idx}"
            
            vectors.append({
                "from": from_name,
                "to": to_name,
                "strength": round(strength, 2),
                "prob": round(prob, 2)
            })
            pos += vector_size
        
        # 6. Собираем узлы (уникальные имена из векторов)
        node_set = set()
        for v in vectors:
            node_set.add(v['from'])
            node_set.add(v['to'])
        
        nodes = [{"id": node_id} for node_id in sorted(list(node_set))]
        
        # 7. Формируем JVGr
        graph = {
            "nodes": nodes,
            "vectors": vectors,
            "_meta": {
                "source": bvg_file,
                "version": version,
                "crc32": f"{crc32:08X}",
                "names_count": len(names),
                "types_count": len(type_dict)
            }
        }
        
        # 8. Сохраняем
        with open(jvgr_file, 'w', encoding='utf-8') as f_out:
            json.dump(graph, f_out, ensure_ascii=False, indent=2)
        
        print(f"✓ JVGr восстановлен в {jvgr_file}")
        print(f"  Узлов: {len(nodes)}")
        print(f"  Векторов: {len(vectors)}")
        print(f"  Имен в словаре: {len(names)}")
        print(f"  Типов полей: {len(type_dict)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python bvg_to_jvgr.py input.bvg output.json")
        sys.exit(1)
    
    bvg_to_jvgr(sys.argv[1], sys.argv[2])
