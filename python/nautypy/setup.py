#! /usr/bin/python3
from setuptools import setup

setup(
    name="nautypy",
    version="1.0",
    py_modules=["nautypy"],
    setup_requires=["cffi>=1.0.0", "path"],
    install_requires=["networkx", "hashable_containers","matplotlib","pygraphviz","prettytable"],
    cffi_modules=["cffibuild_nautypy.py:ffibuilder"],
)
