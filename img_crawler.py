import sys
import urllib, urllib2
import re
import os
from BeautifulSoup import BeautifulSoup


_quiet = False
URLS_FILE_NAME = 'urls.txt'
IMGS_EXTENSIONS = ['png', 'gif', 'tiff', 'bmp', 'jpg', 'jpeg']
PROTOCOLS = ['http://', 'https://', 'ftp://']

imgs_re = re.compile('.*(\.(' + "|".join(IMGS_EXTENSIONS) + '))$', re.I)
protocols_re = re.compile('^(' + "|".join(PROTOCOLS) + ").*", re.I)

def do_log(str):
    if not _quiet:
        print str

def do_crawl(url):
    # read url
    retopen = None
    try:
        retopen = urllib2.urlopen(url)
        ret = retopen.read()
        return ret
    except IOError, e:
        do_log("IOError while reading [%s] url: %s" % (url, e.message))
    finally:
        if retopen:
            retopen.close()
    return None

def do_crawl_and_save(url, filename):
    data = do_crawl(url)
    if data:
        try:
            d = os.path.dirname(filename)
            if not os.path.exists(d):
                os.makedirs(d)
            f = open(filename, 'w')
            f.write(data)
            f.close()
        except IOError, e:
            do_log("IOError while writing to file [%s]: %s" % (filename, e.message))

def get_protocol_domain(url):
    vals = url.split('://')
    protocol = vals[0]
    parts = vals[1].split('/')
    domain = parts[0]
    rest_without_name = "/".join(parts[1:-1])
    return (protocol, domain, rest_without_name)

def get_url_file_name(attr_value, url_base):
    url = None
    file_name = None
    if protocols_re.match(attr_value):
        # easy: it's a FULL URL
        url = attr_value
    else:
        protocol, domain, rest_without_name = get_protocol_domain(url_base)
        if attr_value.startswith('/'):
            # relatively easy: it's a FULL URL without protocol
            url = protocol + '://' + domain + attr_value
        else:
            # hard
            url = protocol + '://' + domain + '/' + rest_without_name + '/' + attr_value
    return (url, url.split('://')[1])

def process_tag(tag, attribute_name, url_base):
    do_log("Processing TAG: %s from [%s]" % (tag, url_base))
    for attr in tag.attrs:
        name, value = attr
        if name.lower() == attribute_name.lower():
            if imgs_re.match(value):
                url, dest_filename = get_url_file_name(value, url_base)
                do_log("Retrieving image URL [%s] and saving it into [%s]" % (url, dest_filename))
                do_crawl_and_save(url, dest_filename)


def main():

    if '-q' in sys.argv:
        _quiet = True

    for url in open(URLS_FILE_NAME):
        url = url.strip()
        if url and protocols_re.match(url):
            do_log("Processing URL [%s]" % (url))
            html = do_crawl(url)
            if html:
                do_log("HTML read complete for [%s] with %d characters" % (url, len(html)))
                soup = BeautifulSoup(html)
                anchors = soup.findAll('a')
                for anchor in anchors:
                    process_tag(anchor, 'href', url)
                imgs = soup.findAll('img')
                for img in imgs:
                    process_tag(img, 'src', url)
            else:
                do_log("Could not read HTML from [%s]" % (url))
                
if __name__ == "__main__":
    main()
