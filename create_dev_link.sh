#!/bin/bash
cd /home/nick/projs/deluge_pieces/pieces
mkdir temp
export PYTHONPATH=./temp
python setup.py build develop --install-dir ./temp
cp ./temp/Pieces.egg-link /home/nick/.config/deluge/plugins
rm -fr ./temp
