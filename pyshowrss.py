#!/usr/bin/env python
import argparse
import subprocess
import ConfigParser
import hashlib
import os.path
import urllib2
import urllib
import feedparser
import traceback
import logging
import libtorrent
import time
import tempfile

__author__ = "pyface.net"
__version__ = "0.3"
__license__ = "MIT License"


def log_exception(message):
    try:
        logging.error(message)
        with open("exceptions.log", 'a') as outfile:
            outfile.write(message + "\n")
            outfile.write(traceback.format_exc())
    except:
        pass


def save_cache(cache, cache_file):
    with open(cache_file, 'w+') as outfile:
        cache.write(outfile)
        outfile.close()


def load_create_cache_file(cache_file):
    cache = None
    if cache_file:
        cache = ConfigParser.ConfigParser()
        cache.read(cache_file)
        try:
            cache.add_section("cache")
        except:
            pass
    return cache

# ..very very poor validation...
def is_valid(buffer):
    try:
        if buffer.index('d8') == 0:
            return True
    except:
        pass
    try:
        if buffer.index('d13') == 0:
            return True
    except:
        pass
    return False

def get_torrent_via_magnet(url):
    try:
        session = libtorrent.session()
        tempdir = tempfile.mkdtemp()
        params = {
            'save_path': tempdir,
            'storage_mode': libtorrent.storage_mode_t(2),
            'paused': False,
            'auto_managed': True,
            'duplicate_is_error': True
        }
        handle = libtorrent.add_magnet_uri(session, url, params)
        while (not handle.has_metadata()):
            time.sleep(.1)

        session.pause()
        torinfo = handle.get_torrent_info()

        fs = libtorrent.file_storage()
        for file in torinfo.files():
            fs.add_file(file)
        torfile = libtorrent.create_torrent(fs)
        torfile.set_comment(torinfo.comment())
        torfile.set_creator(torinfo.creator())
        torrent_data = libtorrent.bencode(torfile.generate())
        session.remove_torrent(handle)
        return torrent_data
    except:
        torrent_data = None

    if handle and session:
        session.remove_torrent(handle)

    return torrent_data


def download_torrent_file(url, magnet_link, output_dir, validate):
    torrent_data = None
    torrent_name = None
    if magnet_link:
        torrent_name = url.split(':')[3].split('&')[0] + ".torrent"
        torrent_data = get_torrent_via_magnet(url)
    else:
        safe_url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")
        torrent_name = safe_url.split('/')[-1]
        response = urllib2.urlopen(safe_url)
        torrent_data = response.read()
    if not torrent_data or not torrent_name:
        return False
    elif not validate or (validate and is_valid(torrent_data)):
        torrent_file = os.path.join(output_dir, torrent_name)
        with open(torrent_file, 'wb') as outfile:
            outfile.write(torrent_data)
        return True
    else:
        return False


def process_rss_feed(url, output_dir, post_dl_cmd, validate, magnet_link, cache_file):
    cache = load_create_cache_file(cache_file)
    rss_feed = feedparser.parse(url)
    logging.info("Checking for new shows...")
    for item in rss_feed.entries:
        title = item['title'].encode('ascii', 'ignore')
        id = item['id']
        cache_key = hashlib.md5(id).hexdigest()
        torrent_link = item['links'][0]['href']

        download = True
        try:
            if cache:
                cache.get("cache", cache_key)
            logging.info("Show already in cache: '%s'" % title)
            download = False
        except:
            pass

        if download:
            try:
                logging.info("Downloading show: '%s' (%s)" % (title, torrent_link))
                if download_torrent_file(torrent_link, magnet_link, output_dir, validate):
                    if post_dl_cmd:
                        subprocess.check_call(post_dl_cmd.split() + [title] + [torrent_link])
                    if cache:
                        cache.set("cache", cache_key, "True")
                        save_cache(cache, cache_file)
                else:
                    logging.warning("Download failed: '%s' (%s)" % (title, torrent_link))
            except:
                log_exception("Exception while downloading: '%s' (%s)" % (title, torrent_link))
    logging.info("Done!")


def get_rss_url(config):
    url = config.get("showrss", "url")
    user_id = config.get("showrss", "user_id")
    quality = config.get("showrss", "quality")
    repack = config.get("showrss", "repack")
    magnets = config.get("showrss", "magnets")

    return (url % (user_id, magnets, quality, repack))


def get_options(config):
    post_dl_cmd = None
    cache_file = None
    validate = False
    magnets = False

    if config.has_option("default", "post_dl_cmd"):
        post_dl_cmd = config.get("default", "post_dl_cmd")
    if config.has_option("default", "cache_file"):
        cache_file = config.get("default", "cache_file")
    if config.has_option("default", "validate_torrent_file"):
        validate = config.getboolean("default", "validate_torrent_file")
    if config.has_option("showrss", "magnets"):
        magnets = config.getboolean("showrss", "magnets")

    return (post_dl_cmd, validate, cache_file, magnets)


def get_args():
    default_config_file = "pyshowrss.ini"
    program = os.path.basename(__file__).split('.')[0]
    arg_parser = argparse.ArgumentParser(prog=program, version=__version__,
                                         description="Downloads .torrent files from a ShowRSS feed")
    arg_parser.add_argument('-c', '-config', dest='configFile',
                            default=os.path.join(os.getcwd(), default_config_file),
                            help="path to configuration file to use "
                            "(default = ./" + default_config_file + ")")
    arg_parser.add_argument('-o', '-outputDir', dest='outputDir',
                            default=os.path.join(os.getcwd(), "torrents"),
                            help="full path to an output directory for .torrent files "
                            "(default = ./torrents)")

    args = arg_parser.parse_args()

    if not os.path.isfile(args.configFile):
        logging.error("config (%s) does not exist" % args.configFile)
        return None

    if not os.path.isdir(args.outputDir):
        logging.warning("output dir (%s) does not exist... creating it.." % args.outputDir)
        os.makedirs(args.outputDir)

    return args


def main():
    logging.basicConfig(filename='pyshowrss.log',
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S',
                        level=logging.DEBUG)
    args = get_args()
    if args:
        config = ConfigParser.ConfigParser()
        config.read(args.configFile)
        (post_dl_cmd, validate, cache_file, magnet_link) = get_options(config)
        url = get_rss_url(config)
        process_rss_feed(url, args.outputDir, post_dl_cmd, validate, magnet_link, cache_file)

if __name__ == "__main__":
    main()
