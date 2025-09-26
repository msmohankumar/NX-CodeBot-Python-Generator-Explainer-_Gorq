import os
import json

def folder_py_to_json(folder_path, output_json_path):
    py_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f"Found file: {file_path}")  # Debug here
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                py_files.append({
                    'filename': os.path.relpath(file_path, folder_path).replace('\\', '/'),
                    'content': content
                })
    with open(output_json_path, 'w', encoding='utf-8') as json_file:
        json.dump(py_files, json_file, indent=4)

folder_path = r"C:\Users\MSM6BAN\Downloads\NX-CodeBot-Python-Generator--main\NX-CodeBot-Python-Generator--main\nx_examples"
output_json_file = "nx_examples_as_json.json"

folder_py_to_json(folder_path, output_json_file)
