#! /bin/bash
printf "\n==================[Building libnautypy]=================\n"
meson setup build
cd build
meson compile -v
cd ..
printf "\n=============[Building hashable_containers]=============\n"
cd python/hashable_containers
python3 setup.py build
printf "\n============[Installing hashable_containers]============\n"
pip install -r requirements.txt .
cd ../
printf "\n===================[Building nautypy]===================\n"
cd nautypy
rm -rf build/
python3 setup.py build_ext
printf "\n==================[Installing nautypy]==================\n"
pip install -r requirements.txt .
cd ../..
printf "\n====================[Building Docs]=====================\n"
cd docs
make html
cd ..
