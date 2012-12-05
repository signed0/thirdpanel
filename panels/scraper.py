import requests
import xml.sax
import cStringIO
from bs4 import BeautifulSoup

comic = dict(title="A Softer World",
             rss_url="http://www.rsspect.com/rss/asw.xml")

class RssHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.items = []

        self._cur_content = None
        self._cur_item = None

    def startElement(self, name, attrs):
        if name == 'item':
            self._cur_item = dict()
            self.items.append(self._cur_item)

        if self._cur_item is not None:
            self._cur_content = cStringIO.StringIO()


    def endElement(self, name):
        content = None
        if self._cur_content is not None:            
            content = self._cur_content.getvalue()
            self._cur_content.close()

            if len(content) == 0:
                content = None

            if self._cur_item is not None:
                self._cur_item[name] = content

        self._cur_content = None
        if name == 'item':
            self._cur_item = None


    def characters(self, content):
        if self._cur_content is not None:
            self._cur_content.write(content)

def parse_rss_feed(feed_content):

    handler = RssHandler()
    xml.sax.parseString(feed_content, handler=handler)

    return dict(items=handler.items)

def clean_asw_items(items):
    for item in items:
        soup = BeautifulSoup(item['description'])
        for image in soup.findAll('img'): 
            alt_text = image.get('title')       
            if alt_text is not None:
                item['image_url'] = image['src']
                item['alt_text'] = alt_text
                break

        comic_id = item['link'].rsplit('=', 1)[-1]
        item['title'] = "%s %s" % (item['title'], comic_id)

        del item['description']

def fetch_updates(rss_url):
    r = requests.get(rss_url)

    feed = parse_rss_feed(r.content)
    items = feed['items']
    clean_asw_items(items)
    for item in items:
        print item


if __name__ == '__main__':
    fetch_updates(comic['rss_url'])
