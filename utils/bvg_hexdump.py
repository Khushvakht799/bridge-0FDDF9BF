import sys
import struct
import zlib
import json

def hex_dump(data, bytes_per_line=16):
    result = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i+bytes_per_line]
        hex_str = ' '.join(f'{b:02x}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        result.append(f'{i:04x}: {hex_str:<48} {ascii_str}')
    return '\n'.join(result)

def parse_bvg_dump(bvg_file):
    try:
        with open(bvg_file, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"❌ Файл не найден: {bvg_file}")
        return
    
    print("=" * 80)
    print("BVG HEX DUMP")
    print("=" * 80)
    print(hex_dump(data[:min(512, len(data))]))  # покажем начало
    print("=" * 80)
    
    if len(data) < 32:
        print("❌ Файл слишком мал для заголовка BVG v2")
        return
    
    # Парсим заголовок (v2 - 32 байта)
    magic = data[0:4]
    version = data[4]
    flags = data[5]
    
    print(f"\n📋 HEADER:")
    print(f"  Magic: {magic.decode()}")
    print(f"  Version: {version}")
    
    if magic == b'BVG1':
        print("  ⚠️  Это BVG v1 файл. Используйте старый hexdump или обновите файл до v2")
        # Здесь можно вызвать старый парсер, но пока просто выходим
        return
    elif magic != b'BVG2':
        print(f"❌ Не BVG файл (ожидалось BVG1/BVG2, получено {magic})")
        return
    
    # Читаем v2 заголовок полностью
    reserved1 = struct.unpack('<H', data[6:8])[0]
    offset_names = struct.unpack('<I', data[8:12])[0]
    offset_types = struct.unpack('<I', data[12:16])[0]
    offset_data = struct.unpack('<I', data[16:20])[0]
    offset_v2 = struct.unpack('<I', data[20:24])[0]
    crc32 = struct.unpack('<I', data[24:28])[0]
    reserved2 = struct.unpack('<I', data[28:32])[0]
    
    print(f"  Flags: {flags} ({'little endian' if flags & 1 == 0 else 'big endian'})")
    print(f"  Offset Names: {offset_names} (0x{offset_names:04x})")
    print(f"  Offset Types: {offset_types} (0x{offset_types:04x})")
    print(f"  Offset Data: {offset_data} (0x{offset_data:04x})")
    print(f"  Offset V2: {offset_v2} (0x{offset_v2:04x})")
    print(f"  CRC32: {crc32:08x}")
    
    # Проверяем смещения
    file_size = len(data)
    if offset_names >= file_size or offset_types >= file_size or offset_data >= file_size:
        print("❌ Смещения вне файла")
        return
    
    # --- NAME DICTIONARY ---
    print("\n📋 NAME DICTIONARY:")
    pos = offset_names
    name_count = struct.unpack('<H', data[pos:pos+2])[0]
    pos += 2
    print(f"  Count: {name_count}")
    
    names = []
    for i in range(name_count):
        name_len = data[pos]
        pos += 1
        name = data[pos:pos+name_len].decode('utf-8', errors='replace')
        pos += name_len
        names.append(name)
        print(f"  {i}: {name}")
    
    # --- TYPE DICTIONARY v2 ---
    print("\n📋 TYPE DICTIONARY v2:")
    pos = offset_types
    type_count = struct.unpack('<H', data[pos:pos+2])[0]
    pos += 2
    print(f"  Count: {type_count}")
    
    type_map = {
        1: "float", 2: "int", 3: "string", 
        4: "bool", 5: "json", 6: "vector"
    }
    
    for i in range(type_count):
        name_idx = struct.unpack('<H', data[pos:pos+2])[0]
        pos += 2
        type_id = data[pos]
        pos += 1
        type_name = type_map.get(type_id, f"unknown({type_id})")
        field_name = names[name_idx] if name_idx < len(names) else f"field_{name_idx}"
        print(f"  {i}: {field_name} -> {type_name}")
    
    # --- GRAPH DATA v1 ---
    print("\n📋 GRAPH DATA (v1):")
    pos = offset_data
    vector_count = 0
    vector_size = 12
    
    v1_vectors = []
    while pos + vector_size <= offset_v2 and pos + vector_size <= file_size:
        try:
            from_idx = struct.unpack('<H', data[pos:pos+2])[0]
            to_idx = struct.unpack('<H', data[pos+2:pos+4])[0]
            strength = struct.unpack('<f', data[pos+4:pos+8])[0]
            prob = struct.unpack('<f', data[pos+8:pos+12])[0]
            
            from_name = names[from_idx] if from_idx < len(names) else f"node_{from_idx}"
            to_name = names[to_idx] if to_idx < len(names) else f"node_{to_idx}"
            
            print(f"  Vector {vector_count}: {from_name} -> {to_name} | strength={strength:.2f} prob={prob:.2f}")
            v1_vectors.append((from_idx, to_idx, strength, prob))
            
            pos += vector_size
            vector_count += 1
        except Exception as e:
            print(f"  ❌ Ошибка на векторе {vector_count}: {e}")
            break
    
    print(f"\n  Всего v1 векторов: {vector_count}")
    
    # --- V2 DATA (если есть) ---
    if offset_v2 > 0 and offset_v2 < file_size:
        print("\n📋 V2 ATTRIBUTES:")
        pos = offset_v2
        
        # NODE ATTRIBUTES
        if pos + 2 > file_size:
            print("  ❌ Нет места для node_count")
        else:
            node_attr_count = struct.unpack('<H', data[pos:pos+2])[0]
            pos += 2
            print(f"\n  Node attributes: {node_attr_count}")
            
            for i in range(node_attr_count):
                if pos + 3 > file_size:
                    print(f"    ❌ Узел {i}: преждевременный конец файла")
                    break
                
                node_idx = struct.unpack('<H', data[pos:pos+2])[0]
                pos += 2
                flags_byte = data[pos]
                pos += 1
                
                node_name = names[node_idx] if node_idx < len(names) else f"node_{node_idx}"
                print(f"    Node {node_idx} ({node_name}): flags=0x{flags_byte:02x}")
                
                if flags_byte & 0x01:  # has_state
                    state_idx = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    state_val = names[state_idx] if state_idx < len(names) else f"state_{state_idx}"
                    print(f"      state: {state_val}")
                
                if flags_byte & 0x02:  # has_intent
                    intent_idx = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    intent_val = names[intent_idx] if intent_idx < len(names) else f"intent_{intent_idx}"
                    print(f"      intent: {intent_val}")
                
                if flags_byte & 0x04:  # has_meta
                    meta_len = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    meta_str = data[pos:pos+meta_len].decode('utf-8', errors='replace')
                    pos += meta_len
                    try:
                        meta_json = json.loads(meta_str)
                        print(f"      meta: {json.dumps(meta_json, ensure_ascii=False)}")
                    except:
                        print(f"      meta: {meta_str}")
        
        # VECTOR ATTRIBUTES
        if pos + 2 <= file_size:
            vec_attr_count = struct.unpack('<H', data[pos:pos+2])[0]
            pos += 2
            print(f"\n  Vector attributes: {vec_attr_count}")
            
            for i in range(vec_attr_count):
                if pos + 3 > file_size:
                    print(f"    ❌ Вектор {i}: преждевременный конец файла")
                    break
                
                vec_idx = struct.unpack('<H', data[pos:pos+2])[0]
                pos += 2
                flags_byte = data[pos]
                pos += 1
                
                print(f"    Vector {vec_idx}: flags=0x{flags_byte:02x}")
                
                if flags_byte & 0x01:  # has_state
                    state_idx = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    state_val = names[state_idx] if state_idx < len(names) else f"state_{state_idx}"
                    print(f"      state: {state_val}")
                
                if flags_byte & 0x02:  # has_intent
                    intent_idx = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    intent_val = names[intent_idx] if intent_idx < len(names) else f"intent_{intent_idx}"
                    print(f"      intent: {intent_val}")
                
                if flags_byte & 0x04:  # has_meta
                    meta_len = struct.unpack('<H', data[pos:pos+2])[0]
                    pos += 2
                    meta_str = data[pos:pos+meta_len].decode('utf-8', errors='replace')
                    pos += meta_len
                    print(f"      meta: {meta_str}")
    
    # --- CRC CHECK ---
    # Вычисляем CRC по данным от offset_names до конца
    crc_data = data[offset_names:]
    crc_calc = zlib.crc32(crc_data) & 0xFFFFFFFF
    print(f"\n📋 CRC CHECK:")
    print(f"  CRC в заголовке: {crc32:08x}")
    print(f"  Вычисленный CRC: {crc_calc:08x}")
    print(f"  Совпадение: {'✅' if crc32 == crc_calc else '❌'}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python bvg_hexdump.py <file.bvg>")
        sys.exit(1)
    
    parse_bvg_dump(sys.argv[1])
