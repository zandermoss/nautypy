#! /bin/bash
rm -rf build
python3 setup.py build_ext
pip install -r requirements.txt .
