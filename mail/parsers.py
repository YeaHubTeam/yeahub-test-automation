import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlparse

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+")
_VERIFICATION_LINK_FRAGMENT = "verify-email"
_VERIFICATION_LINK_PATH = "/auth/verify-email"
_PASSWORD_RECOVERY_FRAGMENT = "password-recovery"
_PASSWORD_RECOVERY_PATH = "/auth/password-recovery"


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


def _pick_link_with_token(
    links: list[str],
    *,
    path_fragment: str,
    exact_path: str,
) -> str | None:
    for link in links:
        if path_fragment not in link:
            continue
        try:
            parsed = urlparse(link)
        except Exception:
            continue
        if parsed.path != exact_path:
            continue
        token = (parse_qs(parsed.query).get("token") or [None])[0]
        if not token:
            continue
        return link
    return None


def _pick_verification_link(links: list[str]) -> str | None:
    return _pick_link_with_token(
        links,
        path_fragment=_VERIFICATION_LINK_FRAGMENT,
        exact_path=_VERIFICATION_LINK_PATH,
    )


def _pick_password_recovery_link(links: list[str]) -> str | None:
    return _pick_link_with_token(
        links,
        path_fragment=_PASSWORD_RECOVERY_FRAGMENT,
        exact_path=_PASSWORD_RECOVERY_PATH,
    )


def extract_verification_link(
    text: str | None = None,
    html: str | None = None,
) -> str | None:
    links: list[str] = []

    if html:
        parser = _HrefCollector()
        parser.feed(html)
        links.extend(parser.hrefs)
        links.extend(_URL_PATTERN.findall(html))

    if text:
        links.extend(_URL_PATTERN.findall(text))

    return _pick_verification_link(links)


def extract_password_recovery_link(
    text: str | None = None,
    html: str | None = None,
) -> str | None:
    links: list[str] = []

    if html:
        parser = _HrefCollector()
        parser.feed(html)
        links.extend(parser.hrefs)
        links.extend(_URL_PATTERN.findall(html))

    if text:
        links.extend(_URL_PATTERN.findall(text))

    return _pick_password_recovery_link(links)
