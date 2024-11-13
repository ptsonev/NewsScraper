from itemloaders import ItemLoader
from itemloaders.processors import TakeFirst
from scrapy import Request
from scrapy.utils.request import fingerprint

from NewsScraper.items import ArticleItem


class ArticleItemLoader(ItemLoader):
    default_item_class = ArticleItem

    # default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    def load_item(self) -> ArticleItem:
        if source_url := self.get_output_value('source_url'):
            request_hash = fingerprint(Request(source_url)).hex()
            self.replace_value('news_hash', request_hash)

        return super().load_item()
