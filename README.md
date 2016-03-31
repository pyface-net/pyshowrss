# pyshowrss #

----------

A small python script to download .torrent files from a [ShowRSS](https://new.showrss.info) feed

----------

## Requirements ##

**If running directly with python:**

- Python 2.7
- Python feedparser module
	- `pip install feedparser`
- A [ShowRSS](https://new.showrss.info) user id

**If running Windows / Ubuntu-ARM standalone (pyinstaller) version:**

- A [ShowRSS](https://new.showrss.info) user id

## Configuration ##

Read the `pyshowrss.ini` for details on how to configure pyshowrss. At a minimum you will need to replace the `user_id` field with your actual ShowRSS user id.

## Usage ##

	usage: pyshowrss [-h] [-v] [-c CONFIGFILE] [-o OUTPUTDIR]
	
	Downloads .torrent files from a ShowRSS feed
	
	optional arguments:
	  -h, --help            show this help message and exit
	  -v, --version         show program's version number and exit
	  -c CONFIGFILE, -config CONFIGFILE
	                        path to configuration file to use (default =
	                        ./pyshowrss.ini)
	  -o OUTPUTDIR, -outputDir OUTPUTDIR
	                        full path to an output directory for .torrent files
	                        (default = ./torrents)
