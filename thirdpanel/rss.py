import xml.sax
import cStringIO

ROOT_TAGS = ('title', 'link', 'description', 'language')

class RssHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.items = []
        self.channel_tags = {}

        self._cur_content = None
        self._cur_item = None        
        self._in_root_tag = False

    def startElement(self, name, attrs):
        if name == 'item':
            self._cur_item = dict()
            self.items.append(self._cur_item)

        
        if self._cur_item is None:
            # above an item tag
            if name in ROOT_TAGS:
                self._cur_content = cStringIO.StringIO()
                self._in_root_tag = True
        else:
            # inside an item tag
            self._cur_content = cStringIO.StringIO()


    def endElement(self, name):
        content = None
        if self._cur_content is not None:            
            content = self._cur_content.getvalue()
            self._cur_content.close()

            if len(content) == 0:
                content = None

            if self._in_root_tag:
                self.channel_tags[name] = content

            if self._cur_item is not None:
                self._cur_item[name] = content

        # reset variables
        self._cur_content = None
        if name == 'item':
            self._cur_item = None
        self._in_root_tag = False


    def characters(self, content):
        if self._cur_content is not None:
            self._cur_content.write(content.encode('utf8'))

def parse_rss_feed(feed_content):
    handler = RssHandler()
    xml.sax.parseString(str(feed_content), handler=handler)

    result = dict(items=handler.items)
    result.update(handler.channel_tags)

    return result
