#!/bin/sh
# NOTE: this has been built for and tested on OSX Yosemite (10.10.5)
rm -R ./build
rm -R ./dist
/usr/local/bin/pyinstaller pyshowrss.py --onefile --distpath ./dist/osx -i ./icons/feed-icon.ico
cp pyshowrss.ini ./dist/osx
tar -cvzf ./installer/osx/pyshowrss.tar.gz ./dist/osx/*

