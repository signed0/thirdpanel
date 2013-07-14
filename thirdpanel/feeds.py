from datetime import datetime
import hashlib
import rfc822
import re

import requests
import pytz
from bs4 import BeautifulSoup

from thirdpanel.rss import parse_rss_feed
from thirdpanel.util import extract_html_images


class ComicFeed(object):
    rss_url = None
    image_has_alt_text = True

    def _fetch_rss_feed(self):
        """Fetches the RSS XML from the webserver"""
        r = requests.get(self.rss_url)
        return r.content

    def _iter_current_items(self, min_publish_date=None, exclude_guids=()):
        """Iterate over current strips"""
        feed_xml = self._fetch_rss_feed()
        feed = parse_rss_feed(feed_xml)

        for item in feed['items']:
            if not self._item_is_comic(item):
                continue

            publish_date = self._item_publish_date(item)

            if min_publish_date and publish_date < min_publish_date:
                continue

            guid = hashlib.sha1(self._item_guid(item)).hexdigest()

            if guid in exclude_guids:
                continue

            image = self._item_image(item)
            if image is None:
                values = (self.name, self._item_number(item))
                raise Exception("[%s] Unable to find image for %s" % values)

            strip = dict(publish_date=publish_date,
                         url=self._item_url(item),
                         image_url=image['src'],
                         guid=guid,
                         title=self._item_title(item),
                         alt_text=image.get('title'),
                         number=self._item_number(item)
                         )
            yield strip

    def fetch_items(self, min_publish_date=None, exclude_guids=()):
        """Fetches the current RSS feed and returns one or more items"""
        strips = self._iter_current_items(min_publish_date, exclude_guids)
        return tuple(strips)

    def _item_is_comic(self, item):
        """Determines whether or not the RSS item is actually a comic

        This allows certain items to be ignored such as text only items.

        """
        return True

    def _item_title(self, item):
        return item['title']

    def _item_publish_date(self, item):
        """Returns the UTC date that the comic strip was published

        Converts a RFC822 string to a UTC datetime.

        """
        parts = rfc822.parsedate_tz(item['pubDate'])
        timestamp = rfc822.mktime_tz(parts)
        return datetime.fromtimestamp(timestamp, pytz.utc)

    def _item_publish_date_tz(self, item):
        """Returns the date that the comic strip was published.

        The original timezone is preserved.

        """
        parts = rfc822.parsedate_tz(item['pubDate'])
        timestamp = rfc822.mktime_tz(parts)
        return datetime.fromtimestamp(timestamp)

    def _item_image(self, item):
        """Returns the image for the comic strip or None

        The correct image is usually found somewhere in the description HTML.
        On occasion the description is just the image URL.

        """
        raw_images = extract_html_images(html=item['description'],
                                         has_title=self.image_has_alt_text)

        if len(raw_images) == 0:
            return None
        return raw_images[0]

    def _item_guid(self, item):
        return '%s-%s' % (self.name, self._item_number(item))

    def _item_url(self, item):
        return item['link']

    def _item_number(self, item):
        raise NotImplementedError()


class ASofterWorldFeed(ComicFeed):
    # Uses RSSPECT
    name = 'asofterworld'
    rss_url = 'http://www.rsspect.com/rss/asw.xml'

    def _item_is_comic(self, item):
        # Exclude I Blame The Sea items
        if 'iblamethesea' in item['link']:
            return False

        return (item['title'] == "A Softer World")

    def _item_title(self, item):
        return None

    def _item_number(self, item):
        return int(item['link'].rsplit('=', 1)[-1])


class WondermarkFeed(ComicFeed):
    # Uses Feedburner
    name = 'wondermark'
    rss_url = 'http://feeds.feedburner.com/wondermark'

    def _item_is_comic(self, item):
        return ';' in item['title'] and '#' in item['title']

    def _item_number(self, item):
        number, _ = item['title'].split(';', 1)
        return int(number.lstrip('#'))

    def _item_title(self, item):
        _, title = item['title'].split(';', 1)
        return title.strip()

    def _item_url(self, item):
        return 'http://wondermark.com/%i/' % self._item_number(item)


class DinosaurComicsFeed(ComicFeed):
    # Uses RSSPECT
    name = 'dinosaurcomics'
    rss_url = 'http://www.rsspect.com/rss/qwantz.xml'

    def _item_image(self, item):
        soup = BeautifulSoup(item['description'])
        comic = soup.find('img', {'class': 'comic'})

        return dict(src=comic['src'], title=comic['title'])

    def _item_number(self, item):
        # http://www.qwantz.com/index.php?comic=<number>
        return int(item['link'].rsplit('=', 1)[-1])


