import os
import re
import json
import os.path
import pathlib
import copy
from wcmatch import glob
from urllib.parse import urljoin
from html import escape
from base64 import b64encode
import urllib
from functools import partial

from binaryornot.check import is_binary
from filetype import image_match, video_match, audio_match
import streamlit as st
import numpy as np
import streamlit.components.v1 as components
from streamlit_ace import st_ace
from streamlit_molstar import st_molstar, st_molstar_remote
from streamlit_molstar.auto import st_molstar_auto
from streamlit_embeded import st_embeded

_DEVELOP_MODE = os.getenv("STREAMLIT_FILE_BROWSER_DEVELOP_MODE")
# _DEVELOP_MODE = True

CACHE_FILE_NAME = ".st-tree.cache"

if _DEVELOP_MODE:
    _component_func = components.declare_component(
        "streamlit_file_browser",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component(
        "streamlit_file_browser", path=build_dir
    )


def render_static_file_server(
    key,
    path: str,
    static_file_server_path: str,
    show_choose_file: bool = False,
    show_choose_folder: bool = False,
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
        show_choose_folder=show_choose_folder,
        show_download_file=show_download_file,
        show_delete_file=show_delete_file,
        show_new_folder=show_new_folder,
        show_upload_file=show_upload_file,
        ignore_file_select_event=ignore_file_select_event,
        key=key,
    )
    return event


def _do_code_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.code(f.read(), **kwargs)


def _do_pdf_preview(root, file_path, url, height="420px", **kwargs):
    abs_path = os.path.join(root, file_path)
    if url:
        safe_url = escape(url)
    else:
        with open(abs_path, "rb") as f:
            data = b64encode(f.read()).decode("utf-8")
        safe_url = f"data:application/pdf;base64,{data}"
    pdf_display = f'<iframe src="{safe_url}" width="100%" min-height="240px" height="{height} type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def _do_molecule_preview(root, file_path, url, **kwargs):
    use_auto = kwargs.pop("use_auto", False)
    abs_path = os.path.join(root, file_path)
    test_traj_path = os.path.splitext(abs_path)[0] + ".xtc"
    if os.path.exists(test_traj_path):
        traj_path = test_traj_path
        traj_url = os.path.splitext(url)[0] + ".xtc" if url else None
    else:
        traj_path = None
        traj_url = None
    if use_auto:
        st_molstar_auto(
            [{"file": url, "local": abs_path} if url else abs_path], **kwargs
        )
    else:
        if url:
            st_molstar_remote(url, traj_url, **kwargs)
        else:
            st_molstar(abs_path, traj_path, **kwargs)
    return True


def _do_csv_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    import pandas as pd

    df = pd.read_csv(abs_path)
    mask = df.applymap(type) != bool
    d = {True: "True", False: "False"}
    df = df.where(mask, df.replace(d))
    df = df.replace(np.nan, None)
    st.dataframe(df, **kwargs)
    return True


def _do_tsv_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    import pandas as pd

    df = pd.read_table(abs_path)
    mask = df.applymap(type) != bool
    d = {True: "True", False: "False"}
    df = df.where(mask, df.replace(d))
    df = df.replace(np.nan, None)
    st.dataframe(df, **kwargs)
    return True


def _do_json_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        st.json(f.read(), **kwargs)


def _do_html_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        html = f.read()
        # TODO fix this hardcode

        artifacts_url = urljoin("https://launching.mlops.dp.tech/artifacts/", file_path[: file_path.rfind("/")+1])
        print(f"artifacts_url old: {artifacts_url}")
        artifacts_url = url[: url.rfind("/")+1]
        print(f"artifacts_url: {artifacts_url}")
        artifacts_url = artifacts_url.replace("https://launching.mlops.dp.tech/users/", "https://launching.mlops.dp.tech/artifacts/users/")
        artifacts_url = artifacts_url.replace("https://canary-launching.mlops.dp.tech/users/", "https://canary-launching.mlops.dp.tech/artifacts/users/")
        html = html.replace("launching-artifacts://", artifacts_url)
        st_embeded(html, **kwargs)
    return True


def _do_markdown_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        key = f'{kwargs.get("key", abs_path)}-preview'
        st.markdown(f.read(), unsafe_allow_html=True)


def _do_plain_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    with open(abs_path) as f:
        key = f'{kwargs.get("key", abs_path)}-preview'
        st_ace(value=f.read(), readonly=True, show_gutter=False, key=key)


# RNA Secondary Structure Formats
# DB (dot bracket) format (.db, .dbn) is a plain text format that can encode secondory structure.
def _do_dbn_preview(root, file_path, url, **kwargs):
    abs_path = os.path.join(root, file_path)
    content = ""
    with open(abs_path, "r", encoding="utf8") as f:
        content = f.read()

    encoding = urllib.parse.urlencode(
        {"id": "fasta", "file": content}, safe=r"()[]{}>#"
    )
    encoding = encoding.replace("%0A", "%5Cn").replace("#", ">")
    url = r"https://mrna-proxy.mlops.dp.tech/forna/forna.html?" + encoding
    components.iframe(url, height=600)


PREVIEW_HANDLERS = {
    extention: handler
    for extentions, handler in [
        (
            (
                ".pdb",
                ".pdbqt",
                ".ent",
                ".trr",
                ".nctraj",
                ".nc",
                ".ply",
                ".bcif",
                ".sdf",
                ".cif",
                ".mol",
                ".mol2",
                ".xyz",
                ".sd",
                ".gro",
                ".mrc",
            ),
            _do_molecule_preview,
        ),
        ((".mrc",), partial(_do_molecule_preview, use_auto=True)),
        ((".json",), _do_json_preview),
        ((".pdf",), _do_pdf_preview),
        ((".csv",), _do_csv_preview),
        ((".tsv",), _do_tsv_preview),
        ((".log", ".txt", ".md", ".upf", ".UPF", ".orb"), _do_plain_preview),
        ((".md",), _do_markdown_preview),
        ((".py", ".sh"), _do_code_preview),
        ((".html", ".htm"), _do_html_preview),
        ((".dbn",), _do_dbn_preview),
    ]
    for extention in extentions
}


def show_file_preview(
    root,
    selected_file,
    artifacts_site,
    key=None,
    height=None,
    overide_preview_handles=None,
    **kwargs,
):
    target_path = selected_file["path"]
    abs_path = os.path.join(root, target_path)
    basename = os.path.basename(target_path)
    preview_raw = not is_binary(abs_path)
    if preview_raw:
        preview, raw = st.tabs(["Preview", "Text"])
    else:
        preview, raw = st.container(), None

    with preview:
        if basename in ("POSCAR", "CONTCAR", "POSCAR.txt", "CONTCAR.txt"):
            basename = f"{basename}.cif"
            target_path = os.path.join(os.path.dirname(target_path), basename)
            abs_target_path = os.path.join(root, target_path)
            if not os.path.exists(abs_target_path):
                from pymatgen.core import Structure

                structure = Structure.from_file(abs_path)
                structure.to(filename=abs_target_path, **kwargs)

        ext = os.path.splitext(target_path)[1]
        text_mode = not is_binary(abs_path)
        handles = copy.copy(PREVIEW_HANDLERS)
        handles.update(overide_preview_handles or {})
        if ext in handles:
            try:
                handler = handles[ext]
                url = urljoin(artifacts_site, target_path) if artifacts_site else None
                handler(root, target_path, url, **kwargs)
            except Exception as e:
                st.error(f"failed preview {target_path}")
                st.exception(e)
        elif ft := image_match(abs_path):
            st.image(abs_path, **kwargs)
        elif ft := video_match(abs_path):
            st.video(abs_path, format=ft.mime, **kwargs)
        elif ft := audio_match(abs_path):
            st.audio(abs_path, format=ft.mime, **kwargs)
        elif not text_mode:
            st.info(f"No preview aviable for {ext}")

    if raw:
        with raw:
            with open(abs_path) as f:
                rs = f.readlines(10000)
                if len(rs) == 10000:
                    st.warning("File too large, only show first 10000 lines")
                key = f"{kwargs.get('key', abs_path)}-raw"
                st_ace(value="".join(rs), readonly=True, show_gutter=False, key=key)


def _get_file_info(root, path):
    stat = os.stat(path)
    info = {
        "path": path[len(root) + 1 :],
        "size": stat.st_size,
        "create_time": stat.st_ctime * 1000,
        "update_time": stat.st_mtime * 1000,
        "access_time": stat.st_atime * 1000,
    }
    info["name"] = os.path.basename(path)
    return info


def ensure_tree_cache(
    path: str,
    glob_patterns=("**/*",),
    file_ignores=None,
    limit=10000,
    use_cache: bool = False,
    force_rebuild: bool = False,
):
    cache_path = os.path.join(path, CACHE_FILE_NAME)
    if use_cache and not force_rebuild and os.path.exists(cache_path):
        with open(cache_path, "r") as cache_file:
            return json.load(cache_file)

    root = pathlib.Path(os.path.abspath(path))

    _files = [
        root / f
        for f in glob.glob(
            root_dir=path,
            patterns=glob_patterns,
            flags=glob.GLOBSTAR | glob.NODIR,
            limit=limit,
        )
    ]
    
    ignore_collection = {}
    def _check_ignore(f, ignore):
        if isinstance(ignore, re.Pattern):
            if not ignore.match(os.path.basename(f)):
                return True
            else:
                ignore_collection[os.path.dirname(f)] = False
                return False
        elif type(ignore) == str:
            if os.path.basename(f) in ignore:
                ignore_collection[os.path.dirname(f)] = False
                return False
            else:
                return True
            
    retain_parent, current_file_ignores = (file_ignores.get("retain_parent", False), file_ignores.get("rules", [])) if type(file_ignores) == dict else (False, file_ignores or [])

    for ignore in current_file_ignores or []:
        _files = list(filter(lambda f: _check_ignore(f, ignore), _files))
    
    
        
    files = [_get_file_info(str(root), str(path)) for path in _files]
    if retain_parent:
        for f in _files:
            parent = os.path.dirname(f)
            if parent in ignore_collection:
                ignore_collection[parent] = True

        redeem_dir = [path for path, exist in ignore_collection.items() if not exist]
        for redeem in redeem_dir:
            files.append(_get_file_info(str(root), f"{redeem.rstrip('/')}/"))

    if use_cache:
        with open(cache_path, "w+") as cache_file:
            json.dump(files, cache_file)
    return files


def st_file_browser(
    path: str,
    *,
    show_preview=True,
    show_preview_top=False,
    glob_patterns=("**/*",),
    ignore_file_select_event=False,
    file_ignores=None,
    select_filetype_ignores=None,
    extentions=None,
    show_delete_file=False,
    show_choose_file=False,
    show_choose_folder=False,
    show_download_file=True,
    show_new_folder=False,
    show_upload_file=False,
    show_rename_file=False,
    show_rename_folder=False,
    limit=10000,
    artifacts_site=None,
    artifacts_download_site=None,
    key=None,
    use_cache=False,
    use_static_file_server=False,
    overide_preview_handles=None,
    static_file_server_path=None,
    sort=None,
):
    extentions = tuple(extentions) if extentions else None
    root = pathlib.Path(os.path.abspath(path))
    if use_static_file_server and static_file_server_path:
        event = render_static_file_server(
            key,
            path,
            static_file_server_path,
            show_choose_file,
            show_choose_folder,
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
        
        files = (
            [file for file in files if str(file["path"]).endswith(extentions)]
            if extentions
            else files
        )
        if show_preview and show_preview_top:
            preview = st.container()
        if not artifacts_download_site and artifacts_site:
            artifacts_download_site = artifacts_site
            
        other_params = {}
        if sort and callable(sort):
            files = sort(files)
            other_params["sort"] = None
        
        event = _component_func(
            files=files,
            show_choose_file=show_choose_file,
            show_choose_folder=show_choose_folder,
            show_download_file=show_download_file,
            show_delete_file=show_delete_file,
            show_new_folder=show_new_folder,
            show_rename_file=show_rename_file,
            show_rename_folder=show_rename_folder,
            ignore_file_select_event=ignore_file_select_event,
            artifacts_download_site=artifacts_download_site,
            artifacts_site=artifacts_site,
            key=key,
            **other_params,
        )

    if event and type(event) == dict and "type" in event:
        if event["type"] == "SELECT_FILE" and (
            (not select_filetype_ignores)
            or (
                not any(
                    event["target"]["path"].endswith(ft)
                    for ft in select_filetype_ignores
                )
            )
        ):
            file = event["target"]
            if "path" in file:
                if not os.path.exists(os.path.join(root, file["path"])):
                    st.warning(f"File {file['path']} not found")
                    return event
            if show_preview and show_preview_top:
                with preview:
                    with st.expander("", expanded=True):
                        show_file_preview(
                            str(root),
                            file,
                            artifacts_site,
                            overide_preview_handles=overide_preview_handles,
                            key=f"{key}-preview",
                        )
            elif show_preview and not show_preview_top:
                with st.expander("", expanded=True):
                    show_file_preview(
                        str(root),
                        file,
                        artifacts_site,
                        overide_preview_handles=overide_preview_handles,
                        key=f"{key}-preview",
                    )

    return event


if _DEVELOP_MODE or os.getenv("SHOW_FILE_BROWSER_DEMO"):
    current_path = os.path.dirname(os.path.abspath(__file__))
    from streamlit_antd.tabs import st_antd_tabs

    tab_event = st_antd_tabs(
        [{"Label": "Upload from local"}, {"Label": "Choose from workspace"}], key="tab"
    )
    if tab_event and tab_event["Label"] == "Choose from workspace":
        event = st_file_browser(
            os.path.join(current_path, "..", "example_artifacts"),
            artifacts_site="http://localhost:1024/artifacts/",
            artifacts_download_site="http://localhost:1024/download/artifacts/",
            show_choose_file=True,
            show_download_file=True,
            glob_patterns=("molecule/**/*",),
            key="CC",
        )
    else:
        event = st.file_uploader(key="ding", label="upload file")

    st.header("Default Options")
    def sort(files):
        return sorted(files, key=lambda x: x["size"])
    
    event = st_file_browser(
        os.path.join(current_path, "..", "example_artifacts"),
        file_ignores=("a.py", "a.txt", re.compile(".*.pdb")),
        key="A",
        show_choose_file=True,
        show_choose_folder=True,
        show_delete_file=True,
        show_download_file=True,
        show_new_folder=True,
        show_upload_file=True,
        show_rename_file=True,
        show_rename_folder=True,
        use_cache=True,
        sort=sort,
    )
    st.write(event)

    st.header("With Artifacts Server, Allow choose & download")
    event = st_file_browser(
        os.path.join(current_path, "..", "example_artifacts"),
        artifacts_site="http://localhost:1024/artifacts/",
        artifacts_download_site="http://localhost:1024/download/artifacts/",
        show_choose_file=True,
        show_download_file=True,
        key="B",
    )
    st.write(event)

    st.header("Show only molecule files")
    event = st_file_browser(
        os.path.join(current_path, "..", "example_artifacts"),
        artifacts_site="http://localhost:1024/artifacts/",
        artifacts_download_site="http://localhost:1024/download/artifacts/",
        show_choose_file=True,
        show_download_file=True,
        glob_patterns=("molecule/**/*",),
        key="C",
    )
    st.write(event)

    st.header("Show only molecule files in sub directory")
    event = st_file_browser(
        os.path.join(current_path, "..", "example_artifacts/molecule"),
        artifacts_site="http://localhost:1024/artifacts/molecule/",
        artifacts_download_site="http://localhost:1024/download/artifacts/molecule/",
        show_choose_file=True,
        show_download_file=True,
        glob_patterns=("*",),
        key="D",
    )
    st.write(event)
    
    
    import time

    st.header("Deep glob")
    start_time = time.time()
    # If you use the static file server, you must make sure
    # that the path listened to by the static file server
    # is the same as the path passed to st_file_browser by root.
    event = st_file_browser(
        os.path.join(current_path, "..", "example_artifacts/static_file_server/root"),
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

