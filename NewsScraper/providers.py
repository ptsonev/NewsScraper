from typing import Callable, Set, Union, Optional

from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.exceptions import IgnoreRequest
from scrapy.http.request import NO_CALLBACK
from scrapy.utils.defer import maybe_deferred_to_future
from scrapy_poet import PageObjectInputProvider
from scrapy_poet.utils import (
    http_request_to_scrapy_request,
    scrapy_response_to_http_response,
)
from web_poet import HttpClient, HttpRequest, HttpResponse
from web_poet.exceptions import HttpError, HttpRequestError
from web_poet.page_inputs.client import _Headers, _StatusList
from web_poet.page_inputs.url import _Url
from yarl import URL

from NewsScraper.items import ArticleItem


# Injected Classes
class HttpClientEx(HttpClient):

    async def get(
            self,
            url: Union[str, _Url, URL],
            *,
            headers: Optional[_Headers] = None,
            allow_status: _StatusList = None,
    ) -> HttpResponse:
        return await super().get(str(url), headers=headers, allow_status=allow_status)


# Providers
class HttpClientProviderEx(PageObjectInputProvider):
    """This class provides :class:`web_poet.HttpClient
    <web_poet.page_inputs.client.HttpClient>` instances.
    """

    provided_classes = {HttpClientEx}

    def __call__(self, to_provide: Set[Callable], crawler: Crawler):
        """Creates an :class:`web_poet.HttpClient
        <web_poet.page_inputs.client.HttpClient>` instance using Scrapy's
        downloader.
        """
        downloader = self.create_scrapy_downloader_ex(crawler.engine.download)
        save_responses = crawler.settings.getbool("_SCRAPY_POET_SAVEFIXTURE")
        return [
            HttpClientEx(request_downloader=downloader, save_responses=save_responses)
        ]

    def create_scrapy_downloader_ex(self, download_func):
        async def scrapy_downloader(request: HttpRequest):
            if not isinstance(request, HttpRequest) and not isinstance(request, Request):
                raise TypeError(
                    f"The request should be 'web_poet.HttpRequest' or 'scrapy.Request' but received "
                    f"one of type: {type(request)!r}."
                )

            if isinstance(request, Request):
                scrapy_request = request.replace(callback=NO_CALLBACK)
            else:
                _meta = getattr(request, 'meta', {})
                scrapy_request = http_request_to_scrapy_request(request, meta=_meta)

            scrapy_request.dont_filter = True

            if scrapy_request.method == "HEAD":
                scrapy_request.meta["dont_redirect"] = True

            deferred = download_func(scrapy_request)
            deferred_or_future = maybe_deferred_to_future(deferred)
            try:
                response = await deferred_or_future
            except IgnoreRequest as e:
                # A Scrapy downloader middleware has caused the request to be
                # ignored.
                message = f"Additional request ignored: {scrapy_request}"
                raise HttpError(message) from e
            except Exception as e:
                # This could be caused either by network errors (Twisted
                # exceptions, OpenSSL, exceptions, etc.) or by unhandled exceptions
                # in Scrapy downloader middlewares. We assume the former (raise
                # HttpRequestError instead of HttpError), it being the most likely,
                # and the latter only happening due to badly written code.
                message = f"Additional request failed: {scrapy_request}"
                raise HttpRequestError(message) from e

            return scrapy_response_to_http_response(response)

        return scrapy_downloader


class InitArticleItemProvider(PageObjectInputProvider):
    """This class provides :class:`ArticleItem` instances.
    """

    provided_classes = {ArticleItem}

    def __call__(self, to_provide: Set[Callable], request: Request):
        return [
            request.cb_kwargs.get('init_item') or ArticleItem()
        ]
