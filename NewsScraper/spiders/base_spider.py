from typing import Iterable, Any

import scrapy
from scrapy import Request
from scrapy.http import Response
from scrapy.utils.defer import maybe_deferred_to_future
from web_poet import ApplyRule
import sqlalchemy

import NewsScraper.newsdb.models as models
from NewsScraper.poet_pages.base_pages import ArticlePage, ArticleResultsPage
from NewsScraper.poet_pages.nytimes_pages import NyTimesArticlePage, NyTimesRssPage


class BaseNewsSpider(scrapy.Spider):
    name = 'news_spider'

    custom_settings = {
        'SCRAPY_POET_RULES': [
            ApplyRule('www.nytimes.com', use=NyTimesArticlePage, instead_of=ArticlePage),
            ApplyRule('rss.nytimes.com', use=NyTimesRssPage, instead_of=ArticleResultsPage),
        ]
    }

    def start_requests(self) -> Iterable[Request]:

        models.init_db(self.settings.get('MYSQL_CONNECTION_STRING'))

        with models.Session() as session:
            for source in session.query(models.ScraperSource).all():
                yield Request(
                    url=source.source_url,
                    cb_kwargs={
                        'source': {
                            'category_id': source.category_id,
                            'city_id': source.city_id,
                        }
                    },
                    meta={'zyte_api_automap': False} if source.is_rss else {},
                    callback=self.parse_article_results
                )

    def parse_article_results(self, response: Response, article_results_page: ArticleResultsPage, **kwargs: Any) -> Any:
        with models.Session() as session:

            for article in article_results_page.parse_articles():

                result = session.query(models.Article.article_id).filter(
                        sqlalchemy.and_(
                            models.Article.news_hash == article['news_hash'],
                            models.Article.created_at_timestamp == int(article['created_at_timestamp'])
                        )
                ).first()
                if result is not None:
                    continue

                else:
                    self.logger.info(f"New article found: {article['news_hash']} - {article['source_url']} - {article['created_at_timestamp']}")

                continue

                article['journalist_id'] = 1
                article['category_id'] = kwargs['source']['category_id']
                article['city_id'] = kwargs['source']['city_id']

                yield Request(
                    url=article['source_url'],
                    cb_kwargs={
                        'init_item': article,
                    },
                    callback=self.parse_article
                )

    def parse_article(self, response: scrapy.http.Response, article_page: ArticlePage, **kwargs):
        yield article_page.to_item()

    async def inline_request(self, request: Request | str) -> Response:
        _request = request if isinstance(request, Request) else Request(url=request)
        deferred = self.crawler.engine.download(_request)
        return await maybe_deferred_to_future(deferred)
