#! /bin/bash
meson setup build
cd build
meson compile -v
cd ../python
rm -rf build/
python3 setup.py build_ext
pip install .
