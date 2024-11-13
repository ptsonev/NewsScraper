import json
import re

from parsel import Selector
from tldextract import tldextract


def normalize_whitespaces(text: str) -> str:
    if text is None:
        return ''
    return re.sub(r'\s+', ' ', str(text)).strip()


def get_script_json(input_html: Selector | str, prefix_expr: str) -> dict:
    prefix_expr_re = re.compile(prefix_expr)

    html_selector = input_html if isinstance(input_html, Selector) else Selector(text=input_html)
    for script_js in html_selector.xpath('//script/text()').getall():
        if not script_js or not prefix_expr_re.match(script_js):
            continue

        script_js = prefix_expr_re.sub("", script_js)
        if script_js.endswith(";"):
            script_js = script_js[:-1]

        script_js = script_js.replace(":undefined", ":null")

        return json.loads(script_js)


def get_domain(url: str) -> str:
    return tldextract.extract(url).registered_domain.lower()
