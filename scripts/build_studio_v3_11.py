"""Build the standalone 3.11 editor from the preserved uploaded 3.10 HTML."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'FOF_Profile_Studio_v3_10.html').read_text()
def replace(old,new,count=1):
 global s
 assert s.count(old)==count,(old[:100],s.count(old),count)
 s=s.replace(old,new)
replace('工具 v3.10','工具 v3.11')
s=s.replace('Studio 3.10','Studio 3.11').replace('Template 3.10','Template 3.11').replace("appVersion:'3.10'","appVersion:'3.11'").replace('FOF_Profile_Common_Style_v3_10.css','FOF_Profile_Common_Style_v3_11.css')
replace("'獎項','專長與軟件','其他公開資訊'","'獎項','媒體報道','專長與軟件','其他公開資訊'")
replace("'獎項':'Awards'","'獎項':'Awards','媒體報道':'Media Coverage'")
replace("  if(txt(p['相片網址'])&&!web(p['相片網址']))bad.push(id+' 相片網址須使用http或https');","   photoInputs(p).forEach((url,j)=>{if(!web(url))bad.push(id+' 第'+(j+1)+'個相片網址須使用http或https');});")
replace("  if(txt(p['資料狀態'])!=='已核對')notes.push(p['中文姓名']+'：資料仍待核對');\n  if(!d['內容明細'].some(r=>r['教師ID']===id&&r['模組']==='個人簡介'&&txt(r['內容'])))notes.push(p['中文姓名']+'：未填個人簡介');",'')
replace(' return{bad,notes:[...new Set(notes)]};'," return{bad,notes:d['教師資料'].flatMap(p=>reviewMessages(p['教師ID'],d))};")
replace(" return out+'\\n#fof-faculty-profile .fp-citation", " return out+FEATURE_CSS+'\\n#fof-faculty-profile .fp-citation")
replace("'時間':en?careerDate(txt(r['時間（英文）'])||r['時間'],'en'):careerDate(r['時間'])","'時間':en?careerDate(txt(r['時間（英文）'])||r['時間'],'en'):careerDate(r['時間'])") # Assert legacy bilingual dates stay intact.
replace("list(mod(name)),'fp-extra-'+(++n)","(timelineModules.includes(name)?timelineHTML(mod(name),lang):list(mod(name))),'fp-extra-'+(++n)")
replace("(web(p['相片網址'])?'':' fp-no-photo')","(photoURLs(p).length?'':' fp-no-photo')")
replace("(web(p['相片網址'])?'<div class=\"fp-photo-frame\"><img class=\"fp-portrait\" src=\"'+esc(web(p['相片網址']))+'\" alt=\"'+esc(name)+'\" /></div>':'')","galleryHTML(p,name,lang)")
replace("(mentor&&setting('顯示導師標籤','是')==='是'?'<div class=\"fp-supervision\"><span class=\"fp-supervisor-tag\">'+esc(mentor)+'</span></div>':'')", "recognitionHTML(p,mentor,lang)")
replace(" if(enableNav&&nav.length)result+=", " if(photoURLs(p).length>1)result+='\\n<script>\\n'+PROFILE_SLIDESHOW+'\\n<\\/script>';\n if(enableNav&&nav.length)result+=")
features=(ROOT/'scripts/studio_v3_11_features.js').read_text()
replace("const STORAGE_KEY=",features+"\nconst STORAGE_KEY=")
replace("'行政職務（英文）','導師標籤（英文）'],","'行政職務（英文）','導師標籤（英文）','亮點標籤','亮點標籤（英文）','核對指紋','確認時間','最後編輯時間'],")
replace("if(canonicalModule(r['模組'])==='學術工作經驗')r['時間']=careerDate(r['時間']);","if(canonicalModule(r['模組'])==='學術工作經驗'||timelineModules.includes(canonicalModule(r['模組'])))r['時間']=careerDate(r['時間']);")
replace("function changed(){fileLabel=", "function changed(id){if(id)markEditing(id);fileLabel=")
replace("function replaceData(input,label,keep=true){const ready=shape(input);if(keep)remember();", "function replaceData(input,label,keep=true){const ready=shape(input);document.activeElement?.blur();if(keep)remember();")
replace("renderEditor();changed();return id;","renderEditor();changed(id);return id;")
replace("renderEditor(data[kind].length-1);changed();return", "renderEditor(data[kind].length-1);changed(id);return")
replace("function removeRow(kind,index){remember();data[kind].splice(index,1);renderEditor();changed();}","function removeRow(kind,index){remember();const id=data[kind][index]['教師ID'];data[kind].splice(index,1);renderEditor();changed(id);}")
replace("renderEditor(index);changed();}","renderEditor(index);changed(data[kind][index]['教師ID']);}")
replace("?Number(value):value;changed();if(kind===", "?Number(value):value;changed(kind==='共用設定'?null:data[kind][index]['教師ID']);if(kind===")
replace("const check=validate(data);errors=check.bad;warnings=[...languageNotes($('teacherSelect').value,lang),...check.notes];", "const check=validate(data);errors=check.bad;warnings=reviewMessages($('teacherSelect').value);renderReview();")
replace("(errors.length?errors:warnings).slice(0,10)","(errors.length?errors:warnings)")
replace("($('navToggle').checked?'含章節定位程式':'不含JavaScript')","(currentCode.includes('<script>')?'含章節定位／輪播程式':'不含JavaScript')")
replace("時間（共用；學術經驗用YYYY/MM）","時間（共用；YYYY、YYYY/MM 或 YYYY/MM/DD）")
replace("'來源網址','資料狀態'];","'來源網址'];")
replace("+'<div class=\"field-heading wide\">共用資料（兩個版本同步）</div>'+common.map(k=>f(k,{readonly:k==='教師ID',choices:k==='資料狀態'?['待核對','已核對']:undefined})).join('')", "+f('亮點標籤',{long:true,label:'中文亮點標籤（選填；每行一個，例如 全球前2%頂尖科學家）'})+f('亮點標籤（英文）',{long:true,label:'English highlights（optional; one per line）'})+'<div class=\"field-heading wide\">共用資料（兩個版本同步）</div>'+common.map(k=>f(k,{readonly:k==='教師ID',long:k==='相片網址',label:k==='相片網址'?'相片網址（每行一個；一張顯示靜態相，多張自動輪播）':undefined})).join('')")
replace("個人簡介每段一項。","個人簡介每段一項。研究項目、學術服務與指導、獎項及媒體報道以日期／內容兩欄顯示；沒有日期可留空，項目只按「排序」排列，不按日期重排。")
replace("canonicalModule(data['內容明細'][Number(t.dataset.index)]?.['模組'])==='學術工作經驗'","['學術工作經驗',...timelineModules].includes(canonicalModule(data['內容明細'][Number(t.dataset.index)]?.['模組']))")
# Preserve day precision in dates where the original provides it.
replace("const ym=(original,year,month)=>{const m=Number(month);return m>=1&&m<=12?year+'/'+String(m).padStart(2,'0'):original;};","const ym=(original,year,month,day)=>{const m=Number(month),d=Number(day);return m>=1&&m<=12?year+'/'+String(m).padStart(2,'0')+(day&&d>=1&&d<=31?'/'+String(d).padStart(2,'0'):''):original;};")
replace(r"(\d{1,2})\s*月(?:\s*\d{1,2}\s*日)?/g,ym",r"(\d{1,2})\s*月(?:\s*(\d{1,2})\s*日)?/g,ym")
replace(r"(\d{1,2})(?:[./-]\d{1,2})?(?!\d)/g,ym",r"(\d{1,2})(?:[./-](\d{1,2}))?(?!\d)/g,ym")
replace('const STORAGE_KEY=', 'const STORAGE_KEY=')
review_bar='<div class="review-current"><strong id="reviewStatus"></strong><div class="actions"><button id="editTeacherButton">編輯資料</button><button id="confirmTeacherButton" class="primary">確認資料</button></div></div><details id="reviewOverview"><summary>教師核對進度 · <span id="reviewCounts"></span></summary><div id="reviewTable"></div></details>'
replace('<p id="sourceLabel" class="muted"></p>',review_bar+'<p id="sourceLabel" class="muted"></p>')
dialog='''<dialog id="confirmationDialog"><h2 id="confirmationTitle">確認資料</h2><p class="muted">自動檢查會列出缺欄、項目數、日期及數字差異；翻譯含義及原站差異請人手核對。</p><div id="confirmationIssues"></div><p id="confirmationBlock" class="error" hidden>請先補齊姓名、職稱或修正無效相片網址，才可確認。</p><label id="confirmationAcknowledgementLabel"><input id="confirmationAcknowledgement" type="checkbox"> 我已核對以上提示，確認差異或留空為正確／不適用。</label><div class="actions"><button id="confirmReviewButton" class="primary">確認無誤</button><button id="cancelReviewButton">返回編輯</button></div></dialog>'''
replace('<footer>',dialog+'\n<footer>')
ui_css='''\n.review-current{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;margin:16px 0;padding:12px;background:#f4f8f5;border:1px solid #cbdcd1;border-radius:6px}.review-current .actions{margin:0}#reviewOverview{margin:14px 0}#reviewTable{overflow:auto;max-height:420px;margin-top:12px}#reviewTable table{width:100%;border-collapse:collapse;font-size:12px}#reviewTable th,#reviewTable td{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid #dfe8e2}#reviewTable td:last-child{min-width:170px}.review-badge{white-space:nowrap;padding:3px 7px;border-radius:4px;background:#fff3d8;color:#795915}.review-done{background:#e2f4e9;color:#126045}.review-editing{background:#e7f0fc;color:#245487}#checks{max-height:280px;overflow:auto}#confirmationDialog{width:min(760px,94vw);max-height:90vh}#confirmationIssues{max-height:50vh;overflow:auto;padding:0 8px 8px}#confirmationIssues li{margin-bottom:9px}#confirmationAcknowledgementLabel{display:block;margin-top:15px}\n'''
replace('</style></head><body>\n<header>',ui_css+'</style></head><body>\n<header>')
bindings="""
$('editTeacherButton').addEventListener('click',()=>startEditing($('teacherSelect').value));
$('confirmTeacherButton').addEventListener('click',()=>requestConfirmation($('teacherSelect').value));
$('reviewTable').addEventListener('click',e=>{const b=e.target.closest('[data-review-action]');if(!b)return;if(b.dataset.reviewAction==='edit')startEditing(b.dataset.id);else{refreshTeachers(b.dataset.id);renderEditor();requestConfirmation(b.dataset.id);}});
$('confirmationAcknowledgement').addEventListener('change',()=>{$('confirmReviewButton').disabled=!$('confirmationAcknowledgement').checked;});
$('confirmReviewButton').addEventListener('click',completeConfirmation);
$('cancelReviewButton').addEventListener('click',()=>{$('confirmationDialog').close();});
"""
replace("window.addEventListener('beforeunload'",bindings+"\nwindow.addEventListener('beforeunload'")
replace("window.FOFProfileStudio={readExcel", "window.FOFProfileStudio={reviewIssues,reviewState,reviewFingerprint,confirmed,startEditing,requestConfirmation,photoURLs,tagValues,readExcel")
replace('若出406，可關閉章節定位，再複製HTML/CSS版測試。','多相輪播包含播放程式，關閉章節定位後仍會保留；請先在測試頁預覽。')
(ROOT/'FOF_Profile_Studio_v3_11.html').write_text(s)
print('Built standalone Studio 3.11',len(s))
