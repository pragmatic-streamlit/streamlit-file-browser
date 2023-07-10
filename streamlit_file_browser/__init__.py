import os
import re
import json
import os.path
import pathlib
from wcmatch import glob
from urllib.parse import urljoin
from html import escape
from base64 import b64encode

from filetype import image_match, video_match, audio_match
import streamlit as st
import numpy as np
import streamlit.components.v1 as components
from streamlit_molstar import st_molstar, st_molstar_remote
from streamlit_antd.table import st_antd_table
from streamlit_embeded import st_embeded

_DEVELOP_MODE = os.getenv('DEVELOP_MODE') or os.getenv('FILE_BROWSER_DEVELOP_MODE')
CACHE_FILE_NAME = ".st-tree.cache"

if _DEVELOP_MODE:
    _component_func = components.declare_component(
        "streamlit_file_browser",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("streamlit_file_browser", path=build_dir)


def render_static_file_server(
    key,
    path: str,
    static_file_server_path: str,
    show_choose_file: bool = False,
    show_download_file: bool = False,
    show_delete_file: bool = False,
    show_new_folder: bool = False,
    show_upload_file: bool = False,
    ignore_file_select_event: bool = False,
):
    if not static_file_server_path:
        print("static_file_server_path is required")
        return None
    event = _component_func(
        files=None,
        path=path,
        static_file_server_path=static_file_server_path,
        show_choose_file=show_choose_file,
        show_download_file=show_download_file,
        show_delete_file=show_delete_file,
        show_new_folder=show_new_folder,
        show_upload_file=show_upload_file,
        ignore_file_select_event=ignore_file_select_event,
        key=key,
    )
    return event

def _do_code_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.code(f.read())

def _do_pdf_preview(root, file_path, url, height="420px"):
    abs_path = os.path.join(root, file_path)
    if url:
        safe_url = escape(url)
    else:
        with open(abs_path, 'rb') as f:
            data = b64encode(f.read()).decode("utf-8")
        safe_url = f"data:application/pdf;base64,{data}"
    pdf_display = (
        f'<iframe src="{safe_url}" width="100%" min-height="240px" height="{height} type="application/pdf"></iframe>'
    )
    st.markdown(pdf_display, unsafe_allow_html=True)

def _do_molecule_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    test_traj_path = os.path.splitext(abs_path)[0] + '.xtc'
    if os.path.exists(test_traj_path):
        traj_path = test_traj_path
        traj_url = os.path.splitext(url)[0] + '.xtc' if url else None
    else:
        traj_path = None
        traj_url = None
    return st_molstar_remote(url, traj_url) if url else st_molstar(abs_path, traj_path)

def _do_csv_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    import pandas as pd

    df = pd.read_csv(abs_path)
    mask = df.applymap(type) != bool
    d = {True: 'True', False: 'False'}
    df = df.where(mask, df.replace(d))
    df = df.replace(np.nan, None)
    st.dataframe(df)

def _do_tsv_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    import pandas as pd

    df = pd.read_table(abs_path)
    mask = df.applymap(type) != bool
    d = {True: 'True', False: 'False'}
    df = df.where(mask, df.replace(d))
    df = df.replace(np.nan, None)
    st.dataframe(df)

def _do_json_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.json(f.read())

def _do_html_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st_embeded(f.read())

def _do_plain_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.text(f.read())


# RNA Secondary Structure Formats
# DB (dot bracket) format (.db, .dbn) is a plain text format that can encode secondory structure.
def _do_dbn_preview(root, file_path, url):
    print('dbn file path:', file_path)
    abs_path = os.path.join(root, file_path)
    valid_content = []
    with open(abs_path) as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith(">") or line.startswith("#") or not line:
                continue

            valid_content.append(line)

    if len(valid_content) == 1:
        # structure is optional
        valid_content.append("")

    params = f'sequence={valid_content[0]}&structure={valid_content[1]}'
    url = r'http://nibiru.tbi.univie.ac.at/forna/forna.html?id=url/name&' + params
    components.iframe(url, height=500, scrolling=False)


PREVIEW_HANDLERS = {
    extention: handler 
    for extentions, handler in [
        (('.pdb', '.pdbqt', '.ent', '.trr', '.nctraj', '.nc', '.ply', '.bcif', '.sdf', '.cif', '.mol', '.mol2', '.xyz', '.sd', '.gro'), _do_molecule_preview),
        (('.json',), _do_json_preview),
        (('.pdf',), _do_pdf_preview),
        (('.csv',), _do_csv_preview),
        (('.tsv',), _do_tsv_preview),
        (('.log', '.txt', '.md', '.upf', '.UPF', '.orb'), _do_plain_preview),
        (('.py', '.sh'), _do_code_preview),
        (('.html', '.htm'), _do_html_preview),
        (('.dbn',), _do_dbn_preview)
    ]
    for extention in extentions
}


def show_file_preview(root, selected_file, artifacts_site, height=None):
    target_path = selected_file["path"]
    abs_path = os.path.join(root, target_path)
    basename = os.path.basename(target_path)
    
    preview_raw = False
    if basename in ('POSCAR', 'CONTCAR', 'POSCAR.txt', 'CONTCAR.txt'):
        basename = f'{basename}.cif'
        target_path = os.path.join(os.path.dirname(target_path), basename)
        abs_target_path = os.path.join(root, target_path)
        if not os.path.exists(abs_target_path):
            from pymatgen.core import Structure
            structure = Structure.from_file(abs_path)
            structure.make_supercell(scaling_matrix=[3, 3, 3], to_unit_cell=False)
            structure.to(filename=abs_target_path)
        st.caption('scaling_matrix=[3, 3, 3]')
        preview_raw = True

    ext = os.path.splitext(target_path)[1]
    if ext in PREVIEW_HANDLERS:
        try:
            url = urljoin(artifacts_site, target_path) if artifacts_site else None
            PREVIEW_HANDLERS[ext](root, target_path, url)
        except Exception as e:
            st.error(f'failed preview {target_path}')
            st.exception(e)
    elif ft := image_match(abs_path):
        st.image(abs_path)
    elif ft := video_match(abs_path):
        st.video(abs_path, format=ft.mime)
    elif ft := audio_match(abs_path):
        st.audio(abs_path, format=ft.mime)
    elif basename in ('STDOUTERR', 'INPUT', 'KPT', 'STRU', 'STRU_ION_D', 'kpoints', 'istate.info', 'PDOS', 'TDOS') or (
        basename.startswith('STRU_ION') and basename.endswith('_D')
    ) or (basename.startswith('BANDS_') and basename.endswith('.dat')):
        with open(abs_path) as f:
            st.text(f.read())
    else:
        st.info(f"No preview aviable for {ext}")
    if preview_raw:
        with open(abs_path) as f:
            st.text(f.read())

def _get_file_info(root, path):
    stat = os.stat(path)
    info = {
        "path": path[len(root)+1:],
        "size": stat.st_size,
        "create_time": stat.st_ctime * 1000,
        "update_time": stat.st_mtime * 1000,
        "access_time": stat.st_atime * 1000,
    }
    info['name'] = os.path.basename(path)
    return info


def ensure_tree_cache(
        path: str,
        glob_patterns=('**/*',),
        file_ignores=None,
        limit=10000,
        use_cache: bool = False,
        force_rebuild: bool = False):
    cache_path = os.path.join(path, CACHE_FILE_NAME)
    if use_cache and not force_rebuild and os.path.exists(cache_path):
        with open(cache_path, 'r') as cache_file:
            files = json.load(cache_file)
            return files

    root = pathlib.Path(os.path.abspath(path))

    files = [root / f for f in glob.glob(root_dir=path, patterns=glob_patterns, flags=glob.GLOBSTAR | glob.NODIR, limit=limit)]
    for ignore in (file_ignores or []):
        files = filter(lambda f: (not ignore.match(os.path.basename(f))) if isinstance(ignore, re.Pattern) else (
                    os.path.basename(f) not in file_ignores), files)
    files = [_get_file_info(str(root), str(path)) for path in files]

    if use_cache:
        with open(cache_path, 'w+') as cache_file:
            json.dump(files, cache_file)

    return files


def st_file_browser(path: str, *, show_preview=True, show_preview_top=False,
        glob_patterns=('**/*',), ignore_file_select_event=False,
        file_ignores=None,
        select_filetype_ignores=None,
        extentions=None,
        show_delete_file=False,
        show_choose_file=False, show_download_file=True,
        show_new_folder=False, show_upload_file=False,
        limit=10000,
        artifacts_site=None, artifacts_download_site=None,
        key=None,
        use_cache=False,
        use_static_file_server=False,
        static_file_server_path=None,):
    extentions = tuple(extentions) if extentions else None
    root = pathlib.Path(os.path.abspath(path))
    if use_static_file_server and static_file_server_path:
        event = render_static_file_server(
            key,
            path,
            static_file_server_path,
            show_choose_file,
            show_download_file,
            show_delete_file,
            show_new_folder,
            show_upload_file,
        )
    else:
        files = ensure_tree_cache(
            path,
            glob_patterns,
            file_ignores,
            limit,
            use_cache=use_cache,
        )

        files = [file for file in files if str(file["path"]).endswith(extentions)] if extentions else files
        if show_preview and show_preview_top:
            with st.expander('', expanded=True):
                preview = st.container()
        if not artifacts_download_site and artifacts_site:
            artifacts_download_site = artifacts_site
        event = _component_func(files=files,
            show_choose_file=show_choose_file,
            show_download_file=show_download_file,
            show_delete_file=show_delete_file,
            ignore_file_select_event=ignore_file_select_event,
            artifacts_download_site=artifacts_download_site,
            artifacts_site=artifacts_site, key=key)
    if event:
        if event["type"] == "SELECT_FILE" and ((not select_filetype_ignores) or (not any(event["target"]['path'].endswith(ft) for ft in select_filetype_ignores))):
            file = event["target"]
            if "path" in file:
                if not os.path.exists(os.path.join(root, file["path"])):
                    st.warning(f"File {file['path']} not found")
                    return event
            if show_preview and show_preview_top:
                with preview:
                    show_file_preview(file, artifacts_site)
            elif show_preview and not show_preview_top:
                with st.expander('', expanded=True):
                    show_file_preview(str(root), file, artifacts_site)
    return event
                

if _DEVELOP_MODE or os.getenv('SHOW_FILE_BROWSER_DEMO'):
    current_path = os.path.dirname(os.path.abspath(__file__))
    import time

    st.header('Deep glob')
    start_time = time.time()
    # If you use the static file server, you must make sure
    # that the path listened to by the static file server
    # is the same as the path passed to st_file_browser by root.
    event = st_file_browser(os.path.join(current_path, "..", "example_artifacts/static_file_server/root"),
        key="deep",
        use_static_file_server=True,
        show_choose_file=True,
        show_delete_file=True,
        show_download_file=False,
        show_new_folder=True,
        show_upload_file=False,
        static_file_server_path="http://localhost:9999/?choose=true",
    )
    print(event)
    end_time = time.time()
    execution_time = end_time - start_time
    st.write(f"代码段执行时间: {execution_time:.6f} 秒")
    st.write(event)
    
    from streamlit_antd.tabs import st_antd_tabs
    tab_event = st_antd_tabs([{'Label': 'Upload from local'}, {'Label': 'Choose from workspace'}], key='tab')
    if tab_event and tab_event['Label'] == 'Choose from workspace':
        event = st_file_browser(os.path.join(current_path, "..", "example_artifacts"),
                            artifacts_site="http://localhost:1024/artifacts/", 
                            artifacts_download_site="http://localhost:1024/download/artifacts/", 
                            show_choose_file=True, show_download_file=True, glob_patterns=('molecule/**/*',), key='CC')
    else:
        event = st.file_uploader(key="ding", label="upload file")
    
    
    
    st.header('Default Options')
    event = st_file_browser(os.path.join(current_path, "..", "example_artifacts"),
                            file_ignores=('a.py', 'a.txt', re.compile('.*.pdb')),
                            key='A')
    st.write(event)

    st.header('With Artifacts Server, Allow choose & download')
    event = st_file_browser(os.path.join(current_path, "..", "example_artifacts"),
                            artifacts_site="http://localhost:1024/artifacts/",
                            artifacts_download_site="http://localhost:1024/download/artifacts/", 
                            show_choose_file=True, show_download_file=True, key='B')
    st.write(event)

    st.header('Show only molecule files')
    event = st_file_browser(os.path.join(current_path, "..", "example_artifacts"),
                            artifacts_site="http://localhost:1024/artifacts/", 
                            artifacts_download_site="http://localhost:1024/download/artifacts/", 
                            show_choose_file=True, show_download_file=True, glob_patterns=('molecule/**/*',), key='C')
    st.write(event)

    st.header('Show only molecule files in sub directory')
    event = st_file_browser(os.path.join(current_path, "..", "example_artifacts/molecule"),
                            artifacts_site="http://localhost:1024/artifacts/molecule/", 
                            artifacts_download_site="http://localhost:1024/download/artifacts/molecule/",
                            show_choose_file=True, show_download_file=True, glob_patterns=('*',), key='D')
    st.write(event)