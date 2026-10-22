"""Download Yahoo News headlines and the short descriptions supplied by articles."""
import datetime
import email.utils
import json
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

FEEDS = [
    ('主要', 'https://news.yahoo.co.jp/rss/topics/top-picks.xml'),
    ('社会', 'https://news.yahoo.co.jp/rss/topics/domestic.xml'),
    ('経済', 'https://news.yahoo.co.jp/rss/topics/business.xml'),
    ('AI・テクノロジー', 'https://news.yahoo.co.jp/rss/topics/it.xml'),
]


class DescriptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.description = ''
        self.og_description = ''

    def handle_starttag(self, tag, attrs):
        if tag.lower() != 'meta':
            return
        attrs = dict(attrs)
        content = ' '.join(attrs.get('content', '').split())
        if attrs.get('property', '').lower() == 'og:description':
            self.og_description = content
        elif attrs.get('name', '').lower() == 'description':
            self.description = content


def download(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 NewsFlow/1.0'})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read(2_000_000)


def add_summary(article):
    try:
        parser = DescriptionParser()
        parser.feed(download(article['link']).decode('utf-8'))
        summary = parser.og_description or parser.description
        article['summary'] = summary[:240] + ('…' if len(summary) > 240 else '')
    except Exception as error:
        # A missing summary must not discard an otherwise usable headline.
        print('Summary unavailable:', article['link'], type(error).__name__)
        article['summary'] = ''
    return article


def main():
    articles, seen, errors = [], set(), []
    for category, url in FEEDS:
        try:
            root = ET.fromstring(download(url))
            for item in root.findall('.//item')[:20]:
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                if not title or not link.startswith('https://news.yahoo.co.jp/') or title in seen:
                    continue
                seen.add(title)
                try:
                    date = email.utils.parsedate_to_datetime(item.findtext('pubDate', ''))
                    published = date.astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M')
                except (ValueError, TypeError, AttributeError):
                    published = ''
                articles.append({'category': category, 'title': title, 'link': link,
                                 'published': published, 'source': 'Yahoo!ニュース'})
        except Exception as error:
            errors.append(f'{category}: {error}')
    if not articles:
        raise SystemExit('No news feeds available: ' + str(errors))
    with ThreadPoolExecutor(max_workers=4) as pool:
        articles = list(pool.map(add_summary, articles))
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    Path('news.json').write_text(json.dumps(
        {'updated': now, 'articles': articles, 'errors': errors},
        ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved', len(articles), 'articles;', sum(bool(a['summary']) for a in articles),
          'summaries; feed errors:', errors)


if __name__ == '__main__':
    main()
