from bs4 import BeautifulSoup

def clean_string(value):
    """Returns None instead of empty strings"""
    if value is None:
        return None
    value = value.strip()
    if len(value) == 0:
        return None

    return value

def clean_int(value):
    """Returns an int or None"""
    if value is None:
        return None

    if value.isdigit():
        return int(value)

    return None

def extract_html_images(html, has_title=True):
    """Searches for images in a HTML string"""
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

        if title is None:
            title = clean_string(image_tag.get('alt'))

        image = dict(src=src,
                     title=title,
                     width=width,
                     height=height
                    )

        result.append(image)

    return result
