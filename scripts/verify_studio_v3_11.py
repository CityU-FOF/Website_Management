"""Exercise 3.11 UI, review lifecycle, dates, gallery, and lossless JSON/XLSX exports."""
import collections
import json
import os
import threading
import zipfile
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BACKUP=ROOT/'FOF_Profile_Backup_All_Faculty_2026-11-18.json'
WORK=ROOT/'work/studio_v3_11'
TARGETS=['研究項目','學術服務與指導','獎項','媒體報道']

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    original=json.loads((ROOT/'FOF_Profile_Backup_All_Faculty_2026-11-17.json').read_text())
    backup=json.loads(BACKUP.read_text());data=backup['data']
    assert data['研究成果']==original['data']['研究成果']
    assert backup['templateCSS']==original['templateCSS']
    assert data['共用設定']==original['data']['共用設定']
    assert len(data['教師資料'])==43
    assert all(not isinstance(v,(list,dict)) for rows in data.values() for row in rows for v in row.values())
    for module in TARGETS[:3]:
        old=[r for r in original['data']['內容明細'] if r['模組']==module]
        new=[r for r in data['內容明細'] if r['模組']==module]
        assert len(old)==len(new)
        assert [(r['教師ID'],r['排序']) for r in old]==[(r['教師ID'],r['排序']) for r in new]
        for a,b in zip(old,new):
            assert a['內容']==b['版塊日期原文（中文）']
            assert a.get('內容（英文）','')==b['版塊日期原文（英文）']
    media=[r for r in data['內容明細'] if r['模組']=='媒體報道']
    assert len(media)==30 and [r['時間'] for r in media][-2:]==['2012','2019']
    assert all(r['教師ID']=='arman' for r in media)
    assert [r for r in data['內容明細'] if r['模組']=='學術工作經驗']==[r for r in original['data']['內容明細'] if r['模組']=='學術工作經驗']
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}/'
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
        page.goto(base+'FOF_Profile_Studio_v3_11.html',wait_until='domcontentloaded')
        page.locator('#restoreInput').set_input_files(str(BACKUP));page.wait_for_function('FOFProfileStudio.getData()["教師資料"].length===43')
        assert not page.evaluate('FOFProfileStudio.validate(FOFProfileStudio.getData()).bad')
        assert page.locator('[data-review-teacher]').count()==43
        # Every teacher is editable and every non-empty section keeps its original order in both languages.
        generated=page.evaluate('''()=>FOFProfileStudio.getData()['教師資料'].flatMap(t=>['zh','en'].map(lang=>({id:t['教師ID'],lang,html:FOFProfileStudio.generate(t['教師ID'],lang)})))''')
        for result in generated:
            soup=BeautifulSoup(result['html'],'html.parser')
            teacher=next(t for t in data['教師資料'] if t['教師ID']==result['id'])
            assert len(soup.select('.fp-paper h4'))==sum(r['教師ID']==result['id'] for r in data['研究成果'])
            assert len(soup.select('.fp-highlight'))==len((teacher.get('亮點標籤（英文）' if result['lang']=='en' else '亮點標籤') or '').splitlines())
            assert len(soup.select('.fp-photo-choice[type="radio"]'))==(3 if result['id']=='arman' else 0)
            assert len(soup.select('.fp-portrait'))==len(teacher['相片網址'].splitlines())
            for section in soup.select('.fp-section'):
                heading=section.select_one('h3').get_text()
                labels={'研究項目':'Research Projects','學術服務與指導':'Academic Service and Supervision','獎項':'Awards','媒體報道':'Media Coverage'}
                module=next((m for m in TARGETS if heading==(labels[m] if result['lang']=='en' else m)),None)
                if not module:continue
                rows=sorted([r for r in data['內容明細'] if r['教師ID']==result['id'] and r['模組']==module and (r.get('內容（英文）') if result['lang']=='en' else r['內容'])],key=lambda r:r['排序'])
                def norm(v):return ''.join(v.split())
                assert [norm(el.get_text()) for el in section.select('.fp-entry-body')]==[norm((r.get('內容（英文）') if result['lang']=='en' else r['內容'])+(r.get('補充（英文）','') if result['lang']=='en' else r.get('補充',''))+('Related link ↗' if result['lang']=='en' else '相關連結 ↗')*bool(r.get('連結'))) for r in rows],(result['id'],module,result['lang'])
                assert len(section.select('.fp-year'))==len(rows)
        # Check actual positions at the profile-card grid breakpoint where the labels diverged.
        layout = browser.new_page()
        layout.route('**/*', lambda route: route.abort())
        for result in generated:
            if result['id'] not in {'_adriancheung', 'cclee'}:
                continue
            layout.set_content(result['html'], wait_until='domcontentloaded')
            for width in (320, 390, 550, 640, 1440):
                layout.set_viewport_size({'width': width, 'height': 900})
                assert layout.locator('.fp-recognition > .fp-supervisor-tag + .fp-highlights').count() == 1
                assert layout.evaluate('''() => {
                  const mentor = document.querySelector('.fp-supervisor-tag').getBoundingClientRect();
                  const highlight = document.querySelector('.fp-highlight');
                  const badge = highlight.getBoundingClientRect();
                  const style = getComputedStyle(highlight);
                  const contact = document.querySelector('.fp-contact').getBoundingClientRect();
                  const profile = document.querySelector('.fp-profile').getBoundingClientRect();
                  return badge.height > 0 && Math.abs(badge.x - mentor.x) < 1
                    && badge.top >= mentor.bottom && badge.top - mentor.bottom <= 10
                    && badge.bottom < contact.top && badge.right <= profile.right
                    && style.backgroundColor === 'rgb(248, 229, 180)'
                    && style.borderLeftWidth === '3px' && style.borderRightWidth === '1px'
                    && style.borderLeftColor === 'rgb(181, 130, 43)' && style.color === 'rgb(84, 54, 4)'
                    && style.fontWeight === '700' && style.borderRadius === '6px';
                }'''), (result['id'], result['lang'], width)
            if result['id'] == '_adriancheung':
                layout.set_viewport_size({'width': 550, 'height': 900})
                layout.locator('.fp-profile').screenshot(path=str(WORK / f"highlights_{result['lang']}.png"))
        layout.close()
        # Real UI: specific bilingual conflicts are shown on confirmation and disappear only after acknowledgement.
        page.evaluate('FOFProfileStudio.selectTeacher("arman")');page.locator('#confirmTeacherButton').click()
        assert page.locator('#confirmationDialog').is_visible()
        assert '中英文日期不同' in page.locator('#confirmationIssues').inner_text()
        assert '媒體報道' in page.locator('#confirmationIssues').inner_text()
        assert page.locator('#confirmReviewButton').is_disabled()
        page.locator('#confirmationAcknowledgement').check();page.locator('#confirmReviewButton').click()
        assert page.evaluate('FOFProfileStudio.confirmed(FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman"))')
        assert page.locator('#checks').is_hidden()
        assert '已核對' in page.locator('#reviewStatus').inner_text()
        # Selecting another teacher and back does not invalidate confirmation.
        page.evaluate('FOFProfileStudio.selectTeacher("cclee");FOFProfileStudio.selectTeacher("arman")')
        assert page.locator('#checks').is_hidden()
        page.locator('input[data-key="電話"]').fill('8590 9999');page.wait_for_function('FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman")["資料狀態"]==="編輯中"')
        page.wait_for_function('document.getElementById("reviewStatus").textContent.includes("編輯中")')
        assert page.locator('#checks').is_visible()
        page.locator('#confirmTeacherButton').click();page.locator('#confirmationAcknowledgement').check();page.locator('#confirmReviewButton').click()
        with page.expect_download() as download:page.locator('#backupButton').click()
        roundtrip=WORK/'reviewed_roundtrip.json';download.value.save_as(str(roundtrip));saved=json.loads(roundtrip.read_text())
        assert saved['data']==page.evaluate('FOFProfileStudio.getData()')
        page.reload();page.wait_for_function('FOFProfileStudio.getData()["教師資料"].length===43')
        page.evaluate('FOFProfileStudio.selectTeacher("arman")');assert page.locator('#checks').is_hidden()
        page.locator('#restoreInput').set_input_files(str(roundtrip));page.wait_for_function('document.getElementById("notice").textContent.includes("reviewed_roundtrip")');assert page.locator('#checks').is_hidden()
        # Media editing, optional highlights, invalid URL handling, and post-confirm edits all use the ordinary editor.
        page.evaluate('FOFProfileStudio.selectModule("媒體報道")');assert page.locator('.record').count()==30
        page.locator('[data-action="addRow"]').click();assert page.locator('.record').count()==31
        assert page.evaluate('FOFProfileStudio.reviewState(FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman"))')=='編輯中'
        page.evaluate('FOFProfileStudio.selectTab("basic")')
        page.locator('[data-key="亮點標籤"]').fill('測試亮點\n第二個標籤');page.locator('[data-key="亮點標籤（英文）"]').fill('Test highlight\nSecond highlight')
        assert page.evaluate('new DOMParser().parseFromString(FOFProfileStudio.generate("arman","zh"),"text/html").querySelectorAll(".fp-highlight").length')==2
        page.locator('[data-key="相片網址"]').fill('javascript:alert(1)')
        assert page.evaluate('FOFProfileStudio.validate(FOFProfileStudio.getData()).bad.length')>0
        page.evaluate('FOFProfileStudio.restoreData('+json.dumps(backup,ensure_ascii=False)+',"reset fixture")')
        assert page.evaluate('FOFProfileStudio.photoURLs(FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman")).length')==3
        # No fabricated months and exact day precision are retained by both date renderers.
        assert page.evaluate('FOFProfileStudio.careerDate("2024年3月5日 – 2025年4月6日","en")')=='2024/03/05 – 2025/04/06'
        assert page.evaluate('FOFProfileStudio.careerDate("2024 – 至今","en")')=='2024 – Present'
        # Multi-photo output must work even with JavaScript disabled and chapter links enabled.
        assert page.locator('#navToggle').is_checked()
        arman_codes={lang:page.evaluate('(lang)=>FOFProfileStudio.generate("arman",lang)',lang) for lang in ('zh','en')}
        for code in arman_codes.values():
            markup=BeautifulSoup(code,'html.parser')
            assert not markup.select('script')
            assert not any(key.lower().startswith('on') for element in markup.find_all(True) for key in element.attrs)
            assert len(markup.select('.fp-gallery img'))==3 and not markup.select('.fp-gallery a,.fp-gallery form')
            assert len(markup.select('.fp-photo-choice[checked] + .fp-gallery-panel .fp-slide'))==1
            assert markup.select_one('.fp-native-nav a[href="#fp-publications"]')
        page.evaluate('FOFProfileStudio.selectTeacher("arman")')
        preview=page.frame_locator('#preview')
        preview.locator('label.fp-photo-arrow[data-photo-direction="next"]:visible').click()
        assert preview.locator('.fp-photo-choice').nth(1).is_checked()
        assert preview.locator('.fp-slide:visible').count()==1
        page.locator('#navToggle').focus();page.locator('#navToggle').press('Space');page.wait_for_timeout(400)
        assert not page.locator('#navToggle').is_checked()
        with_nav_off=BeautifulSoup(page.evaluate('FOFProfileStudio.generate("arman","en")'),'html.parser')
        assert len(with_nav_off.select('.fp-slide'))==3 and not with_nav_off.select('script,.fp-nav')
        solo=BeautifulSoup(page.evaluate('FOFProfileStudio.generate("cclee","en")'),'html.parser')
        assert len(solo.select('.fp-portrait'))==1 and not solo.select('script,.fp-gallery')
        # Exercise the same renderer for another teacher with two and four photo URLs.
        other_teacher_codes=page.evaluate(r'''() => {
            const studio = FOFProfileStudio, backup = studio.backupObject();
            const teachers = backup.data['教師資料'];
            const other = teachers.find(teacher => teacher['教師ID'] === 'cclee');
            const photos = studio.photoURLs(other).concat(studio.photoURLs(teachers.find(teacher => teacher['教師ID'] === 'arman')));
            return [2,4].map(count => {
                other['相片網址'] = photos.slice(0,count).join('\n');
                studio.restoreData(backup, 'multi-photo test', false);
                return studio.generate('cclee','en');
            });
        }''')
        gallery=browser.new_page(java_script_enabled=False, viewport={'width':1200,'height':950})
        photo_sources=json.loads((ROOT/'data/studio_v3_11_source_additions.json').read_text())
        photos={url:WORK/f'arman_photo_{i}.img' for i,url in enumerate(photo_sources['arman_gallery']['zh']['photo_urls'])}
        def route_photo(route):
            file=photos.get(route.request.url)
            if file and file.exists():route.fulfill(path=str(file),content_type='image/jpeg' if file.read_bytes().startswith(b'\xff\xd8') else 'image/png')
            else:route.abort()
        gallery.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route_photo(route))
        layouts=[('arman_en',1200,3,arman_codes['en']),('arman_zh',390,3,arman_codes['zh'])]
        layouts.extend((f'cclee_{count}',390,count,code) for count,code in zip((2,4),other_teacher_codes))
        for name,width,count,code in layouts:
            file=WORK/f'{name}_cms_preview.html'
            # On the CMS, a fragment link can resolve against the homepage rather than the profile.
            file.write_text('<!doctype html><meta charset="UTF-8"><base href="/">'+code)
            gallery.set_viewport_size({'width':width,'height':950})
            url=base+file.relative_to(ROOT).as_posix()
            gallery.goto(url,wait_until='load')
            assert gallery.evaluate('document.documentElement.scrollWidth<=innerWidth')
            group=gallery.locator('.fp-gallery')
            assert group.evaluate('(el)=>el.scrollWidth<=el.clientWidth')
            choices=group.locator('.fp-photo-choice')
            assert choices.count()==count and choices.first.is_checked()
            arrows=group.locator('.fp-photo-arrow:visible')
            assert arrows.all_text_contents()==['←','→']
            assert group.locator('.fp-photo-arrow.is-disabled:visible').get_attribute('data-photo-direction')=='previous'
            for direction,indices in [('next',range(1,count)),('previous',range(count-2,-1,-1))]:
                for index in indices:
                    group.locator(f'label.fp-photo-arrow[data-photo-direction="{direction}"]:visible').click()
                    assert gallery.url==url and choices.nth(index).is_checked()
                    assert group.locator('.fp-slide:visible').count()==1
                    assert group.locator('.fp-slide').nth(index).is_visible()
                    assert arrows.all_text_contents()==['←','→']
                disabled=group.locator('.fp-photo-arrow.is-disabled:visible')
                assert disabled.count()==1 and disabled.get_attribute('data-photo-direction')==direction
            choices.first.focus()
            choices.first.press('ArrowRight')
            assert choices.nth(1).is_checked() and gallery.url==url
            if name.startswith('arman'):
                group.screenshot(path=str(WORK/f'{name}_gallery.png'))
        gallery.close()
        # Export final deliverables from a clean fixture, including all newly introduced fields in XLSX.
        page.evaluate('FOFProfileStudio.restoreData('+json.dumps(backup,ensure_ascii=False)+',"final fixture")')
        page.evaluate('FOFProfileStudio.selectTeacher("arman")');page.locator('#confirmTeacherButton').click();page.locator('#confirmationAcknowledgement').check();page.locator('#confirmReviewButton').click()
        page.evaluate('''()=>{const d=FOFProfileStudio.getData(),i=d['共用設定'].findIndex(r=>r['設定']==='論文區高度');FOFProfileStudio.updateField('共用設定',i,'值',540);}''')
        assert page.evaluate('FOFProfileStudio.confirmed(FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman"))')
        before_excel=page.evaluate('FOFProfileStudio.getData()')
        with page.expect_download() as download:page.locator('#exportExcel').click()
        excel=WORK/'studio_v3_11.xlsx';download.value.save_as(str(excel))
        page.locator('#excelInput').set_input_files(str(excel));page.wait_for_function('document.getElementById("notice").textContent.includes("Excel")')
        restored=page.evaluate('FOFProfileStudio.getData()')
        compact=lambda d:{key:[{k:v for k,v in row.items() if v not in ['',None]} for row in rows] for key,rows in d.items()}
        assert compact(restored)==compact(before_excel)
        assert page.evaluate('FOFProfileStudio.confirmed(FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman"))')
        assert len([r for r in restored['內容明細'] if r['模組']=='媒體報道'])==30
        assert next(t for t in restored['教師資料'] if t['教師ID']=='arman')['相片網址']==next(t for t in data['教師資料'] if t['教師ID']=='arman')['相片網址']
        tampered=json.loads(json.dumps(saved));next(t for t in tampered['data']['教師資料'] if t['教師ID']=='arman')['電話']='8590 0000'
        page.evaluate('FOFProfileStudio.restoreData('+json.dumps(tampered,ensure_ascii=False)+',"externally changed backup")')
        assert page.evaluate('FOFProfileStudio.reviewState(FOFProfileStudio.getData()["教師資料"].find(t=>t["教師ID"]==="arman"))')=='編輯中'
        page.evaluate('FOFProfileStudio.restoreData('+json.dumps(backup,ensure_ascii=False)+',"final export")')
        with page.expect_download(timeout=120000) as download:
            page.locator('details.import-panel > summary').click();page.locator('#batchButton').click()
        zip_path=ROOT/'FOF_Profile_Codes_All_Faculty_2026-11-18.zip';download.value.save_as(str(zip_path))
        with zipfile.ZipFile(zip_path) as z:
            assert z.testzip() is None;assert len([n for n in z.namelist() if n.endswith('_ClickrAdmin.txt')])==86
            for lang in ('ZH','EN'):
                code=BeautifulSoup(z.read(f'arman_{lang}_ClickrAdmin.txt').decode(),'html.parser')
                assert len(code.select('.fp-gallery img'))==3 and not code.select('script,.fp-gallery a')
                assert code.select_one('.fp-native-nav a[href="#fp-publications"]')
                assert code.find('h3',string='Media Coverage' if lang=='EN' else '媒體報道')
            assert '確認資料' not in z.read('arman_ZH_ClickrAdmin.txt').decode()
        assert page.evaluate('FOFProfileStudio.persist()')
        assert not errors,errors
        report={'studio_version':'3.11.2','teachers':43,'generated_bilingual_pages':len(generated),'media_rows':30,'gallery_photos':3,
                'dates_and_undated_items_keep_source_order':True,'original_research_and_career_rows_preserved':True,
                'optional_bilingual_highlights':True,'bilingual_highlights_aligned_below_supervisor':True,
                'approved_gold_highlight_appearance_preserved':True,
                'review_confirmation_and_edit_invalidation':True,'specific_bilingual_diagnostics':True,
                'review_survives_json_restore_and_reload':True,'gallery_switches_with_javascript_disabled_and_homepage_base':True,
                'gallery_previous_next_and_keyboard_work_with_two_three_and_four_photos':True,
                'single_photo_static_multi_photo_gallery':True,'multi_photo_output_script_free_with_or_without_chapter_links':True,
                'json_and_xlsx_roundtrip':True,'batch_zip_code_files':86,'local_storage_saved':True,'mobile_no_horizontal_overflow':True,'runtime_errors':errors}
        (ROOT/'data/studio_v3_11_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));browser.close()
    server.shutdown()

if __name__=='__main__':main()
