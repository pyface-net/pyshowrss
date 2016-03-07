#!/usr/bin/env python
__author__ = "pyface.net"
__version__ = "0.1"
__license__ = "MIT License"

import argparse
import subprocess
import ConfigParser
import hashlib
import os.path
import urllib2
import urllib
import feedparser

def log(message):
        print message

def saveCache(cache, cache_file):
    with open(cache_file, 'w+') as outfile:
        cache.write(outfile)
        outfile.close()

def loadCreateCacheFile(cache_file):
    cache = None
    if cache_file:
        cache = ConfigParser.ConfigParser()
        cache.read(cache_file)
        try:
            cache.add_section("cache")
        except:
            pass
    return cache

def is_valid(buffer):
    return (buffer.index('d8') == 0)

def downloadTorrentFile(url, output_dir, validate):
    safe_url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
    torrent_name = safe_url.split('/')[-1]
    response = urllib2.urlopen(safe_url)
    torrent_data = response.read()

    if not validate or (validate and is_valid(torrent_data)):
        torrent_file = os.path.join(output_dir,torrent_name)
        with open(torrent_file, 'w') as outfile:
            outfile.write(torrent_data)
        return True
    else:
        return False


def processRSSFeed(url, output_dir, post_dl_cmd, validate, cache_file):
    cache = loadCreateCacheFile(cache_file)
    rss_feed = feedparser.parse(url)
    log("Checking for new shows...")
    for item in rss_feed.entries:
        title = item['title']
        id = item['id']
        cache_key = hashlib.md5(id).hexdigest()
        torrent_link = item['links'][0]['href']

        download = True
        try:
            if cache:
                cache.get("cache", cache_key)
            download = False
        except:
            pass

        if download:
            try:
                log("Downloading show: '%s' (%s)" % (title,torrent_link))
                if downloadTorrentFile(torrent_link, output_dir, validate):
                    if post_dl_cmd:
                        subprocess.check_call(post_dl_cmd.split() + [title.encode('ascii', 'ignore')] + [torrent_link])
                    if cache:
                        cache.set("cache", cache_key, "Downloaded")
                        saveCache(cache,cache_file)
                else:
                    log("Download failed: '%s' (%s)" % (title,torrent_link))
            except:
                log("Exception while downloading: '%s' (%s)" % (title,torrent_link))
    log("Done!")


def getRSSUrl(config):
    url = config.get("showrss","url")
    user_id = config.get("showrss","user_id")
    quality = config.get("showrss","quality")
    repack = config.get("showrss","repack")

    return (url % (user_id,quality,repack))


def getOptions(config):
    post_dl_cmd = None
    cache_file = None
    validate = False

    if config.has_option("default","post_dl_cmd"):
        post_dl_cmd = config.get("default","post_dl_cmd")
    if config.has_option("default","cache_file"):
        cache_file = config.get("default","cache_file")
    if config.has_option("default","validate_torrent_file"):
        validate = config.getboolean("default","validate_torrent_file")

    return (post_dl_cmd, validate, cache_file)


def _getArgs():
    DEFAULT_CONFIG_FILENAME = "pyshowrss.ini"
    program = os.path.basename(__file__)
    arg_parser = argparse.ArgumentParser(prog=program, version=__version__,
                                         description="Downloads .torrents from a showRSS feed")
    arg_parser.add_argument('-c', '-config', dest='configFile',
                            default=os.path.join(os.getcwd(),DEFAULT_CONFIG_FILENAME),
                            help="path to configuration file to use "
                                 "(default = ./" + DEFAULT_CONFIG_FILENAME)
    arg_parser.add_argument('-o', '-outputDir', dest='outputDir', default=os.getcwd(),
                            help="path to an output directory for .torrent files "
                                 "(default = ./")

    args = arg_parser.parse_args()

    if not os.path.isfile(args.configFile):
        print "ERROR: config (%s) does not exist" % args.configFile
        return None

    if not os.path.isdir(args.outputDir):
        print "ERROR: output dir (%s) does not exist" % args.outputDirs
        return None

    return args

def main():
    args = _getArgs()
    if args:
        config = ConfigParser.ConfigParser()
        config.read(args.configFile)
        (post_dl_cmd, validate, cache_file) = getOptions(config)
        url = getRSSUrl(config)
        processRSSFeed(url, args.outputDir, post_dl_cmd, validate, cache_file)

if __name__ == "__main__":
    main()