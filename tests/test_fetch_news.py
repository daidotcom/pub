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


if __name__ == '__main__':
    unittest.main()
