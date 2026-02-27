import sys
import struct

def bvg_info(bvg_file):
    with open(bvg_file, 'rb') as f:
        header = f.read(28)
        magic, version, flags, offset_names, offset_types, offset_data, crc32, reserved = \
            struct.unpack('<4sBBIIII6s', header)
        
        print("=== BVG Info ===")
        print(f"Magic: {magic.decode()}")
        print(f"Version: {version}")
        print(f"Flags: {'little' if flags==0 else 'big'} endian")
        print(f"Offset Names: {offset_names}")
        print(f"Offset Types: {offset_types}")
        print(f"Offset Data: {offset_data}")
        print(f"CRC32: {crc32:08X}")
        
        # Читаем имена
        f.seek(offset_names)
        name_count = struct.unpack('<H', f.read(2))[0]
        print(f"\nNames ({name_count}):")
        for i in range(name_count):
            name_len = struct.unpack('<B', f.read(1))[0]
            name = f.read(name_len).decode('utf-8')
            print(f"  {i}: {name}")
        
        # Читаем типы
        f.seek(offset_types)
        type_count = struct.unpack('<H', f.read(2))[0]
        print(f"\nTypes ({type_count}):")
        for i in range(type_count):
            name_idx = struct.unpack('<H', f.read(2))[0]
            type_id = struct.unpack('<B', f.read(1))[0]
            type_name = ['float', 'int', 'string'][type_id-1] if 1 <= type_id <= 3 else 'unknown'
            print(f"  {i}: name_idx={name_idx} type={type_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python bvg_info.py file.bvg")
        sys.exit(1)
    
    bvg_info(sys.argv[1])
