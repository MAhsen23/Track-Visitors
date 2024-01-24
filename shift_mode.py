import os

def replace_text_in_files(folder_path, target_text, replacement_text):

    for filename in os.listdir(folder_path):
        if filename == "__init__.py":
            continue

        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()

            updated_content = file_content.replace(target_text, replacement_text)

            with open(file_path, 'w') as file:
                file.write(updated_content)

if __name__ == "__main__":
    folder_path = "E:\\NewPythonProjects\\FYPProject\\FYPProject\\API"
    target_text = "from FYPProject import DB_Connection"
    replacement_text = "import DB_Connection"

    replace_text_in_files(folder_path, target_text, replacement_text)

    target_text = "from FYPProject import Extras_Func"
    replacement_text = "import Extras_Func"

    replace_text_in_files(folder_path, target_text, replacement_text)
