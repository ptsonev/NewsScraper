# Automatically created by: shub deploy

from setuptools import setup, find_packages

setup(
    name         = 'News Scraper',
    version      = '1.0',
    packages     = find_packages(),
    package_data = {
        'NewsScraper': ['resources/*.json', 'resources/*.html', 'resources/*.jinja']
    },
    entry_points = {'scrapy': ['settings = NewsScraper.settings']
    },
    zip_safe=False,
    include_package_data=True,
)
