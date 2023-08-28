import setuptools

setuptools.setup(
    name="streamlit-file-browser",
    version="3.2.3",
    author="",
    author_email="",
    description="",
    long_description="",
    long_description_content_type="text/plain",
    url="",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[],
    python_requires=">=3.6",
    install_requires=[
        "pandas",
        "filetype",
        "binaryornot",
        "wcmatch",
        "streamlit-molstar >= 0.4.4",
        "streamlit-antd",
        "streamlit-embeded",
        "streamlit >= 0.63",
        "pymatgen",
    ],
)
