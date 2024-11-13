# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ArticleItem(scrapy.Item):
    title = scrapy.Field()
    created_at_timestamp = scrapy.Field()
    source_url = scrapy.Field()
    content = scrapy.Field()
    slug = scrapy.Field()
    journalist_id = scrapy.Field()
    category_id = scrapy.Field()
    city_id = scrapy.Field()
    featured_image = scrapy.Field()

    news_hash = scrapy.Field()
