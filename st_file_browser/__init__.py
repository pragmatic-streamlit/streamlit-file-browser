import os
from functools import reduce
import streamlit.components.v1 as components

_DEVELOP_MODE = os.getenv('DEVELOP_MODE')
# _DEVELOP_MODE = True

if _DEVELOP_MODE:
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

if _DEVELOP_MODE:
    import viz
    import pandas as pd
    import streamlit as st
    import json
    test_path = "../test"
    event = st_file_browser(test_path)
    def show_file_content(selected_file):
        support_exts = {
            "sdf": viz.show_ligand,
            "csv": lambda path: st.dataframe(pd.read_csv(path)),
            "mol": viz.show_molecule,
            "pdb": viz.show_protein,
            "json": lambda path: st.json(json.loads((f := open(path), f.read(), f.close())[1])),
            "txt": lambda path: st.write((f := open(path), f.read(), f.close())[1])
        }
        if selected_file:
            ext = os.path.splitext(selected_file["name"])[1][1:]
            if ext in support_exts:
                support_exts[ext](selected_file["absolute_path"])

    if event:
        if event["type"] == "SELECT_FILE":
            file = event["target"]
            show_file_content(file)
        elif event["type"] == "DOWNLOAD":
            ...
        else:
            print(f'\033[1;31maction({event["type"]}) be not supported\033[0m')
            