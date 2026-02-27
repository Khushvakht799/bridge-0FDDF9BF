# BRIDGE — Текстовый мост в бинарные графы

## Полный цикл:
1. Текст -> JVGr (utils/text_to_jvgr.py)
2. JVGr -> BVG  (compiler/jvgr_to_bvg.py)
3. BVG  -> JVGr (decompiler/bvg_to_jvgr.py)
4. JVGr -> текст (руками, через просмотр)

## Структура:
- 1_input/    исходные тексты (ТЗ, spec)
- 2_jvgr/     JSON Vector Graph (человекочитаемый)
- 3_bvg/      Binary Vector Graph (машинный)
- 4_output/   восстановленные JVGr

## Быстрый старт:
См. инструкции в compiler/ и decompiler/
