build:
	cd streamlit_file_browser/frontend && npm run build && cd ../..
	python setup.py sdist