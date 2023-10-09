#! /bin/bash
rm -rf build
python3 setup.py build
pip install -r requirements.txt .
