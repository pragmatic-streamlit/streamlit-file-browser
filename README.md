# Streamlit file browser

A streamlit component serve as web file browser from local directory.

## Install

```
pip install streamlit-file-browser
```
## Usage


```python
import streamlit as st
from streamlit_file_browser import st_file_browser

st.header('Default Options')
event = st_file_browser("example_artifacts", key='A')
st.write(event)

st.header('With Artifacts Server, Allow choose file, disable download')
event = st_file_browser("example_artifacts", artifacts_site="http://localhost:1024", show_choose_file=True, show_download_file=False, key='B')
st.write(event)

st.header('Show only molecule files')
event = st_file_browser("example_artifacts", artifacts_site="http://localhost:1024", show_choose_file=True, show_download_file=False, glob_patterns=('molecule/*',), key='C')
st.write(event)
```