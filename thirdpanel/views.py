from lxml import etree
from xml.sax.saxutils import quoteattr

from flask import render_template, request, abort, jsonify, Response

from app import app

import feeds

AVAILABLE_FEED_LOADERS = {'asofterworld': feeds.ASofterWorldFeed,
                          'wondermark': feeds.WondermarkFeed,
                          'dinosaurcomics': feeds.DinosaurComicsFeed,
                          'xkcd': feeds.XkcdFeed,
                          'dilbert': feeds.DilbertFeed,
                          'smbc': feeds.SmbcFeed
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

    for key, value in feed.iteritems():
        if key != 'items':
            etree.SubElement(channel, key).text = value

    for item in feed['items']:
        xml_item = etree.SubElement(channel, 'item')

        item_keys = ITEM_FIELDS & frozenset(item.iterkeys())
        for field in item_keys:                
            element = etree.SubElement(xml_item, field)
            element.text = item[field]
            if field == 'guid':
                element.set('isPermaLink', 'false')

        desc = etree.SubElement(xml_item, 'description')

        alt_text = item.get('alt_text')
        if alt_text is None:
            alt_text = ''
        else:
            alt_text = quoteattr(alt_text)

        img_tag = '<img src="%s" title=%s />'
        desc.text =  img_tag % (item['image_url'], alt_text)

    return etree.tostring(root, 
                          xml_declaration=True, 
                          encoding="UTF-8")

@app.route('/<comic_name>')
@app.route('/<comic_name>/')
def comic_home(comic_name):
    comic_data = fetch_feed_or_404(comic_name)
    return render_template('comic_index.jinja2', comic=comic_data)

@app.route('/<comic_name>/feed.json')
def feed_json(comic_name):
    feed_data = fetch_feed_or_404(comic_name)
    return jsonify(feed_data)

@app.route('/<comic_name>/rss.xml')
def feed_rss(comic_name):
    feed_data = fetch_feed_or_404(comic_name) 
    feed_str = render_feed_as_rss(feed_data)
    return Response(feed_str, content_type='application/rss+xml')
