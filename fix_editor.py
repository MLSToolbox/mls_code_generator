""" Fix editor.json file """

import json
from src.mls_code_generator.utils import fix_editor

if __name__ == '__main__':

    FILE_PATH = 'editor.json'
    OUT_PATH = 'fixed_editor.json'

    with open(FILE_PATH, 'r', encoding='utf-8') as file:
        content = json.load(file)

        new_content = fix_editor(content)

        with open(OUT_PATH, 'w', encoding='utf-8') as out_file:
            json.dump(new_content, out_file, indent=4)
