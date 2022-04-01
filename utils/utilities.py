import yaml
import os
import base64
from pathlib import Path


def get_config(file_path) -> dict:
    """Loads config file"""
    with open(file_path) as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def create_file_and_return_its_path() -> dict:
    content_root_file_path = 'resources/file.txt'
    file_dir = content_root_file_path.split("/")[0]
    file_name = content_root_file_path.split("/")[-1]
    try:
        os.mkdir(file_dir)
    except FileExistsError:
        print(f"Directory: '{file_dir}' already exists")

    try:
        with open(content_root_file_path, 'xt+', encoding="utf-8") as output_file:
            output_file.write("test")
    except FileExistsError:
        print("Did not create a file - File already exists!")

    return {"file_path": str(Path(__file__).resolve().parent.parent.joinpath(content_root_file_path)),
            "file_name": file_name}


def get_file_content_base64(file_path):
    raw_data = open(file_path, "rb").read()
    encoded_data = base64.b64encode(raw_data)
    return encoded_data.decode('utf-8')


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)
    else:
        print(f"{file} does not exist!")
