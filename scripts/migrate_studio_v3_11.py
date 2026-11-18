"""Prepare 3.11 data: dated sections in source order, media rows, gallery and badges."""
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup
from normalize_career_dates import MONTHS, MONTH_PATTERN

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'FOF_Profile_Backup_All_Faculty_2026-11-17.json'
OUTPUT=ROOT/'FOF_Profile_Backup_All_Faculty_2026-11-18.json'
MODULES={'研究項目','學術服務與指導','獎項','媒體報道'}
TOKEN=re.compile(r'(?<![\dA-Za-z])(?:(?:'+MONTH_PATTERN+r')\.?\s*,?\s*(?:19|20)\d{2}|\d{1,2}/(?:19|20)\d{2}|(?:19|20)\d{2}(?:\s*年(?:\s*\d{1,2}\s*月(?:\s*\d{1,2}\s*日)?)?|[./]\d{1,2}(?:[./]\d{1,2})?)?)(?!\d)',re.I)

def date_token(text):
    m=re.fullmatch(r'('+MONTH_PATTERN+r')\.?\s*,?\s*((?:19|20)\d{2})',text,re.I)
    if m:return f'{m[2]}/{MONTHS[m[1].lower()]:02d}'
    m=re.fullmatch(r'(\d{1,2})/((?:19|20)\d{2})',text)
    if m:return f'{m[2]}/{int(m[1]):02d}'
    values=[int(v) for v in re.findall(r'\d+',text)]
    if len(values)>1 and not 1<=values[1]<=12:return ''
    if len(values)>2 and not 1<=values[2]<=31:return ''
    return str(values[0])+''.join('/'+str(v).zfill(2) for v in values[1:])

def extract_date(text,lang):
    if not text.strip():return '',text,'empty'
    # A row is kept intact; dates inside study titles are not deleted as date labels.
    line=text.split('\n',1)[0]
    tokens=list(TOKEN.finditer(line));blocks=[];i=0
    while i<len(tokens):
        m=tokens[i];start,end=m.span();date=date_token(m[0]);i+=1
        if not date:continue
        if i<len(tokens) and re.fullmatch(r'\s*(?:[-–—~～至到]|to)\s*',line[end:tokens[i].start()],re.I):
            second=tokens[i];date+=' – '+date_token(second[0]);end=second.end();i+=1
        else:
            short=re.match(r'\s*[-–—]\s*(\d{2})(?!\d)',line[end:])
            ongoing=re.match(r'\s*(?:[-–—至:：]*\s*)(?:present|current|now|至今|迄今|現在|现在|現今|今)(?![A-Za-z])',line[end:],re.I)
            if short and len(date)==4:date+=' – '+date[:2]+short[1];end+=short.end()
            elif ongoing:date+=' – '+('Present' if lang=='en' else '至今');end+=ongoing.end()
            elif not line[:start].strip() and (opening:=re.match(r'\s*[-–—]\s*(?=[^\d\s]|$)',line[end:])):
                date+=' – '+('Present' if lang=='en' else '至今');end+=opening.end()
        blocks.append((start,end,date))
    if not blocks:return '',text,'no date supplied'
    prefix=[b for b in blocks if not line[:b[0]].strip(' \t()（）：:•·-*')]
    suffix=[b for b in blocks if not line[b[1]:].strip(' \t()（）.,，。;；')]
    chosen=(prefix or [b for b in suffix if '/' in b[2]] or suffix or blocks)[0]
    start,end,date=chosen
    clear=bool(chosen in prefix or chosen in suffix)
    if clear:
        body=(text[:start]+text[end:]).strip(' \t,，.。;；:：–—-')
        body=re.sub(r'[（(]\s*[)）]','',body).strip(' \t,，.。;；:：–—-')
        return date,body,'prefix' if chosen in prefix else 'suffix'
    # Embedded years may belong to an award or study title: show a date without truncating the title.
    return date,text,'embedded date retained in content'

def source_additions():
    path=ROOT/'data/studio_v3_11_source_additions.json'
    if path.exists():return json.loads(path.read_text())
    records={}
    for lang in ['zh','en']:
        file=ROOT/f'work/arman_live_{lang}.html'
        soup=BeautifulSoup(file.read_text(),'html.parser')
        urls=[img['data-src'] for img in soup.select('img.owl-lazy[data-src]')]
        assert len(urls)==3
        records[lang]={'url':'https://fof.cityu.edu.mo/'+('en/' if lang=='en' else '')+'arman',
                       'page_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'photo_urls':urls}
    out={'captured_on':'2026-11-18','arman_gallery':records,
         'highlight_sources':{'_adriancheung':'https://fof.cityu.edu.mo/adriancheung','cclee':'https://fof.cityu.edu.mo/cclee'}}
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');return out

def main():
    backup=json.loads(INPUT.read_text());data=backup['data'];sources=source_additions()
    for p in data['教師資料']:
        p.update({'亮點標籤':'','亮點標籤（英文）':'','核對指紋':'','確認時間':'','最後編輯時間':''})
        if p['教師ID'] in sources['highlight_sources']:
            p.update({'亮點標籤':'全球前2%頂尖科學家','亮點標籤（英文）':'World’s Top 2% Scientists','亮點標籤來源':sources['highlight_sources'][p['教師ID']]})
        if p['教師ID']=='arman':p['原相片網址']=p['相片網址'];p['相片網址']='\n'.join(sources['arman_gallery']['zh']['photo_urls'])
    content=[];media_count=0
    for row in data['內容明細']:
        if row['教師ID']=='arman' and row['模組']=='其他公開資訊':
            zh=row['內容'].splitlines();en=row.get('內容（英文）','').splitlines();assert len(zh)==len(en)==30
            for i,(a,b) in enumerate(zip(zh,en),1):
                new=copy.deepcopy(row);new.update({'模組':'媒體報道','排序':i,'內容':a,'內容（英文）':b});content.append(new);media_count+=1
        else:content.append(row)
    data['內容明細']=content;audit=[]
    for row in content:
        if row['模組'] not in MODULES:continue
        dates={}
        for lang,key,timekey in [('zh','內容','時間'),('en','內容（英文）','時間（英文）')]:
            original=row.get(key,'');date,body,rule=extract_date(original,lang)
            row['版塊日期原文（'+('中文' if lang=='zh' else '英文')+'）']=original
            if not row.get(timekey):row[timekey]=date
            if date:row[key]=body
            dates[lang]={'date':row.get(timekey,''),'rule':rule,'source':original,'content':row[key]}
        if not row.get('內容') and not row.get('時間') and row.get('時間（英文）'):row['時間']=row['時間（英文）'].replace('Present','至今')
        row['版塊日期版本']=1
        audit.append({'teacher':row['教師ID'],'module':row['模組'],'order':row['排序'],**dates})
    backup['appVersion']='3.11';backup['savedAt']=datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(backup,ensure_ascii=False,indent=2)+'\n')
    report={'teachers':len(data['教師資料']),'content_rows':len(content),'research_rows':len(data['研究成果']),
            'media_rows':media_count,'gallery_photos':3,'highlighted_teachers':list(sources['highlight_sources']),
            'date_policy':'有月份使用YYYY/MM，有日保留YYYY/MM/DD，只有年份保留YYYY。未提供日期留空，不按日期重排；保留原排序。',
            'sections':{m:{'rows':sum(r['模組']==m for r in content),'with_date':sum(r['模組']==m and bool(r.get('時間')) for r in content)} for m in sorted(MODULES)},'date_audit':audit}
    (ROOT/'data/studio_v3_11_migration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='date_audit'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
