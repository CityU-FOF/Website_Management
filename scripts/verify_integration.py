"""Exercise the supplied, unmodified Studio with the integrated backup."""
import collections
import difflib
import json
import os
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
    assert len(data['教師資料'])==43
    assert {p['教師ID'].lstrip('_') for p in data['教師資料']}=={p['id'] for p in snapshot['profiles']}
    assert integrated['templateCSS']==original['templateCSS']
    assert data['共用設定']==original['data']['共用設定']
    assert {p['教師ID'] for p in original['data']['教師資料']} <= {p['教師ID'] for p in data['教師資料']}
    source_works=0
    source_content=0
    preserved_edits=[]
    for profile in snapshot['profiles']:
        tid=next(p['教師ID'] for p in data['教師資料'] if p['教師ID'].lstrip('_')==profile['id'])
        for lang in ['zh','en']:
            for module,source_rows in items(profile[lang])[0].items():
                targets=[r.get('內容' if lang=='zh' else '內容（英文）','') for r in data['內容明細'] if r['教師ID']==tid and r['模組']==module]
                corpus=norm(' '.join(targets))
                for source in prepare_content(source_rows,module):
                    text=content_text(source)
                    if module=='學術工作經驗':
                        text=leading_date(text)[1]
                    if norm(text) not in corpus:
                        score=max((difflib.SequenceMatcher(None,norm(text),norm(t)).ratio() for t in targets),default=0)
                        assert score>.95,(tid,lang,module,'missing content',text)
                        preserved_edits.append({'teacher':tid,'language':lang,'module':module,'source':text})
                    source_content+=1
            refs='\n'.join(r.get('原始引用（中文）' if lang=='zh' else '原始引用（英文）','') for r in data['研究成果'] if r['教師ID']==tid)
            for work in items(profile[lang])[1]:
                assert norm(work['text']) in norm(refs), (tid,lang,'missing reference',work['text'])
                source_works+=1
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
            assert 'undefined' not in result['html'] and '[object Object]' not in result['html']
        with page.expect_download() as downloaded:
            page.locator('#backupButton').click()
        roundtrip_path=ROOT/'work/studio_roundtrip.json'
        downloaded.value.save_as(str(roundtrip_path))
        roundtrip=json.loads(roundtrip_path.read_text())
        assert roundtrip['templateCSS']==original['templateCSS']
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
            text_files=[name for name in archive.namelist() if name.endswith('_ClickrAdmin.txt')]
            assert len(text_files)==86
        assert not runtime_errors,runtime_errors
        assert page.evaluate('FOFProfileStudio.persist()') is True
        report={'teachers':43,'source_language_pages':86,'source_research_citations_accounted_for':source_works,
                'content_rows':len(data['內容明細']),'research_rows':len(data['研究成果']),
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
