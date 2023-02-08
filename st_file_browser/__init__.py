import os
from functools import reduce
import streamlit.components.v1 as components

_DEVELOP_MODE = os.getenv('DEVELOP_MODE')

if not _DEVELOP_MODE:
    _component_func = components.declare_component(
        "st_file_browser",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_file_browser", path=build_dir)

# class File:
#     name: str
#     absolute_path: str
#     relative_path: str
#     is_dir: bool
#     size: int
#     access_time: int
#     create_time: int
#     update_time: int
#     children: List[Self]
    
def get_files_from_dir(path: str, relative: str = ""):
    file = {}
    file["name"] = os.path.basename(path)
    file["absolute_path"] = os.path.abspath(path)
    file["relative_path"] = os.path.join(relative, os.path.basename(path))
    file["is_dir"] = os.path.isdir(path)
    stat = os.stat(path)
    file["size"] = stat.st_size
    file["create_time"] = stat.st_ctime
    file["update_time"] = stat.st_mtime
    file["access_time"] = stat.st_atime
    file["children"] = None
    children = []
    if os.path.isdir(path):
        for f in os.scandir(path):
            children.append(get_files_from_dir(f.path, file["relative_path"]))
        file["children"] = children
    return file

def flat_files_tree(files_arr):
    if not files_arr:
        return []
    return reduce(lambda a, b: a + flat_files_tree(b["children"]) if b["is_dir"] else a + [b], files_arr, [])
    

def st_file_browser(path: str):
    res = get_files_from_dir(path)
    flat_files = flat_files_tree([res])
    component_value = _component_func(files=flat_files)
    return component_value

if not _DEVELOP_MODE:
    test_path = "../test"
    selected_file = st_file_browser(test_path)
    print("selected file: ", selected_file)
