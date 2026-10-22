"""Collect Japanese news and short publisher-provided descriptions."""
import datetime
import email.utils
import json
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from itertools import zip_longest

FEEDS = [
    ('主要', 'Yahoo!ニュース', ['https://news.yahoo.co.jp/rss/topics/top-picks.xml']),
    ('社会', 'Yahoo!ニュース', ['https://news.yahoo.co.jp/rss/topics/domestic.xml']),
    ('経済', 'Yahoo!ニュース', ['https://news.yahoo.co.jp/rss/topics/business.xml']),
    ('AI・テクノロジー', 'Yahoo!ニュース', ['https://news.yahoo.co.jp/rss/topics/it.xml']),
    ('スポーツ', 'Yahoo!ニュース', ['https://news.yahoo.co.jp/rss/topics/sports.xml']),
    ('総合', 'NHK', ['https://news.web.nhk/rss/news/cat0.xml',
                   'https://news.web.nhk/newsweb/rss/all.xml',
                   'https://www3.nhk.or.jp/rss/news/cat0.xml']),
    ('IT', 'ITmedia', ['https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml']),
]


def allowed_link(link, source):
    parsed = urlparse(link)
    hostname = parsed.hostname or ''
    domains = {'Yahoo!ニュース': ('news.yahoo.co.jp',),
               'NHK': ('nhk.or.jp', 'web.nhk'),
               'ITmedia': ('itmedia.co.jp',)}[source]
    return parsed.scheme == 'https' and any(
        hostname == domain or hostname.endswith('.' + domain) for domain in domains)


class PlainTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignored += 1
        elif tag in ('br', 'p', 'div', 'li'):
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored = max(0, self.ignored - 1)
        elif tag in ('p', 'div', 'li'):
            self.parts.append(' ')

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def excerpt(value):
    parser = PlainTextParser()
    parser.feed(value)
    text = ' '.join(''.join(parser.parts).split())
    return text[:240] + ('…' if len(text) > 240 else '')


def parse_feed(payload, category, source, now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    root = ET.fromstring(payload)
    articles = []
    nodes = [node for node in root.iter() if node.tag.rsplit('}', 1)[-1] == 'item']
    for item in nodes[:20]:
        fields = {child.tag.rsplit('}', 1)[-1]: child.text or '' for child in item}
        title = fields.get('title', '').strip()
        link = fields.get('link', '').strip()
        if link.startswith('http://'):
            link = 'https://' + link[len('http://'):]
        if not title or not allowed_link(link, source):
            continue
        try:
            date = email.utils.parsedate_to_datetime(fields.get('pubDate', ''))
            if date.tzinfo is None:
                date = date.replace(tzinfo=datetime.timezone.utc)
            if now - date > datetime.timedelta(hours=48) or date - now > datetime.timedelta(hours=1):
                continue
            published = date.astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M')
        except (ValueError, TypeError, AttributeError):
            published = ''
        articles.append({'category': category, 'title': title, 'link': link,
                         'published': published, 'source': source,
                         'summary': excerpt(fields.get('description', ''))})
    if not articles:
        raise ValueError('Feed contains no supported articles (root=' + root.tag +
                         ', links=' + str([n.text for n in root.iter()
                                           if n.tag.rsplit('}', 1)[-1] == 'link'][:3]) + ')')
    articles.sort(key=lambda article: article['published'], reverse=True)
    return articles


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
    if article.get('summary'):
        return article
    try:
        parser = DescriptionParser()
        parser.feed(download(article['link']).decode('utf-8'))
        summary = parser.og_description or parser.description
        article['summary'] = excerpt(summary)
    except Exception as error:
        # A missing summary must not discard an otherwise usable headline.
        print('Summary unavailable:', article['link'], type(error).__name__)
        article['summary'] = ''
    return article


def main():
    groups, seen, errors = [], set(), []
    for category, source, urls in FEEDS:
        failures = []
        for url in urls:
            try:
                batch = parse_feed(download(url), category, source)
                unique = []
                for article in batch:
                    if article['title'] not in seen:
                        seen.add(article['title'])
                        unique.append(article)
                groups.append(unique)
                print(source, category, len(unique), 'articles', flush=True)
                break
            except Exception as error:
                failures.append(f'{url}: {error}')
        else:
            errors.append(f'{source} / {category}: ' + '; '.join(failures))
    # Mix feeds so sports and the added publishers appear early in rotation.
    articles = [article for row in zip_longest(*groups) for article in row if article]
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
