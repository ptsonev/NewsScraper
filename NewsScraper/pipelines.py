# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import importlib.resources as pkg_resources
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from sqlalchemy.exc import SQLAlchemyError
from twisted.internet.threads import deferToThread

import NewsScraper.newsdb.models as models
from NewsScraper.spiders.base_spider import BaseNewsSpider
from NewsScraper.utils import get_domain


class DefaultPipeline:

    def __init__(self):
        remove_references_data = pkg_resources.read_text('NewsScraper.resources', 'remove_references.json')
        self.remove_references_re = defaultdict(list)
        for domain, references in json.loads(remove_references_data).items():
            for reference in references:
                compiled_reference_regex = re.compile(rf'\b{re.escape(reference)}\b', re.IGNORECASE)
                self.remove_references_re[domain].append(compiled_reference_regex)

    async def process_item(self, item, spider):
        item_adapter = ItemAdapter(item)

        if not item_adapter.get('content'):
            raise DropItem()

        if not item_adapter.get('slug'):
            path = urlparse(item_adapter['source_url']).path
            source_slug = path.rpartition('/')[2].partition('.')[0]
            item_adapter['slug'] = f'{source_slug}-{item_adapter["created_at"]}'

        content_bs = BeautifulSoup(item_adapter['content'], 'html.parser')

        if not item_adapter.get('featured_image') and (img := content_bs.find('img')):
            item_adapter['featured_image'] = img['src']

        root_domain = get_domain(item_adapter['source_url'])
        for href in content_bs.find_all('a'):
            href_domain = get_domain(href['href'])
            if not href_domain or href_domain == root_domain:
                href.replace_with(href.text)

        for reference_re in self.remove_references_re.get(root_domain) or []:
            for _string in list(content_bs.strings):  # type: NavigableString
                if reference_re.search(_string):
                    _string.replace_with('')

        item_adapter['content'] = str(content_bs)

        return item


class MySQLPipeline:

    def process_item(self, item, spider: BaseNewsSpider):
        return deferToThread(self._process_item, item, spider)

    def _process_item(self, item, spider: BaseNewsSpider):
        with models.Session() as session:
            try:
                article_item = models.Article(**item)
                article_item.content = article_item.content[0:65535]
                article_item.created_at = datetime.fromtimestamp(article_item.created_at, timezone.utc)

                article_item = session.merge(article_item)
                session.commit()

                if (featured_image_url := item.get('featured_image')) \
                        and not session.query(models.Media).filter_by(article_id=article_item.article_id).first():
                    media_item = models.Media(
                        article_id=article_item.article_id,
                        media_url=featured_image_url,
                        media_type='image'
                    )
                    session.merge(media_item)
                    session.commit()

            except SQLAlchemyError:
                session.rollback()
                raise

        return item
