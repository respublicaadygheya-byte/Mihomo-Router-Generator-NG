#!/usr/bin/env python3
import json
import sys

def main():
    if len(sys.argv) < 4:
        print("Usage: splitter.py <input_file> <ru_output> <foreign_output>")
        sys.exit(1)

    input_file = sys.argv[1]
    ru_output = sys.argv[2]
    foreign_output = sys.argv[3]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            proxies = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found")
        sys.exit(1)

    # Записываем все прокси в единый файл, без деления на страны
    with open(foreign_output, 'w', encoding='utf-8') as f:
        json.dump(proxies, f, indent=2, ensure_ascii=False)

    # Создаем пустой RU-файл для совместимости с генератором
    with open(ru_output, 'w', encoding='utf-8') as f:
        json.dump([], f, indent=2, ensure_ascii=False)

    print(f"Все {len(proxies)} прокси объединены в единый список")

if __name__ == '__main__':
    main()
