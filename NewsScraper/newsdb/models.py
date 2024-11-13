from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship, declarative_base, sessionmaker, scoped_session, Session as SessionType

Base = declarative_base()


class BaseMixin(Base):
    __abstract__ = True

    def __init__(self, **kwargs):
        super().__init__(**{k: v for k, v in kwargs.items() if hasattr(type(self), k)})

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if getattr(self, c.name)}


class Category(BaseMixin):
    __tablename__ = 'categories'

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100), unique=True, nullable=False)

    # Relationship
    sources = relationship("ScraperSource", back_populates="category")
    articles = relationship("Article", back_populates="category")


class ScraperSource(BaseMixin):
    __tablename__ = 'scraper_source'

    source_id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(2048), nullable=False)
    is_rss = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey('categories.category_id'))
    city_id = Column(Integer, ForeignKey('cities.city_id'))

    # Relationship
    category = relationship("Category", back_populates="sources")


class User(BaseMixin):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum('reader', 'journalist', 'editor', 'admin'), default='reader')
    profile_image = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    # Relationship
    articles = relationship("Article", back_populates="journalist")


class City(BaseMixin):
    __tablename__ = 'cities'

    city_id = Column(Integer, primary_key=True, autoincrement=True)
    city_name = Column(String(100), nullable=False)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False)

    # Relationship
    articles = relationship("Article", back_populates="city")


class Article(BaseMixin):
    __tablename__ = 'articles'

    article_id = Column(Integer, unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    journalist_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.category_id'), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.city_id'), nullable=False)
    created_at = Column(DateTime, nullable=True)
    status = Column(Enum('draft', 'published', 'archived'), default='draft')
    updated_at = Column(DateTime, nullable=True)
    news_hash = Column(String(40), unique=True, nullable=False, primary_key=True)
    source_url = Column(String(2048), nullable=False)

    # Relationships
    journalist = relationship("User", back_populates="articles")
    category = relationship("Category", back_populates="articles")
    city = relationship("City", back_populates="articles")
    media = relationship('Media', back_populates='articles')


class Media(BaseMixin):
    __tablename__ = 'media'

    media_id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey('articles.article_id'), nullable=False)
    media_type = Column(Enum('image', 'video', 'audio'), nullable=False)
    media_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    articles = relationship("Article", back_populates="media")


session_factory: sessionmaker = None
Session: scoped_session[SessionType] = None


def init_db(connection_string: str):
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    global session_factory, Session
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
