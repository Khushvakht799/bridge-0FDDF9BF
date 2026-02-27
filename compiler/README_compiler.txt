# Компилятор JVGr → BVG

## Использование:
python compiler/jvgr_to_bvg.py <input.json> <output.bvg>

## Пример:
python compiler/jvgr_to_bvg.py 2_jvgr/example.json 3_bvg/example.bvg

## Выход:
Бинарный файл BVG со структурой:
- Заголовок (28 байт)
- Словарь имен
- Словарь типов
- Данные графа
