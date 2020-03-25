#!/bin/bash

set -e 

binary_name="smb_lock_manager" 
build_directory="dist"
mkdir -p ${build_directory}
cp smb_lock_manager.py ${build_directory}/
# Install requirements using python 2.7 until qumulo_api supports python3
pip install -r requirements.txt --system --target ${build_directory}
# Use python3 zipapp module to create an executable that it's dependencies
echo "Creating ${binary_name} binary"
python3 -m zipapp -p '/usr/bin/env python' -o ${binary_name} ${build_directory} -m "smb_lock_manager:main" 
rm -Rf ${build_directory}
