from typing import Iterable

from bs4 import BeautifulSoup, Tag
from jsonpath_ng import parse

from NewsScraper.items import ArticleItem
from NewsScraper.poet_pages.base_pages import ArticlePage, ArticleRssPage
from NewsScraper.utils import get_script_json


class NyTimesRssPage(ArticleRssPage):

    def filter_article(self, article: ArticleItem) -> bool:
        urls_to_ignore = [
            'nytimes.com/athletic/',
            'nytimes.com/video/',
            'nytimes.com/live/',
            'nytimes.com/newsletters/',
            'nytimes.com/card/',
        ]

        return not any(url in article['source_url'] for url in urls_to_ignore)


class NyTimesArticlePage(ArticlePage):
    def to_item(self):
        nytimes_parser = NyTimesParser()

        try:
            content = nytimes_parser.parse(self.response.text)
            self.init_item['content'] = content

        except Exception as ex:
            self.logger.exception(ex)

        return self.init_item


class NyTimesParser:
    PARAGRAPH_TYPES = {
        'ParagraphBlock': 'p',
        'LabelBlock': 'h4',
        'DetailBlock': 'p',
        'SummaryBlock': 'p',
        'Heading1Block': 'h1',
        'Heading2Block': 'h2',
        'Heading3Block': 'h3',
        'Heading4Block': 'h4',
        'Heading5Block': 'h5',
        'Heading6Block': 'h6',
        'BlockquoteBlock': 'blockquote',
        'PullquoteBlock': 'blockquote',
    }

    IGNORE_BLOCKS = {
        'Dropzone',
        'RelatedLinksBlock',
        'EmailSignupBlock',
        'CapsuleBlock',
        'InteractiveBlock',
        'RelatedLinksBlock',
        'UnstructuredBlock',
        'BylineBlock',
        'AudioBlock',
        'InstagramEmbedBlock',
        'TwitterEmbedBlock',
    }

    HEADERS = {
        'HeaderBasicBlock',
        'HeaderFullBleedVerticalBlock',
        'HeaderFullBleedHorizontalBlock',
        'HeaderMultimediaBlock',
        'HeaderLegacyBlock',
    }

    def __init__(self):
        self.b_soup: BeautifulSoup = None
        self.content_expression = parse('$..content')
        self.image_url_expression = parse('$..crops[0].renditions[0].url')

        self.caption_expression = parse('$..caption | $..legacyHtmlCaption')

    def parse(self, news_html: str) -> str:

        news_json = get_script_json(news_html, 'window.__preloadedData\s*=')
        try:
            article_blocks = news_json['initialData']['data']['article']['sprinkledBody']['content']
        except (KeyError, TypeError):
            return

        self.b_soup = BeautifulSoup(features='html.parser')
        for tag in self.parse_blocks(article_blocks) or []:

            if not tag:
                continue

            if tag.name == 'figcaption' and not tag.text:
                continue

            self.b_soup.append(tag)

        return str(self.b_soup.prettify())

    def parse_blocks(self, article_blocks: list[dict]) -> Iterable[Tag]:

        for block in article_blocks:
            block_type = block.get('__typename')

            if block_type in self.IGNORE_BLOCKS:
                continue

            elif block_type in self.PARAGRAPH_TYPES:
                yield from self.parse_paragraph_block(block)

            elif block_type in self.HEADERS:
                yield from self.parse_paragraph_block(block.get('headline'))
                yield from self.parse_paragraph_block(block.get('summary'))
                yield from self.parse_image_block(block.get('ledeMedia'))

            elif block_type == 'ImageBlock':
                yield from self.parse_image_block(block)

            elif block_type == 'DiptychBlock':
                yield from self.parse_image_block(block['imageOne'])
                yield from self.parse_image_block(block['imageTwo'])

            elif block_type == 'GridBlock':
                for image in block['gridMedia']:
                    yield from self.parse_image_block(image)
                yield self.create_element_from_block('figcaption', block)

            elif block_type == 'VisualStackBlock':
                yield from self.parse_image_block(block['vsMedia'], False)
                for content_block in block['content']:
                    yield from self.parse_paragraph_block(content_block)

            elif block_type == 'ListBlock':
                if block.get('style') == 'UNORDERED':
                    list_tag = self.b_soup.new_tag('ul')
                else:
                    list_tag = self.b_soup.new_tag('ol')

                for list_content in block['content']:
                    if list_item := self.create_element_from_block('li', list_content):
                        list_tag.append(list_item)
                yield list_tag

            elif block_type == 'YouTubeEmbedBlock':
                yield self.b_soup.new_tag('iframe', src=f'https://www.youtube.com/embed/{block["youTubeId"]}')

            elif block_type == 'RuleBlock':
                yield self.b_soup.new_tag('hr')

            elif block_type == 'LineBreakInline':
                yield self.b_soup.new_tag('br')

            elif block_type == 'CardDeckBlock':
                # TODO: This is the gallery widget, e.g. https://www.nytimes.com/2024/10/10/style/handbag-shape-trend-dachshund-bag.html
                pass
            elif block_type == 'VideoBlock':
                # TODO: This is the video widget(GIF like), e.g. https://www.nytimes.com/2024/10/13/business/millennials-spending.html
                pass

            else:
                raise Exception(f'Unknown block type: {block_type}')

    def create_element_from_block(self, element_tag: str, block: dict) -> Tag:
        if not block:
            return

        element = self.b_soup.new_tag(element_tag)
        self.parse_block_content(block, element)
        return element

    def parse_paragraph_block(self, block: dict):
        if not block:
            return
        yield self.create_element_from_block(self.PARAGRAPH_TYPES[block['__typename']], block)

    def parse_image_block(self, block: dict, parse_caption: bool = True):
        if not block:
            return
        try:
            image_src = self.image_url_expression.find(block)[0].value
        except IndexError:
            return

        image_block = self.b_soup.new_tag('img', src=image_src)
        yield image_block
        if parse_caption:
            yield self.create_element_from_block('figcaption', block)

    def parse_block_content(self, block: dict, parent_tag: Tag) -> None:

        content_blocks = [block for match in self.content_expression.find(block) for block in match.value]

        if not content_blocks:
            for caption in self.caption_expression.find(block):
                if caption.value and isinstance(caption.value, str):
                    parent_tag.append(caption.value)
                    return

        for content in content_blocks:
            if content['__typename'] == 'TextInline':

                formats = content.get('formats') or []
                formats.append({'__typename': 'TextFormat', 'text': content.get('text')})

                nested_tag: Tag = self.b_soup.new_tag('root')
                for current_format in formats:
                    format_type = current_format['__typename']

                    if format_type == 'LinkFormat':
                        format_tag = self.b_soup.new_tag('a', href=current_format['url'])

                    elif format_type == 'BoldFormat':
                        format_tag = self.b_soup.new_tag('b')

                    elif format_type == 'ItalicFormat':
                        format_tag = self.b_soup.new_tag('em')

                    elif format_type == 'TextFormat':
                        format_tag = self.b_soup.new_string(current_format['text'])

                    else:
                        raise Exception(f'Unknown format type: {format_type}')

                    if descendants := list(nested_tag.descendants):
                        descendants[-1].append(format_tag)
                    else:
                        nested_tag.append(format_tag)

                parent_tag.append(nested_tag.next)
