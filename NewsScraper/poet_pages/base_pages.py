import logging
from datetime import datetime
from typing import Iterable

import attr
import feedparser
import pytz
import web_poet
from web_poet.pages import WebPage

from NewsScraper.items import ArticleItem
from NewsScraper.loaders import ArticleItemLoader
from NewsScraper.providers import HttpClientEx


@attr.define
class BasePage(WebPage):
    http: HttpClientEx
    page_params: web_poet.PageParams

    logger = logging.getLogger(__name__)


@attr.define
class ArticleResultsPage(BasePage):
    def parse_articles(self) -> Iterable[ArticleItem]:
        pass


@attr.define
class ArticlePage(BasePage):
    init_item: ArticleItem

    def to_item(self) -> ArticleItem:
        pass


@attr.define
class ArticleRssPage(ArticleResultsPage):

    def filter_article(self, article: ArticleItem) -> bool:
        """
        Filters articles based on certain criteria.

        Args:
            article (ArticleItem): The article to be filtered.

        Returns:
            bool: True if the article passes the filter, False if it is filtered out.
        """
        return True

    def parse_articles(self) -> Iterable[ArticleItem]:
        for entry in feedparser.parse(self.response.text)['entries']:
            item_loader = ArticleItemLoader()

            item_loader.add_value('source_url', entry['link'])
            item_loader.add_value('title', entry['title'])
            item_loader.add_value('created_at', datetime(*entry['published_parsed'][:6], tzinfo=pytz.utc))

            for media in entry.get('media_content', []):
                if media['medium'] == 'image':
                    item_loader.add_value('featured_image', media['url'])
                    break

            item = item_loader.load_item()

            if self.filter_article(item):
                yield item
            else:
                self.logger.info(f'Filtered out article: {item["source_url"]}')
