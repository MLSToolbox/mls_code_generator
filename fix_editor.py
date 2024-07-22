import json
from src.mls_code_generator.utils import fix_editor

if __name__ == '__main__':

    file_path = 'editor.json'
    out_path = 'fixed_editor.json'

    content = json.load(open(file_path))

    new_content = fix_editor(content)

    json.dump(new_content, open(out_path, 'w'), indent=4)

