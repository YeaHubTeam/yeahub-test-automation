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


def _pick_preferred_link(links: list[str]) -> str | None:
    if not links:
        return None

    for link in links:
        if "verify-email" in link:
            return link

    return links[0]


def extract_first_link(text: str | None = None, html: str | None = None) -> str | None:
    links: list[str] = []

    if html:
        parser = _HrefCollector()
        parser.feed(html)
        links.extend(parser.hrefs)
        links.extend(_URL_PATTERN.findall(html))

    if text:
        links.extend(_URL_PATTERN.findall(text))

    return _pick_preferred_link(links)
