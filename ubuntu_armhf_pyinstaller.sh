#!/bin/sh
# NOTE: this has been built for and testing on Ubuntu Mate 15.10 (Wily) for Raspberry PI 2/3 (armhf)
rm -R ./build
rm -R ./dist
~/.local/bin/pyinstaller pyshowrss.py --onefile --distpath ./dist/ubuntu/armhf -i ./icons/feed-icon.ico
cp pyshowrss.ini ./dist/ubuntu/armhf
tar -cvzf ./installer/ubuntu/armhf/pyshowrss.tar.gz ./dist/ubuntu/armhf/*

