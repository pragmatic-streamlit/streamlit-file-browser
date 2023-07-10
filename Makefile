build:
	cd streamlit_file_browser/frontend && npm run build && cd ../..
	python setup.py sdist
run:
	DEVELOP_MODE=True streamlit run streamlit_file_browser/__init__.py
