import re
from html.parser import HTMLParser


_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")


class _HrefCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return

        for attr_name, attr_value in attrs:
            if attr_name.lower() == "href" and attr_value:
                self.hrefs.append(attr_value)
                break


def extract_first_link(text: str | None = None, html: str | None = None) -> str | None:
    if html:
        parser = _HrefCollector()
        parser.feed(html)

        if parser.hrefs:
            return parser.hrefs[0]

        html_match = _URL_PATTERN.search(html)
        if html_match:
            return html_match.group(0)

    if text:
        text_match = _URL_PATTERN.search(text)
        if text_match:
            return text_match.group(0)

    return None
