#!/bin/bash
cd ~/dev/Deluge-Pieces-Plugin/
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/Pieces.egg-link ~/.config/deluge/plugins
rm -fr ./temp
