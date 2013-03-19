from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from thirdpanel.app import db

class Comic(db.Model):
    __tablename__ = 'comics'

    id = Column(Integer, primary_key=True)
    create_date = Column(DateTime, default=db.func.now())
    name = Column(String(20))
    title = Column(String(40))
    description = Column(String(200))
    url = Column(String(100))

    strips = relationship("ComicStrip", backref='comic')


class ComicStrip(db.Model):
    __tablename__ = 'comic_strips'

    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey('comics.id'))
    create_date = Column(DateTime, default=db.func.now())
    publish_date = Column(DateTime)
    title = Column(String(200))
    number = Column(Integer)
    guid = Column(String(40))
    url = Column(String(150))
    image_url = Column(String(150))
    alt_text = Column(String(800))
