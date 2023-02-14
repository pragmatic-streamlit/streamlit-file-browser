import os
import glob
import pathlib
from urllib.parse import urljoin
from html import escape
from base64 import b64encode
from functools import reduce

from filetype import image_match, video_match, audio_match
import streamlit as st
import streamlit.components.v1 as components
from streamlit_molstar import st_molstar, st_molstar_remote


_DEVELOP_MODE = os.getenv('DEVELOP_MODE')
# _DEVELOP_MODE = True

if _DEVELOP_MODE:
    _component_func = components.declare_component(
        "streamlit_file_browser",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("streamlit_file_browser", path=build_dir)


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
    return st_molstar_remote(url) if url else st_molstar(abs_path)

def _do_csv_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    import pandas as pd
    st.dataframe(pd.read_csv(abs_path))

def _do_json_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.json(f.read())

def _do_plain_preview(root, file_path, url):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.text(f.read())


PREVIEW_HANDLERS = {
    extention: handler 
    for extentions, handler in [
        (('.pdb', '.pdbqt', '.sdf', '.cif', '.mol', '.mol2', '.xyz'), _do_molecule_preview),
        (('.json',), _do_json_preview),
        (('.pdf',), _do_pdf_preview),
        (('.csv',), _do_csv_preview),
        (('.log', '.txt', '.md'), _do_plain_preview)
    ]
    for extention in extentions
}


def _show_file_preview(root, selected_file, artifacts_site):
    abs_path = os.path.join(root, selected_file["path"])
    ext = os.path.splitext(selected_file["name"])[1]
    if ext in PREVIEW_HANDLERS:
        try:
            url = urljoin(urljoin(artifacts_site, 'artifacts/'), selected_file["path"]) if artifacts_site else None
            PREVIEW_HANDLERS[ext](root, selected_file["path"], url)
        except Exception as e:
            st.error(f'failed preview {selected_file["path"]}')
            st.exception(e)
    elif ft := image_match(abs_path):
        st.image(abs_path)
    elif ft := video_match(abs_path):
        st.video(abs_path, format=ft.mime)
    elif ft := audio_match(abs_path):
        st.audio(abs_path, format=ft.mime)
    else:
        st.info(f"No preview aviable for {ext}")

def _get_file_info(root, path):
    stat = os.stat(path)
    info = {
        "path": path[len(root)+1:],
        "size": stat.st_size,
        "create_time": stat.st_ctime,
        "update_time": stat.st_mtime,
        "access_time": stat.st_atime,
    }
    info['name'] = os.path.basename(path)
    return info


def st_file_browser(path: str, *, show_preview=True, show_preview_top=False,
        glob_pattern='*',
        show_choose_file=False, show_download_file=True, artifacts_site=None, key=None):
    root = pathlib.Path(os.path.abspath(path))
    files = list(filter(lambda item: item.is_file(), root.rglob(glob_pattern)))
    files = [_get_file_info(str(root), str(path)) for path in files]
    if show_preview and show_preview_top:
        with st.expander('', expanded=True):
            preview = st.container()
    event = _component_func(files=files,
        show_choose_file=show_choose_file,
        show_download_file=show_download_file,
        artifacts_site=artifacts_site, key=key)
    if event:
        if event["type"] == "SELECT_FILE":
            file = event["target"]
            if show_preview and show_preview_top:
                with preview:
                    _show_file_preview(file, artifacts_site)
            elif show_preview and not show_preview_top:
                with st.expander('', expanded=True):
                    _show_file_preview(str(root), file, artifacts_site)
    return event


if _DEVELOP_MODE:
    st.header('Default Options')
    event = st_file_browser("example_artifacts", key='A')
    st.write(event)

    st.header('With Artifacts Server, Allow choose file, disable download')
    event = st_file_browser("example_artifacts", artifacts_site="http://localhost:1024", show_choose_file=True, show_download_file=False, key='B')
    st.write(event)

    st.header('Show only molecule files')
    event = st_file_browser("example_artifacts", artifacts_site="http://localhost:1024", show_choose_file=True, show_download_file=False, glob_pattern='molecule/*', key='C')
    st.write(event)