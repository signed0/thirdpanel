import datetime
from datetime import timedelta
from lxml import etree
from xml.sax.saxutils import quoteattr

from flask import render_template, request, abort, jsonify, Response

from thirdpanel.app import app, db
from thirdpanel.models import Comic, ComicStrip

ITEMS_PER_PAGE = 3

def get_comic_or_404(comic_name):
    comic = db.session.query(Comic).filter(Comic.name==comic_name).first()
    if comic is None:
        abort(404)
    return comic

def get_latest_comic_strips(comic_id, quantity=ITEMS_PER_PAGE):
    comic_strips = db.session \
        .query(ComicStrip )\
        .filter(ComicStrip.comic_id==comic_id) \
        .order_by(ComicStrip.publish_date.desc()) \
        .limit(quantity) \
        .all()
    return comic_strips

def render_feed_as_rss(comic, comic_strips):
    root = etree.Element('rss', version='2.0')

    channel = etree.SubElement(root, 'channel')

    etree.SubElement(channel, 'link').text = comic.url
    etree.SubElement(channel, 'description').text = comic.description
    etree.SubElement(channel, 'title').text = comic.title
    etree.SubElement(channel, 'language').text = 'en-us'

    for item in comic_strips:
        xml_item = etree.SubElement(channel, 'item')

        title = item.title if item.title else '#%i' % item.number

        etree.SubElement(xml_item, 'title').text = title
        etree.SubElement(xml_item, 'link').text = item.url
        pub_date = item.publish_date.strftime("%a, %d %b %Y %H:%M:%S -0000")
        etree.SubElement(xml_item, 'pubDate').text = pub_date

        guid = etree.SubElement(xml_item, 'guid', isPermaLink='false')
        guid.text = item.guid

        desc = etree.SubElement(xml_item, 'description')

        # the alt_text will include the proper surrounding quotations
        alt_text = '""' if item.alt_text is None else quoteattr(item.alt_text)
        img_tag = '<img src="%s" title=%s />'
        desc.text =  img_tag % (item.image_url, alt_text)

    return etree.tostring(root,
                          xml_declaration=True,
                          encoding="UTF-8")

@app.route('/')
def index():
    comics = db.session.query(Comic).all()

    yesterday = datetime.datetime.utcnow() - timedelta(days=1)

    comic_strips = db.session \
        .query(ComicStrip) \
        .filter(ComicStrip.publish_date > yesterday) \
        .order_by(ComicStrip.publish_date.desc()) \
        .all()

    return render_template('index.jinja2',
        comics=comics,
        comic_strips=comic_strips)

@app.route('/<comic_name>')
@app.route('/<comic_name>/')
def comic_home(comic_name):
    comic = get_comic_or_404(comic_name)
    comic_strips = get_latest_comic_strips(comic.id)

    return render_template('comic_index.jinja2',
        comic=comic,
        comic_strips=comic_strips)

@app.route('/<comic_name>/feed.json')
def feed_json(comic_name):
    comic = get_comic_or_404(comic_name)
    comic_strips = get_latest_comic_strips(comic.id)

    response = dict(title=comic.title,
                    description=comic.description,
                    url=comic.url,
                    name=comic.name,
                    items=[]
                    )

    for comic_strip in comic_strips:
        item = dict(title=comic_strip.title,
                    number=comic_strip.number,
                    url=comic_strip.url,
                    image_url=comic_strip.image_url,
                    publish_date=comic_strip.publish_date.isoformat(),
                    alt_text=comic_strip.alt_text
                    )
        response['items'].append(item)

    return jsonify(response)

@app.route('/<comic_name>/rss.xml')
def feed_rss(comic_name):
    comic = get_comic_or_404(comic_name)
    comic_strips = get_latest_comic_strips(comic.id)

    feed_str = render_feed_as_rss(comic, comic_strips)
    return Response(feed_str, content_type='application/rss+xml')
