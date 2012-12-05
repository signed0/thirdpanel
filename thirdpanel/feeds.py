import requests

from bs4 import BeautifulSoup

from rss import parse_rss_feed

def clean_string(value):
    '''Returns None instead of empty strings'''

    if value is None:
        return None
    value = value.strip()
    if len(value) == 0:
        return None

    return value

def clean_int(value):
    '''Returns an int or None'''

    if value is None:
        return None

    if value.isdigit():
        return int(value)

    return None

def extract_images(html, has_title=True):
    result = []

    soup = BeautifulSoup(html)
    for image_tag in soup.findAll('img'): 
        src = clean_string(image_tag.get('src'))
        if src is None:
            continue

        title = clean_string(image_tag.get('title'))        
        if title is None and has_title is True:
            # filter out images without titles
            continue

        width = clean_int(image_tag.get('width'))
        height = clean_int(image_tag.get('height'))        

        if width is None or height is None:
            width = None
            height = None

        image = dict(src=src,
                     title=title,
                     alt=clean_string(image_tag.get('alt')),
                     width=width,
                     height=height
                    )

        result.append(image)

    return result

class ComicFeed(object):

    rss_url = None

    def fetch_data(self):
        r = requests.get(self.rss_url)
        feed = parse_rss_feed(r.content)

        items = []
        for item in feed['items']:
            item = self._clean_item(item)
            if item is not None:
                items.append(item)

        feed['items'] = items

        return feed

    def _clean_item(self, item):
        return item

def add_description_image(item, has_title=False):        
    '''Attemps to correct image in the description'''

    raw_images = extract_images(item['description'], has_title=has_title)

    if len(raw_images) == 0:
        return None
    first_image = raw_images[0]

    item['image_url'] = first_image['src']
    item['alt_text'] = first_image['title']

    del item['description']

    return item

class ASofterWorldFeed(ComicFeed):
    '''Uses RSSPECT'''

    rss_url = "http://www.rsspect.com/rss/asw.xml"

    def _clean_item(self, item):
        item = add_description_image(item, has_title=True)
        if item is None:
            return None

        # add the commic number to the title
        comic_id = item['link'].rsplit('=', 1)[-1]
        item['title'] = "#%s" % comic_id

        return item

class WondermarkFeed(ComicFeed):
    '''Uses Feedburner'''

    rss_url = "http://feeds.feedburner.com/wondermark"

    def _clean_item(self, item):
        return add_description_image(item, has_title=True)

class DinosaurComicsFeed(ComicFeed):
    '''Uses RSSPECT'''

    rss_url = "http://www.rsspect.com/rss/qwantz.xml"

    def _clean_item(self, item):
        soup = BeautifulSoup(item['description'])
        comic = soup.find('img', {'class': 'comic'})

        item['image_url'] = comic['src']
        item['alt_text'] = comic['title']

        del item['description']

        return item

class XkcdFeed(ComicFeed):

    rss_url = "http://xkcd.com/rss.xml"

    def _clean_item(self, item):
        return add_description_image(item, has_title=False)

class DilbertFeed(ComicFeed):
    '''Uses Feedburner'''

    rss_url = "http://feed.dilbert.com/dilbert/daily_strip"

    def _clean_item(self, item):
        return add_description_image(item, has_title=False)

class SmbcFeed(ComicFeed):

    rss_url = "http://feeds.feedburner.com/smbc-comics/PvLb"

    def _clean_item(self, item):
        return add_description_image(item, has_title=False)
