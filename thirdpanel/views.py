from lxml import etree

from flask import render_template, request, abort, jsonify, Response

from app import app

import feeds

AVAILABLE_FEED_LOADERS = {'asofterworld': feeds.ASofterWorldFeed,
                          'wondermark': feeds.WondermarkFeed,
                          'dinosaurcomics': feeds.DinosaurComicsFeed,
                          'xkcd': feeds.XkcdFeed
                          }

ITEM_FIELDS = frozenset(('title', 'link', 'pubDate', 'guid'))

def fetch_feed_or_404(feed_name):
    feed_loader_class = AVAILABLE_FEED_LOADERS.get(feed_name)

    if feed_loader_class is None:
        abort(404)

    feed_loader = feed_loader_class()

    return feed_loader.fetch_data()

def render_feed_as_rss(feed):
    root = etree.Element('rss', version='2.0')

    channel = etree.SubElement(root, 'channel')

    for item in feed['items']:
        xml_item = etree.SubElement(channel, 'item')

        item_keys = ITEM_FIELDS & frozenset(item.iterkeys())
        for field in item_keys:                
            element = etree.SubElement(xml_item, field)
            element.text = item[field]
            if field == 'guid':
                element.set('isPermaLink', 'false')

        desc = etree.SubElement(xml_item, 'description')

        img_tag = '<img src="%s" title="%s" />'
        desc.text =  img_tag % (item['image_url'],
                                item.get('alt_text'))

    return etree.tostring(root, 
                          xml_declaration=True, 
                          encoding="UTF-8")

@app.route('/<feed_name>/feed.json')
def feed_json(feed_name):
    feed_data = fetch_feed_or_404(feed_name)
    return jsonify(feed_data)

@app.route('/<feed_name>/rss.xml')
def feed_rss(feed_name):
    feed_data = fetch_feed_or_404(feed_name) 
    feed_str = render_feed_as_rss(feed_data)
    return Response(feed_str, mimetype='application/rss+xml')
    
