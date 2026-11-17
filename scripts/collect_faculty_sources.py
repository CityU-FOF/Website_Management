import concurrent.futures
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'work' / 'source'
BASE = 'https://fof.cityu.edu.mo'


def download(url, filename):
    target = SOURCE / filename
    if not target.exists():
        response = requests.get(url, timeout=45)
        response.raise_for_status()
        target.write_text(response.content.decode('utf-8'), encoding='utf-8')
    return target


def cards(filename):
    soup = BeautifulSoup((SOURCE / filename).read_text(), 'html.parser')
    records = []
    for card in soup.select('.staff-card'):
        section = next(p for p in card.parents if p.select_one('.rank-badge'))
        records.append({
            'id': urlsplit(card.select_one('a')['href']).path.rstrip('/').split('/')[-1],
            'name': card.select_one('.staff-name').get_text(' ', strip=True),
            'title': card.select_one('.staff-title').get_text(' ', strip=True),
            'supervision': card.select_one('.staff-mentor').get_text(' ', strip=True) if card.select_one('.staff-mentor') else '',
            'image': card.select_one('img')['src'],
            'url': card.select_one('a')['href'],
            'group': section.select_one('.rank-badge').get_text(' ', strip=True),
        })
    return records


def fetch(record):
    url = record['url']
    filename = urlsplit(url).path.strip('/').replace('/', '__') + '.html'
    target = download(url, filename)
    soup = BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser')
    article = soup.select_one('article.enter-content')
    if not article or len(article.get_text(strip=True)) < 30:
        raise ValueError(f'Missing/empty profile article: {url}')
    if '404 Error - Page not found' in article.get_text():
        raise ValueError(f'Soft 404 error page returned with HTTP 200: {url}')
    print(f'OK {record["id"]} {url} {len(article.get_text(strip=True))}', flush=True)
    return {**record, 'source_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'page_title': soup.title.get_text(' ', strip=True),
            'article_html': str(article), 'article_text': article.get_text('\n', strip=True)}


def main():
    parser = argparse.ArgumentParser(description='Collect complete bilingual faculty source articles; this is not a Studio import format.')
    parser.add_argument('--use-cache', action='store_true', help='Use previously downloaded pages for reproducible offline validation.')
    args = parser.parse_args()
    SOURCE.mkdir(parents=True, exist_ok=True)
    if not args.use_cache:
        for file in SOURCE.glob('*.html'):
            file.unlink()
    download(BASE + '/faculty', 'faculty.html')
    download(BASE + '/en/faculty', 'en__faculty.html')
    zh = cards('faculty.html')
    en = cards('en__faculty.html')
    if not zh or not en:
        raise ValueError('A faculty directory contains no teacher cards; refusing an empty export.')
    assert len(zh) == len({p['id'] for p in zh})
    # The English profile's language selector supplies the corrected Chinese URL.
    for record in zh:
        if record['id'] == 'julianzhsng':
            record['directory_url'] = record['url']
            record['id'] = 'julianzhang'
            record['url'] = BASE + '/julianzhang'
    assert {p['id'] for p in zh} == {p['id'] for p in en}
    assert len(en) == len({p['id'] for p in en})
    all_records = zh + en
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, all_records))
    by_url = {r['url']: r for r in results}
    en_by_id = {r['id']: r for r in en}
    combined = [{'id': r['id'], 'zh': by_url[r['url']], 'en': by_url[en_by_id[r['id']]['url']]} for r in zh]
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'data' / 'faculty_sources.json').write_text(json.dumps({
        'format': 'fof-faculty-source-snapshot/v1',
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'source': BASE + '/faculty',
        'english_source': BASE + '/en/faculty',
        'profile_count': len(combined),
        'studio_import_status': 'pending_original_json_and_html_schema',
        'profiles': combined
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'SAVED {len(combined)} bilingual profiles', flush=True)


if __name__ == '__main__':
    main()
