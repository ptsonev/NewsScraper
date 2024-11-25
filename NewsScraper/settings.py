# Scrapy settings for NewsScraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "NewsScraper"

SPIDER_MODULES = ["NewsScraper.spiders"]
NEWSPIDER_MODULE = "NewsScraper.spiders"

ZYTE_API_TRANSPARENT_MODE = True

MYSQL_CONNECTION_STRING = "mysql+pymysql://root:root@localhost:4306/newsdb"

# API Keys
ZYTE_API_KEY = "ZYTE_API_KEY"
SCRAPINGHUB_API_KEY = "SCRAPINGHUB_API_KEY"

ADDONS = {
    "scrapy_zyte_api.Addon": 500,
}

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

HTTPPROXY_ENABLED = True
HTTP_PROXY = None

ZYTE_API_EXPERIMENTAL_COOKIES_ENABLED = False
ZYTE_API_SESSION_ENABLED = False
ZYTE_API_USE_ENV_PROXY = True
ZYTE_API_AUTOMAP_PARAMS = {
    "geolocation": "US",
    "httpResponseBody": True,
    "httpResponseHeaders": True,
}
ZYTE_API_PROVIDER_PARAMS = {
    "geolocation": "US",
}

ZYTE_API_RETRY_POLICY = "NewsScraper.retry_policies.RETRY_POLICY_EXTENDED"
REFERRER_POLICY = "no-referrer"

SCRAPY_POET_PROVIDERS = {
    "NewsScraper.providers.HttpClientProviderEx": 500,
    "NewsScraper.providers.InitArticleItemProvider": 501,
    "scrapy_zyte_api.providers.ZyteApiProvider": 1100,
}

UNWANTED_CODES = [400, 401, 403, 404, 405, 407, 429, 500, 502, 503, 504, 520, 521, 522, 523, 540, 541]

RETRY_TIMES = 5
RETRY_HTTP_CODES = [c for c in UNWANTED_CODES if c not in [404]]

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# LOG_FILE = 'scrapy.log'
PERIODIC_LOG_STATS = False
LOGSTATS = True
LOGSTATS_INTERVAL = 15
LOG_LEVEL = "INFO"

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 5
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 100

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

SPIDERMON_ENABLED = True
SPIDERMON_EMAIL_FAKE = True
SPIDERMON_MAX_ERRORS = 0
SPIDERMON_SPIDER_CLOSE_MONITORS = (
    "NewsScraper.monitors.SingleErrorMonitorSuite"
)
SPIDERMON_EMAIL_TO = ["petko.tsonev@gmail.com"]
SPIDERMON_EMAIL_SUBJECT = "Something went wrong with the News Scraper."
SPIDERMON_ADD_FIELD_COVERAGE = True
SPIDERMON_FIELD_COVERAGE_SKIP_IF_NO_ITEM = True
SPIDERMON_FIELD_COVERAGE_RULES = {
    # TODO: Add rules
}

SPIDERMON_UNWANTED_HTTP_CODES_MAX_COUNT = 0
SPIDERMON_UNWANTED_HTTP_CODES = UNWANTED_CODES

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
    "scrapy_poet.RetryMiddleware": 275,
}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "NewsScraper.middlewares.ProxyMiddleware": 100,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
EXTENSIONS = {
    "scrapy.extensions.periodic_log.PeriodicLog": 0,
    "spidermon.contrib.scrapy.extensions.Spidermon": 500,
}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    "NewsScraper.pipelines.DefaultPipeline": 100,
    "NewsScraper.pipelines.MySQLPipeline": 101,
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
