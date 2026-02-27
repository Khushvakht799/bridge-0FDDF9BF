import sys
import json
import struct
import zlib

def jvgr_to_bvg(jvgr_file, bvg_file):
    # 1. Читаем JVGr с поддержкой UTF-8 BOM
    with open(jvgr_file, 'r', encoding='utf-8-sig') as f:
        content = f.read()
        try:
            graph = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            print("Первые 100 символов файла:")
            print(repr(content[:100]))
            return
    
    # 2. Собираем все уникальные имена
    names = []
    name_to_id = {}
    
    # Добавляем имена узлов
    for node in graph.get('nodes', []):
        node_id = node['id']
        if node_id not in name_to_id:
            name_to_id[node_id] = len(names)
            names.append(node_id)
    
    # Добавляем имена полей (strength, prob и т.д.), если их еще нет
    field_names = ['strength', 'prob']
    for field in field_names:
        if field not in name_to_id:
            name_to_id[field] = len(names)
            names.append(field)
    
    print(f"✓ Найдено узлов: {len([n for n in names if n not in field_names])}")
    print(f"✓ Всего имен в словаре: {len(names)}")
    
    # 3. Словарь типов
    type_dict = [
        ('strength', 1),  # float
        ('prob', 1)       # float
    ]
    
    # 4. Упаковываем NAME DICTIONARY
    name_dict_data = b''
    name_dict_data += struct.pack('<H', len(names))
    for name in names:
        name_bytes = name.encode('utf-8')
        name_dict_data += struct.pack('<B', len(name_bytes))
        name_dict_data += name_bytes
    
    # 5. Упаковываем TYPE DICTIONARY
    type_dict_data = b''
    type_dict_data += struct.pack('<H', len(type_dict))
    for type_name, type_id in type_dict:
        # Берем индекс из name_to_id
        name_idx = name_to_id[type_name]
        type_dict_data += struct.pack('<H', name_idx)
        type_dict_data += struct.pack('<B', type_id)
    
    # 6. Упаковываем GRAPH DATA
    graph_data = b''
    vectors = graph.get('vectors', [])
    for vector in vectors:
        from_idx = name_to_id.get(vector['from'], 0)
        to_idx = name_to_id.get(vector['to'], 0)
        strength = float(vector.get('strength', 1.0))
        prob = float(vector.get('prob', 1.0))
        
        graph_data += struct.pack('<H', from_idx)
        graph_data += struct.pack('<H', to_idx)
        graph_data += struct.pack('<f', strength)
        graph_data += struct.pack('<f', prob)
    
    print(f"✓ Векторов: {len(vectors)}")
    
    # 7. Вычисляем смещения
    offset_names = 28  # после заголовка
    offset_types = offset_names + len(name_dict_data)
    offset_data = offset_types + len(type_dict_data)
    
    # 8. Считаем CRC32
    crc_data = name_dict_data + type_dict_data + graph_data
    crc32 = zlib.crc32(crc_data) & 0xFFFFFFFF
    
    # 9. Формируем HEADER
    header = struct.pack('<4sBBIIII6s', 
                        b'BVG1',           # Magic
                        1,                 # Version
                        0,                 # Flags (little endian)
                        offset_names,      # OffsetNames
                        offset_types,      # OffsetTypes
                        offset_data,       # OffsetData
                        crc32,             # CRC32
                        b'\x00'*6)         # Reserved
    
    # 10. Записываем все в файл
    with open(bvg_file, 'wb') as f:
        f.write(header)
        f.write(name_dict_data)
        f.write(type_dict_data)
        f.write(graph_data)
    
    print(f"\n✅ BVG сохранен в {bvg_file}")
    print(f"  Размер файла: {len(header) + len(name_dict_data) + len(type_dict_data) + len(graph_data)} байт")
    print(f"  CRC32: {crc32:08X}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Использование: python jvgr_to_bvg.py input.json output.bvg")
        sys.exit(1)
    
    jvgr_to_bvg(sys.argv[1], sys.argv[2])
