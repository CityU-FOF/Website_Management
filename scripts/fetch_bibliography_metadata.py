"""Cache public Crossref metadata, with bounded concurrency and retry handling."""
import argparse
import concurrent.futures
import hashlib
import json
import time
import threading
from pathlib import Path
from urllib.parse import quote

import requests

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'work/bibliography/crossref'
LOCAL=threading.local()
RATE_LOCK=threading.Lock()
NEXT_REQUEST=0.0


def fetch(url):
    CACHE.mkdir(parents=True,exist_ok=True)
    path=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if path.exists():
        existing=json.loads(path.read_text())
        if existing.get('status')!=429:return existing
    result={'url':url}
    if not hasattr(LOCAL,'session'):
        LOCAL.session=requests.Session()
    for attempt in range(3):
        try:
            global NEXT_REQUEST
            with RATE_LOCK:
                delay=max(0,NEXT_REQUEST-time.monotonic())
                NEXT_REQUEST=max(NEXT_REQUEST,time.monotonic())+1.1
            if delay:time.sleep(delay)
            response=LOCAL.session.get(url,timeout=20,headers={'User-Agent':'FOF-Profile-Metadata-Formatter/1.0'})
            result['status']=response.status_code
            if response.status_code in {429,500,502,503,504}:
                time.sleep(float(response.headers.get('Retry-After',2*(attempt+1))))
                continue
            if response.ok:
                message=response.json()['message']
                entries=message.get('items',[]) if 'items' in message else [message]
                fields=['DOI','title','author','container-title','publisher','published','published-print','published-online','issued','type','volume','issue','page','article-number','score','ISBN']
                result['items']=[{k:m[k] for k in fields if k in m} for m in entries]
            break
        except Exception as error:
            result['error']=str(error)
            if attempt<2:time.sleep(2)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result


def doi_url(doi):
    return 'https://api.crossref.org/works/'+quote(doi.removeprefix('https://doi.org/'),safe='/')


def search_url(query):
    return 'https://api.crossref.org/works?query.bibliographic='+quote(query)+'&rows=3'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--queries',type=Path)
    args=parser.parse_args()
    if args.queries:
        queries=json.loads(args.queries.read_text())
        urls=[search_url(q['query']) for q in queries]
    else:
        backup=json.loads((ROOT/'FOF_Profile_Backup_All_Faculty_2026-11-17.json').read_text())
        urls=list(dict.fromkeys(doi_url(r['DOI']) for r in backup['data']['研究成果'] if r.get('DOI')))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for i,result in enumerate(pool.map(fetch,urls),1):
            print(i,len(urls),result.get('status'),result['url'],flush=True)


if __name__=='__main__':main()
