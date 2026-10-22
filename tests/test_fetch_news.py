import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('fetch_news', Path(__file__).resolve().parents[1] / 'fetch_news.py')
news = importlib.util.module_from_spec(spec)
spec.loader.exec_module(news)


class SummaryTests(unittest.TestCase):
    def test_metadata_preference_and_entities(self):
        page = '<meta name="description" content="fallback"><meta content="記事 &amp; 詳細" property="og:description">'
        with patch.object(news, 'download', return_value=page.encode()):
            article = news.add_summary({'link': 'https://news.yahoo.co.jp/pickup/test'})
        self.assertEqual(article['summary'], '記事 & 詳細')

    def test_missing_metadata_and_failed_download_keep_headline(self):
        for result in [b'<html></html>', OSError('offline')]:
            kwargs = {'side_effect': result} if isinstance(result, Exception) else {'return_value': result}
            with self.subTest(result=result), patch.object(news, 'download', **kwargs):
                article = news.add_summary({'title': '見出し', 'link': 'https://news.yahoo.co.jp/pickup/test'})
                self.assertEqual(article['summary'], '')
                self.assertEqual(article['title'], '見出し')

    def test_limit_excerpt_length(self):
        with patch.object(news, 'download', return_value=('<meta name="description" content="' + 'あ' * 300 + '">').encode()):
            self.assertEqual(news.add_summary({'link': 'https://news.yahoo.co.jp/pickup/test'})['summary'], 'あ' * 240 + '…')


class FeedTests(unittest.TestCase):
    def test_nhk_itmedia_and_sports_with_feed_descriptions(self):
        for source, category, link in [
            ('NHK', '総合', 'https://news.web.nhk/newsweb/na/na-k1001'),
            ('ITmedia', 'IT', 'https://www.itmedia.co.jp/news/articles/2610/22/news1.html'),
            ('Yahoo!ニュース', 'スポーツ', 'https://news.yahoo.co.jp/pickup/123')]:
            payload = ('<rss><channel><item><title>ニュース</title><link>' + link +
                       '</link><description>&lt;p&gt;記事の概要 &amp;amp; 詳細&lt;/p&gt;</description>'
                       '</item></channel></rss>').encode()
            with self.subTest(source=source):
                article = news.parse_feed(payload, category, source)[0]
                self.assertEqual(article['summary'], '記事の概要 & 詳細')
                self.assertEqual(article['source'], source)
                self.assertEqual(article['category'], category)
                with patch.object(news, 'download') as download:
                    self.assertEqual(news.add_summary(article), article)
                    download.assert_not_called()

    def test_unrelated_domains_and_empty_feeds_are_rejected(self):
        for link in ['https://itmedia.co.jp.evil.example/a', 'javascript:alert(1)']:
            self.assertFalse(news.allowed_link(link, 'ITmedia'))
        with self.assertRaises(ValueError):
            news.parse_feed(b'<rss><channel/></rss>', 'IT', 'ITmedia')


if __name__ == '__main__':
    unittest.main()
