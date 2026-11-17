"""Finalize the reviewed bibliography and career fields without changing the template."""
import collections
import copy
import json
import re
from datetime import datetime, timezone

from integrate_faculty import ROOT, OUTPUT, norm, items, prepare_content, content_text
from normalize_career_dates import normalized_rows


def main():
    backup=json.loads((ROOT/'work/bibliography/candidate_backup.json').read_text())
    snapshot=json.loads((ROOT/'data/faculty_sources.json').read_text())
    # Repair the old list-marker regex, which could consume a four-digit year.
    restored_prefixes=[]
    for profile in snapshot['profiles']:
        tid=next(t['教師ID'] for t in backup['data']['教師資料'] if t['教師ID'].lstrip('_')==profile['id'])
        for lang,key in [('zh','內容'),('en','內容（英文）')]:
            for module,source_rows in items(profile[lang])[0].items():
                if module=='學術工作經驗':continue
                for source in prepare_content(source_rows,module):
                    text=content_text(source)
                    legacy=re.sub(r'^\s*\d+[.)、]\s*','',text)
                    if legacy==text:continue
                    for row in backup['data']['內容明細']:
                        if row['教師ID']==tid and row['模組']==module and norm(row.get(key,''))==norm(legacy):
                            row[key]=text
                            restored_prefixes.append({'teacher':tid,'language':lang,'module':module,'restored':text})
    careers,date_audit=normalized_rows(backup,snapshot)
    career_by_teacher=collections.defaultdict(list)
    for row in careers:career_by_teacher[row['教師ID']].append(row)
    content=[];handled=set()
    for row in backup['data']['內容明細']:
        if row['模組']=='學術工作經驗':
            if row['教師ID'] not in handled:
                content.extend(career_by_teacher[row['教師ID']]);handled.add(row['教師ID'])
        else:content.append(row)
    backup['data']['內容明細']=content
    source_rows=backup['data']['研究成果']
    excluded=[];research=[];merged=[];additional_merges=[]
    for row in source_rows:
        if row['教師ID']=='ygwang' and row.get('完整引用','').strip()=='and Economics Press, 2015':
            excluded.append({'teacher':'ygwang','citation':row['完整引用'],'reason':'官方中英頁均只剩出版社與年份的殘句，不能識別為一項完整文獻；原文保留在來源快照。'})
            continue
        duplicate_target={('evakhong',7):5,('xzchen',17):7}.get((row['教師ID'],int(row['排序'])))
        if duplicate_target:
            parent=next(r for r in research if r['教師ID']==row['教師ID'] and int(r['排序'])==duplicate_target)
            lang='英文' if row['教師ID']=='xzchen' else '中文'
            for original_lang in ['中文','英文']:
                key='原始引用（'+original_lang+'）'
                refs=[parent.get(key,''),row.get(key,'')]
                if row.get('來源網址（'+original_lang+'）'):refs.append(row['完整引用'])
                parent[key]='\n'.join(dict.fromkeys(s for ref in refs for s in ref.splitlines() if s))
            if lang=='英文':
                parent['文章名（英文）']=row['文章名'];parent['期刊名（英文）']=row['期刊名']
            parent['雙語配對依據']='對照題目、作者、期刊、年份及頁碼，相同成果的重複引用合併；原引文保留。'
            additional_merges.append({'teacher':row['教師ID'],'title':parent['文章名'],'merged_citation':row['完整引用'],'basis':parent['雙語配對依據']})
            continue
        if row['教師ID']=='ygwang' and int(row['排序'])<=26 and int(row['排序'])%2==0:
            parent=research[-1]
            assert parent['教師ID']=='ygwang' and int(parent['排序'])==int(row['排序'])-1
            parent['文章名（中文）']=parent['文章名'];parent['期刊名（中文）']=parent['期刊名']
            parent['文章名（英文）']=row['文章名'];parent['期刊名（英文）']=row['期刊名']
            for key in ['原始引用（中文）','原始引用（英文）']:
                refs=list(dict.fromkeys((parent.get(key,'')+'\n'+row.get(key,'')).strip().splitlines()))
                parent[key]='\n'.join(refs)
            parent['雙語配對依據']='官方名單同一項成果的相鄰中英文引用，題目、期刊與年份對照後合併'
            merged.append({'teacher':'ygwang','zh':parent['文章名'],'en':row['文章名']})
            continue
        research.append(row)
    for row in research:
        row.pop('分欄原始引用',None)  # 完整引用 already preserves this verbatim.
        canonical=norm(row.get('完整引用',''))
        for key in ['原始引用（中文）','原始引用（英文）']:
            if row.get(key) and norm(row[key])==canonical:row.pop(key)
        if not row.get('期刊類別'):
            source=row.get('完整引用','')
            ranks=[m.group(1) for m in re.finditer(r'[(（]([^()（）]*(?:SSCI|CSSCI|TSSCI|ABDC|ABS |ERIM|JCR|FT50)[^()（）]*)[)）]',source)]
            row['期刊類別']='; '.join(dict.fromkeys(ranks))
        if row['教師ID']=='ygwang':row['作者資料說明']='原頁的本人作品清單未逐項列完整署名；列本人姓名，未推測其他作者。'
        if not row.get('作者'):row['作者資料說明']='原頁未公開完整作者名單，保留空白；不推測其他作者。'
        assert row.get('文章名'),(row['教師ID'],row.get('完整引用'))
    backup['data']['研究成果']=research
    backup['savedAt']=datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(backup,ensure_ascii=False,indent=2)+'\n')
    summary={'teachers':len(backup['data']['教師資料']),'content_rows':len(content),'research_rows':len(research),
             'career_rows':len(careers),'career_time_fields_filled':sum(bool(r['時間']) for r in careers),
             'month_policy':'只有原文提供月份才使用YYYY/MM；只有年份保留YYYY，不補月份。',
             'fields_filled':{key:sum(bool(str(r.get(key,'')).strip()) for r in research) for key in ['文章名','作者','期刊名','年份','DOI']},
             'crossref_records':sum(r.get('文獻資料來源','').startswith('https://api.crossref.org') for r in research),
             'merged_bilingual_references':merged,'incomplete_source_fragments':excluded,
             'additional_reviewed_merges':additional_merges,
             'restored_year_prefixes':restored_prefixes,
             'missing_authors':[{'teacher':r['教師ID'],'title':r['文章名'],'status':r['狀態']} for r in research if not r.get('作者')],
             'missing_publication_venue':[{'teacher':r['教師ID'],'title':r['文章名'],'type':r['類型'],'status':r['狀態']} for r in research if not r.get('期刊名')],
             'career_dates':date_audit}
    (ROOT/'data/structured_fields_report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ['merged_bilingual_references','additional_reviewed_merges','incomplete_source_fragments','restored_year_prefixes','missing_authors','missing_publication_venue','career_dates']},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
