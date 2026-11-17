"""Exercise the supplied, unmodified Studio with the integrated backup."""
import collections
import difflib
import json
import os
import re
import threading
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from integrate_faculty import INPUT, OUTPUT, ROOT, items, norm, prepare_content, content_text, leading_date


def main():
    integrated=json.loads(OUTPUT.read_text())
    original=json.loads(INPUT.read_text())
    snapshot=json.loads((ROOT/'data/faculty_sources.json').read_text())
    data=integrated['data']
    structured=json.loads((ROOT/'data/structured_fields_report.json').read_text())
    assert len(data['教師資料'])==43
    assert {p['教師ID'].lstrip('_') for p in data['教師資料']}=={p['id'] for p in snapshot['profiles']}
    assert integrated['templateCSS']==original['templateCSS']
    assert data['共用設定']==original['data']['共用設定']
    assert {p['教師ID'] for p in original['data']['教師資料']} <= {p['教師ID'] for p in data['教師資料']}
    assert all(not isinstance(value,(dict,list)) for rows in data.values() for row in rows for value in row.values())
    source_works=0
    source_content=0
    preserved_edits=[]
    for profile in snapshot['profiles']:
        tid=next(p['教師ID'] for p in data['教師資料'] if p['教師ID'].lstrip('_')==profile['id'])
        for lang in ['zh','en']:
            for module,source_rows in items(profile[lang])[0].items():
                key=('原始經歷（中文）' if lang=='zh' else '原始經歷（英文）') if module=='學術工作經驗' else ('內容' if lang=='zh' else '內容（英文）')
                targets=[r.get(key,'') for r in data['內容明細'] if r['教師ID']==tid and r['模組']==module]
                corpus=norm(' '.join(targets))
                for source in prepare_content(source_rows,module):
                    text=content_text(source)
                    if norm(text) not in corpus:
                        score=max((difflib.SequenceMatcher(None,norm(text),norm(t)).ratio() for t in targets),default=0)
                        assert score>.95,(tid,lang,module,'missing content',text)
                        preserved_edits.append({'teacher':tid,'language':lang,'module':module,'source':text})
                    source_content+=1
            refs='\n'.join(r.get('完整引用','')+'\n'+r.get('原始引用（中文）' if lang=='zh' else '原始引用（英文）','') for r in data['研究成果'] if r['教師ID']==tid)
            refs+='\n'+'\n'.join(x['citation'] for x in structured['incomplete_source_fragments'] if x['teacher']==tid)
            for work in items(profile[lang])[1]:
                assert norm(work['text']) in norm(refs), (tid,lang,'missing reference',work['text'])
                source_works+=1
    assert len(data['研究成果'])==696
    assert all(r.get('文章名','').strip() for r in data['研究成果'])
    assert all(r['狀態']=='工作論文' for r in data['研究成果'] if not r.get('作者'))
    careers=[r for r in data['內容明細'] if r['模組']=='學術工作經驗']
    assert len(careers)==125
    date_pattern=r'(?:19|20)\d{2}(?:/(?:0[1-9]|1[0-2]))?(?: – (?:(?:19|20)\d{2}(?:/(?:0[1-9]|1[0-2]))?|至今|Present))?'
    for row in careers:
        assert row['時間']
        for key in ['時間','時間（英文）']:
            if row.get(key):assert re.fullmatch(date_pattern,row[key]),row
    for tid,expected in [('markusleibrecht','2020/09 – 2023/08'),('qiangli','2025/01 – 至今'),('kellyliang','2022/08 – 至今')]:
        assert any(r['教師ID']==tid and r['時間']==expected for r in careers),(tid,expected)
    for row in data['研究成果']:
        assert not re.match(r'^(?:19|20)\d{2}',row.get('作者','')),row
        assert row.get('期刊名') not in {'Volume','International','Productivity'},row
        if 'Spatial Dependencies in the Relationship' in row['文章名']:
            assert row['DOI']=='https://doi.org/10.1016/j.econmod.2025.107442'
            assert row['期刊名']=='Economic Modelling' and 'Markus Leibrecht' in row['作者']
        if row['文章名'].startswith('Shushing the press'):
            assert row['DOI']=='https://doi.org/10.1177/14034948231178879'
        if row['教師ID']=='evakhong' and row['排序'] in [36,37]:
            assert row['類型']=='會議論文' and not row['DOI']
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,directory=str(ROOT),**kwargs)
        def log_message(self,*args):
            pass
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}/'
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
        page=browser.new_page(accept_downloads=True,viewport={'width':1440,'height':1000})
        runtime_errors=[]
        page.on('pageerror',lambda error:runtime_errors.append(str(error)))
        page.route('**/*',lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        page.goto(base+'FOF_Profile_Studio_v3_10.html',wait_until='domcontentloaded')
        page.locator('#restoreInput').set_input_files(str(OUTPUT))
        page.wait_for_function('window.FOFProfileStudio.getData()["教師資料"].length===43')
        assert page.locator('#teacherSelect option').count()==43
        validation=page.evaluate('FOFProfileStudio.validate(FOFProfileStudio.getData())')
        assert not validation['bad'],validation['bad']
        generated=page.evaluate('''() => {
          const s=FOFProfileStudio;
          return s.getData()['教師資料'].flatMap(t=>['zh','en'].map(lang=>({id:t['教師ID'],lang,html:s.generate(t['教師ID'],lang)})));
        }''')
        assert len(generated)==86
        for result in generated:
            soup=BeautifulSoup(result['html'],'html.parser')
            assert len(soup.select('#fof-faculty-profile'))==1
            teacher=next(t for t in data['教師資料'] if t['教師ID']==result['id'])
            assert soup.select_one('h1').get_text()==teacher['英文姓名' if result['lang']=='en' else '中文姓名']
            assert len(soup.select('.fp-paper'))==sum(r['教師ID']==result['id'] for r in data['研究成果'])
            research=[r for r in data['研究成果'] if r['教師ID']==result['id']]
            assert len(soup.select('.fp-paper h4'))==len(research)
            title_key='文章名（英文）' if result['lang']=='en' else '文章名（中文）'
            assert collections.Counter(norm(el.get_text(' ',strip=True)) for el in soup.select('.fp-paper h4'))==collections.Counter(norm(r.get(title_key) or r['文章名']) for r in research)
            assert not soup.select('.fp-citation')
            assert len(soup.select('.fp-authors'))==sum(bool(r.get('作者')) for r in research)
            assert len(soup.select('.fp-journal'))==sum(bool(r.get('期刊名')) for r in research)
            assert len(soup.select('#fp-experience .fp-year'))==sum(r['教師ID']==result['id'] and bool(r.get('內容（英文）' if result['lang']=='en' else '內容')) for r in careers)
            assert 'undefined' not in result['html'] and '[object Object]' not in result['html']
        with page.expect_download() as downloaded:
            page.locator('#backupButton').click()
        roundtrip_path=ROOT/'work/studio_roundtrip.json'
        downloaded.value.save_as(str(roundtrip_path))
        roundtrip=json.loads(roundtrip_path.read_text())
        assert roundtrip['templateCSS']==original['templateCSS']
        assert roundtrip['data']==data
        assert {k:len(v) for k,v in roundtrip['data'].items()}=={k:len(v) for k,v in data.items()}
        page.locator('#restoreInput').set_input_files(str(roundtrip_path))
        page.wait_for_function('document.getElementById("notice").textContent.includes("studio_roundtrip.json")')
        assert page.evaluate('FOFProfileStudio.getData()')==roundtrip['data']
        page.locator('details.import-panel > summary').click()
        with page.expect_download(timeout=120000) as downloaded:
            page.locator('#batchButton').click()
        zip_path=ROOT/'FOF_Profile_Codes_All_Faculty_2026-11-17.zip'
        downloaded.value.save_as(str(zip_path))
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.testzip() is None
            text_files=[name for name in archive.namelist() if name.endswith('_ClickrAdmin.txt')]
            assert len(text_files)==86
        assert not runtime_errors,runtime_errors
        assert page.evaluate('FOFProfileStudio.persist()') is True
        report={'teachers':43,'source_language_pages':86,'source_research_citations_accounted_for':source_works,
                'content_rows':len(data['內容明細']),'research_rows':len(data['研究成果']),
                'career_rows_with_dates':len(careers),'all_research_titles_rendered_in_native_fields':True,
                'structured_bibliography_fields':structured['fields_filled'],
                'source_fragments_excluded_with_audit':structured['incomplete_source_fragments'],
                'source_content_items_accounted_for':source_content,'preserved_original_edit_variants':preserved_edits,
                'studio_validation_errors':validation['bad'],'studio_validation_notes':validation['notes'],
                'generated_profiles':len(generated),'json_export_reimport_passed':True,
                'batch_zip_code_files':len(text_files),'original_styles_preserved':True,'original_settings_preserved':True,
                'runtime_errors':runtime_errors}
        (ROOT/'data/integration_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        (ROOT/'work/generated_profiles.json').write_text(json.dumps(generated,ensure_ascii=False))
        print(json.dumps({k:v for k,v in report.items() if k!='studio_validation_notes'},ensure_ascii=False,indent=2))
        print('STUDIO NOTES',len(validation['notes']))
        browser.close()
    server.shutdown()


if __name__=='__main__':
    main()