class XkcdFeed(ComicFeed):
    name = 'xkcd'
    rss_url = 'http://xkcd.com/rss.xml'
    image_has_alt_text = False

    def _item_number(self, item):
        # http://xkcd.com/<number>/
        return int(item['link'].rstrip('/').split('/')[-1])


class SmbcFeed(ComicFeed):
    name = 'smbc'
    rss_url = 'http://feeds.feedburner.com/smbc-comics/PvLb'
    image_has_alt_text = False

    def _item_url(self, item):
        return item['feedburner:origLink']

    def _item_number(self, item):
        # http://www.smbc-comics.com/index.php?db=comics&id=<number>
        return int(self._item_url(item).rsplit('=', 1)[-1])


class CyanideHappinessFeed(ComicFeed):
    # Feedburner
    name = 'cyanide'
    rss_url = 'http://feeds.feedburner.com/Explosm'
    image_has_alt_text = False

    def _item_is_comic(self, item):
        return (item['description'] == 'New Cyanide and Happiness Comic.')

    def _item_image(self, item):
        url = self._item_url(item)
        r = requests.get(url)
        soup = BeautifulSoup(r.text)

        content = soup.find('div', id='maincontent')
        image_elm = content.find('img', alt='Cyanide and Happiness, a daily webcomic')
        image_src = image_elm['src']
        return dict(src=image_src)

    def _item_number(self, item):
        # http://www.explosm.net/comics/<number>/
        match = re.search(r'comics/(\d+)', item['guid'])
        return match.groups()[0]


class CtrlAltDeleteFeed(ComicFeed):
    name = 'ctrlaltdel'
    rss_url = 'http://cdn.cad-comic.com/rss.xml'

    def _item_title(self, item):
        return item['title'].split(':', 1)[-1].strip()

    def _item_is_comic(self, item):
        return item['guid'].startswith('Ctrl+Alt+Del')

    def _item_image(self, item):
        url = self._item_url(item)
        r = requests.get(url)
        soup = BeautifulSoup(r.text)

        content = soup.find('div', id='content')
        image = extract_html_images(str(content))[0]
        del image['title']
        return image

    def _item_number(self, item):
        return int(item['guid'].lstrip('Ctrl+Alt+Del'))


class ToothpasteForDinnerFeed(ComicFeed):
    name = 'toothpastefordinner'
    rss_url = 'http://toothpastefordinner.com/rss/rss.php'

    def _fetch_rss_feed(self):
        # The server seems to hate it if the user agent is not provided and
        # it displays a completly different website
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(self.rss_url, headers=headers)
        return r.text

    def _item_number(self, item):
        # http://toothpastefordinner.com/index.php?x=<number>
        match = re.search(r'x=(\d+)', item['guid'])
        return match.groups()[0]

    def _item_image(self, item):
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(self._item_url(item), headers=headers)
        soup = BeautifulSoup(r.text)

        title_guess = self._item_title(item).replace(' ', '-')
        date_guess = self._item_publish_date_tz(item).date()

        url_regex = r'http://www.toothpastefordinner.com/(\d+)/(.+).gif'
        url_regex = re.compile(url_regex)
        for image in soup.find_all('img', {'class': 'comic'}):
            date_str, title = url_regex.match(image['src']).groups()
            image_date = datetime.strptime(date_str, '%m%d%y').date()

            if title == title_guess or date_guess == image_date:
                image_url = image['src']
                break
        else:
            raise Exception("Unable to find feed image.")

        return dict(src=image_url)


class MarriedToTheSeaFeed(ComicFeed):
    name = 'marriedtothesea'
    rss_url = 'http://www.marriedtothesea.com/rss/rss.php'

    def _fetch_rss_feed(self):
        # The server seems to hate it if the user agent is not provided and
        # it displays a completly different website
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(self.rss_url, headers=headers)
        return r.text

    def _item_url(self, item):
        # item['link'] does not contain the correct URL
        soup = BeautifulSoup(item['description'])
        link = soup.find('a')
        return link['href']

    def _item_number(self, item):
        # http://marriedtothesea.com/index.php?x=<number>
        match = re.search(r'x=(\d+)', item['guid'])
        return match.groups()[0]

    def _item_image(self, item):
        url = self._item_url(item)
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text)

        content = soup.find('div', id='butts')
        image_elm = content.find('img')
        image_src = image_elm['src']
        return dict(src=image_src)


ALL_FEEDS = [ASofterWorldFeed,
             WondermarkFeed,
             DinosaurComicsFeed,
             XkcdFeed,
             SmbcFeed,
             CyanideHappinessFeed,
             CtrlAltDeleteFeed,
             ToothpasteForDinnerFeed,
             MarriedToTheSeaFeed]


def get_feed_by_name(feed_name):
    for feed in ALL_FEEDS:
        if feed.name == feed_name:
            return feed()
