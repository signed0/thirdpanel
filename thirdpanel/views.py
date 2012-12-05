from lxml import etree

from flask import render_template, request, abort, jsonify, Response

from app import app

import feeds

AVAILABLE_FEED_LOADERS = {'asofterworld': feeds.ASofterWorldFeed }

EXTENSIONS = ['xml', 'json']

item_fields = frozenset(('title', 'link', 'pubDate', 'guid'))

def render_feed_as_rss(feed):
    root = etree.Element('rss', version='2.0')

    channel = etree.SubElement(root, 'channel')

    for item in feed['items']:
        xml_item = etree.SubElement(channel, 'item')

        item_keys = item_fields & frozenset(item.iterkeys())
        for field in item_keys:                
            element = etree.SubElement(xml_item, field)
            element.text = item[field]
            if field == 'guid':
                element.set('isPermaLink', 'false')

        desc = etree.SubElement(xml_item, 'description')
        desc.text = '<img src="%s" title="%s" />' % (item['image_url'],
                                                     item.get('alt_text'))

    return etree.tostring(root, 
                          xml_declaration=True, 
                          encoding="UTF-8")

@app.route('/<feed_name>/feed.<extension>')
def index(feed_name, extension):

    feed_loader_class = AVAILABLE_FEED_LOADERS.get(feed_name)

    if feed_loader_class is None or extension not in EXTENSIONS:
        abort(404)

    feed_loader = feed_loader_class()

    feed_data = feed_loader.fetch_feed() 

    if extension == 'json':
        return jsonify(feed_data)
    elif extension == 'xml':
        feed_str = render_feed_as_rss(feed_data)
        return Response(feed_str, mimetype='application/rss+xml')

    
    return 'hello'