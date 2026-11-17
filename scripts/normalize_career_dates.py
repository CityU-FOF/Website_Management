"""Rebuild career rows from original pages and separate dates from appointment text."""
import copy
import json
import re

from integrate_faculty import ROOT, OUTPUT, items, strip_bullet

MONTHS={s:i+1 for i,values in enumerate([
    ['jan','january'],['feb','february'],['mar','march'],['apr','april'],['may'],['jun','june'],
    ['jul','july'],['aug','august'],['sep','sept','september'],['oct','october'],['nov','november'],['dec','december']]) for s in values}
MONTH_PATTERN='|'.join(sorted(MONTHS,key=len,reverse=True))
TOKEN=re.compile(r'(?<!\d)(?:(?:'+MONTH_PATTERN+r')\.?\s+(?:19|20)\d{2}|\d{1,2}/(?:19|20)\d{2}|(?:19|20)\d{2}(?:\s*年(?:\s*\d{1,2}\s*月)?|[./]\d{1,2})?)(?!\d)',re.I)


def date_token(value):
    text=value.strip()
    match=re.match(r'('+MONTH_PATTERN+r')\.?\s+((?:19|20)\d{2})',text,re.I)
    if match:return f'{match[2]}/{MONTHS[match[1].lower()]:02d}'
    match=re.fullmatch(r'(\d{1,2})/((?:19|20)\d{2})',text)
    if match:return f'{match[2]}/{int(match[1]):02d}'
    match=re.fullmatch(r'((?:19|20)\d{2})(?:\s*年(?:\s*(\d{1,2})\s*月)?|[./](\d{1,2}))?',text)
    if match:
        month=match[2] or match[3]
        return match[1]+(f'/{int(month):02d}' if month else '')
    raise ValueError(value)


def separate_date(value,lang='zh'):
    text=strip_bullet(value)
    matches=list(TOKEN.finditer(text))
    if not matches:return '',text
    first=matches[0]
    last=first
    start=date_token(first[0]);end=''
    if len(matches)>1 and re.fullmatch(r'[\s:：,，–—\-至到~～]*(?:to)?[\s:：,，–—\-至到~～]*',text[first.end():matches[1].start()],re.I):
        last=matches[1];end=date_token(last[0])
    else:
        short=re.match(r'\s*[-–—]\s*(\d{2})(?!\d)',text[first.end():])
        if short and len(start)==4:
            end=start[:2]+short[1]
            last_end=first.end()+short.end()
        else:last_end=first.end()
        ongoing=re.match(r'\s*[-–—至:：]*\s*(?:present|current|now|至今|迄今|現在|现在|現今|今)(?![A-Za-z])',text[last_end:],re.I)
        if ongoing:
            end='Present' if lang=='en' else '至今';last_end+=ongoing.end()
        elif not end and re.match(r'\s*[-–—]\s*[:：]?(?=\s*[^\d])',text[last_end:]):
            open_match=re.match(r'\s*[-–—]\s*[:：]?',text[last_end:]);last_end+=open_match.end();end='Present' if lang=='en' else '至今'
    if last is not first:last_end=last.end()
    # Chinese "From YEAR" and English From/From...to are formatting tokens.
    before=text[:first.start()]
    after=text[last_end:]
    before=re.sub(r'\bfrom\s*$','',before,flags=re.I)
    body=(before.rstrip(' ,，:：-–—')+' '+after.lstrip(' ,，:：-–—')).strip()
    return start+(' – '+end if end else ''),body


def grouped(source_id,lang,rows):
    if source_id=='ygwang':
        groups=[[0,1,2],[3,4,5],[6,7,8]] if lang=='zh' else [[0,1],[2,3],[4,5]]
        return [{**rows[g[0]],'text':'\n'.join(rows[i]['text'] for i in g)} for g in groups]
    if source_id=='jyhua' and lang=='en' and len(rows)==3:
        return [{**rows[0],'text':'\n'.join(r['text'] for r in rows)}]
    return rows


def normalized_rows(backup,snapshot):
    output=[];audit=[]
    for profile in snapshot['profiles']:
        tid=next(t['教師ID'] for t in backup['data']['教師資料'] if t['教師ID'].lstrip('_')==profile['id'])
        rows={lang:grouped(profile['id'],lang,items(profile[lang])[0].get('學術工作經驗',[])) for lang in ['zh','en']}
        for i in range(max(len(rows['zh']),len(rows['en']))):
            a=rows['zh'][i] if i<len(rows['zh']) else None;b=rows['en'][i] if i<len(rows['en']) else None
            zd,zt=separate_date(a['text'],'zh') if a else ('','')
            ed,et=separate_date(b['text'],'en') if b else ('','')
            row={'教師ID':tid,'模組':'學術工作經驗','排序':i+1,'時間':zd or ed.replace('Present','至今'),
                 '時間（英文）':ed,'內容':zt,'內容（英文）':et,'補充':'','補充（英文）':'','連結':'','語言':'中文','雙語欄位版本':1,
                 '來源網址（中文）':profile['zh']['url'] if a else '', '來源網址（英文）':profile['en']['url'] if b else '',
                 '原始經歷（中文）':a['text'] if a else '', '原始經歷（英文）':b['text'] if b else ''}
            output.append(row)
            audit.append({'teacher':tid,'order':i+1,'zh_time':zd,'en_time':ed,'zh':zt,'en':et})
    return output,audit


def main():
    backup=json.loads(OUTPUT.read_text());snapshot=json.loads((ROOT/'data/faculty_sources.json').read_text())
    rows,audit=normalized_rows(backup,snapshot)
    (ROOT/'work/bibliography/career_rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'work/bibliography/career_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    print('CAREER ROWS',len(rows),'TIME FILLED',sum(bool(r['時間']) for r in rows))
    for r in audit:
        print(r['teacher'],r['order'],r['zh_time'],'|',r['en_time'],'|',r['zh'][:70],'|',r['en'][:70])


if __name__=='__main__':main()
