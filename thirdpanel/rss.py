import xml.sax
import cStringIO

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