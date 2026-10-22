import json, urllib.request, xml.etree.ElementTree as ET, datetime, email.utils, html
from pathlib import Path

FEEDS = [
 ('主要','https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja'),
 ('経済','https://news.google.com/rss/search?q=%E7%B5%8C%E6%B8%88&hl=ja&gl=JP&ceid=JP:ja'),
 ('AI・テクノロジー','https://news.google.com/rss/search?q=AI%20%E6%8A%80%E8%A1%93&hl=ja&gl=JP&ceid=JP:ja'),
 ('政治','https://news.google.com/rss/search?q=%E6%94%BF%E6%B2%BB&hl=ja&gl=JP&ceid=JP:ja'),
 ('社会','https://news.google.com/rss/search?q=%E7%A4%BE%E4%BC%9A&hl=ja&gl=JP&ceid=JP:ja'),
]
items=[]; seen=set(); errors=[]
for category,url in FEEDS:
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 NewsFlow/1.0'})
  with urllib.request.urlopen(req,timeout=25) as resp: root=ET.fromstring(resp.read())
  for node in root.findall('.//item')[:20]:
   title=html.unescape(node.findtext('title','')).strip()
   link=node.findtext('link','').strip()
   pub=node.findtext('pubDate','')
   if not title or not link or title in seen:continue
   seen.add(title)
   try: date=email.utils.parsedate_to_datetime(pub).astimezone(datetime.timezone(datetime.timedelta(hours=9))).strftime('%m/%d %H:%M')
   except Exception: date=''
   items.append({'category':category,'title':title,'link':link,'published':date})
 except Exception as e: errors.append(f'{category}: {e}')
path=Path('news.json')
if not items:
 if path.exists(): print('Feeds unavailable; preserving previous data',errors); exit(0)
 raise SystemExit('No news feeds available: '+str(errors))
# Interleave categories so consecutive items are varied.
groups={k:[x for x in items if x['category']==k] for k,_ in FEEDS}; mixed=[]
while any(groups.values()):
 for k,_ in FEEDS:
  if groups[k]:mixed.append(groups[k].pop(0))
now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M JST')
path.write_text(json.dumps({'updated':now,'items':mixed,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved',len(mixed),'articles; errors:',errors)
