// Bundled inside the standalone Studio by build_studio_v3_11.py.
const timelineModules=['研究項目','學術服務與指導','獎項','媒體報道'];
const reviewFields=new Set(['資料狀態','核對指紋','確認時間','最後編輯時間']);
const FEATURE_CSS=`
#fof-faculty-profile .fp-highlights{display:flex;flex-wrap:wrap;gap:7px;margin:14px 0 0;padding:0;list-style:none;}
#fof-faculty-profile .fp-highlight{display:inline-block;padding:5px 10px;border:1px solid #b18b45;border-radius:5px;background:#faf5e9;color:#70521e;font-size:12px;font-weight:600;line-height:1.6;}
#fof-faculty-profile .fp-dated-list{display:grid;grid-template-columns:110px minmax(0,1fr);gap:14px 18px;}
#fof-faculty-profile .fp-dated-list .fp-entry-body{min-width:0;overflow-wrap:anywhere;}
#fof-faculty-profile .fp-gallery{margin-bottom:18px;}
#fof-faculty-profile .fp-slideshow{position:relative;aspect-ratio:1/1.08;overflow:hidden;}
#fof-faculty-profile .fp-slideshow .fp-slide{position:absolute;inset:0;opacity:0;transition:opacity .5s ease;pointer-events:none;}
#fof-faculty-profile .fp-slideshow .fp-slide.is-active{opacity:1;}
#fof-faculty-profile .fp-slideshow .fp-portrait{width:100%;height:100%;object-fit:contain;margin:0;background:#f5f7f5;}
#fof-faculty-profile .fp-gallery-controls{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:7px;margin-top:9px;}
#fof-faculty-profile .fp-gallery-controls button{font:inherit;font-size:12px;line-height:1.5;background:#fff;color:#245d49;border:1px solid #b5c9bd;border-radius:4px;padding:4px 9px;}
#fof-faculty-profile .fp-gallery-controls button:focus-visible{outline:2px solid #b18b45;outline-offset:2px;}
#fof-faculty-profile .fp-gallery-status{font-size:12px;color:#56665d;}
@media(max-width:570px){#fof-faculty-profile .fp-dated-list{grid-template-columns:85px minmax(0,1fr);gap:12px 10px;}#fof-faculty-profile .fp-profile:has(.fp-gallery){display:block;}#fof-faculty-profile .fp-gallery{max-width:260px;margin:0 auto 18px;}}
@media(prefers-reduced-motion:reduce){#fof-faculty-profile .fp-slideshow .fp-slide{transition:none;}}
`;
const PROFILE_SLIDESHOW='('+function(){
 const root=document.getElementById('fof-faculty-profile');
 if(!root)return;
 root.querySelectorAll('.fp-gallery').forEach(gallery=>{
  const slides=[...gallery.querySelectorAll('.fp-slide')],previous=gallery.querySelector('[data-gallery="previous"]'),next=gallery.querySelector('[data-gallery="next"]'),toggle=gallery.querySelector('[data-gallery="toggle"]'),status=gallery.querySelector('.fp-gallery-status');
  if(slides.length<2)return;
  const en=root.lang==='en',motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  let index=0,paused=motion.matches,hovered=false,focused=false,timer;
  function show(value,manual=false){index=(value+slides.length)%slides.length;slides.forEach((slide,i)=>{slide.classList.toggle('is-active',i===index);slide.setAttribute('aria-hidden',String(i!==index));});status.textContent=(index+1)+' / '+slides.length;status.setAttribute('aria-live',manual?'polite':'off');}
  function schedule(){clearInterval(timer);toggle.textContent=paused?(en?'Play':'播放'):(en?'Pause':'暫停');toggle.setAttribute('aria-label',paused?(en?'Play photo slideshow':'播放相片輪播'):(en?'Pause photo slideshow':'暫停相片輪播'));toggle.setAttribute('aria-pressed',String(paused));if(!paused&&!hovered&&!focused&&!document.hidden)timer=setInterval(()=>show(index+1),4500);}
  previous.onclick=()=>{show(index-1,true);schedule();};next.onclick=()=>{show(index+1,true);schedule();};toggle.onclick=()=>{paused=!paused;schedule();};
  gallery.addEventListener('mouseenter',()=>{hovered=true;schedule();});gallery.addEventListener('mouseleave',()=>{hovered=false;schedule();});
  gallery.addEventListener('focusin',()=>{focused=true;schedule();});gallery.addEventListener('focusout',e=>{if(!gallery.contains(e.relatedTarget)){focused=false;schedule();}});
  gallery.addEventListener('keydown',e=>{if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();show(index+(e.key==='ArrowLeft'?-1:1),true);schedule();}});
  document.addEventListener('visibilitychange',schedule);motion.addEventListener('change',e=>{if(e.matches)paused=true;schedule();});show(0);schedule();
 });
}.toString()+')();';
function photoInputs(p){return txt(p['相片網址']).split(/\r?\n/).map(txt).filter(Boolean);}
function photoURLs(p){return [...new Set(photoInputs(p).map(web).filter(Boolean))];}
function tagValues(p,lang){return txt(p[lang==='en'?'亮點標籤（英文）':'亮點標籤']).split(/\r?\n/).map(txt).filter(Boolean);}
function highlightHTML(p,lang){const tags=tagValues(p,lang);return tags.length?'<ul class="fp-highlights" aria-label="'+(lang==='en'?'Highlights':'榮譽亮點')+'">'+tags.map(t=>'<li class="fp-highlight">'+esc(t)+'</li>').join('')+'</ul>':'';}
function galleryHTML(p,name,lang){
 const photos=photoURLs(p),en=lang==='en';if(!photos.length)return '';
 if(photos.length===1)return '<div class="fp-photo-frame"><img class="fp-portrait" src="'+esc(photos[0])+'" alt="'+esc(name)+'" /></div>';
 return '<div class="fp-gallery" role="region" aria-roledescription="'+(en?'carousel':'輪播')+'" aria-label="'+esc(name)+(en?' photos':'相片')+'"><div class="fp-photo-frame fp-slideshow">'+photos.map((url,i)=>'<div class="fp-slide'+(!i?' is-active':'')+'" aria-hidden="'+String(i!==0)+'"><img class="fp-portrait" src="'+esc(url)+'" alt="'+esc(name)+(en?' — photo ':' — 相片 ')+(i+1)+'" /></div>').join('')+'</div><div class="fp-gallery-controls"><button type="button" data-gallery="previous" aria-label="'+(en?'Previous photo':'上一張相片')+'">‹</button><span class="fp-gallery-status" aria-live="off">1 / '+photos.length+'</span><button type="button" data-gallery="next" aria-label="'+(en?'Next photo':'下一張相片')+'">›</button><button type="button" data-gallery="toggle" aria-pressed="false">'+(en?'Pause':'暫停')+'</button></div></div>';
}
function timelineHTML(rows,lang){
 if(!rows.length)return '';
 return '<div class="fp-career fp-dated-list">'+rows.map(r=>'<div class="fp-year"'+(!txt(r['時間'])?' aria-hidden="true"':'')+'>'+esc(careerDate(r['時間'],lang))+'</div><div class="fp-entry-body">'+para(r['內容'])+(txt(r['補充'])&&!txt(r['補充']).includes('待確認')?'<small class="fp-entry-note">'+para(r['補充'])+'</small>':'')+(web(r['連結'])?'<span class="fp-optional-link">'+link(r['連結'],lang==='en'?'Related link ↗':'相關連結 ↗')+'</span>':'')+'</div>').join('')+'</div>';
}
function reviewFingerprint(p,d=data){
 const stable=row=>Object.fromEntries(Object.keys(row).sort().filter(k=>!reviewFields.has(k)&&txt(row[k])!=='').map(k=>[k,row[k]]));
 const raw=JSON.stringify([stable(p),d['內容明細'].filter(r=>r['教師ID']===p['教師ID']).map(stable),d['研究成果'].filter(r=>r['教師ID']===p['教師ID']).map(stable)]);
 let a=2166136261,b=5381;for(let i=0;i<raw.length;i++){a=Math.imul(a^raw.charCodeAt(i),16777619);b=Math.imul(b,33)^raw.charCodeAt(i);}
 return 'v1:'+raw.length+':'+(a>>>0).toString(16)+':'+(b>>>0).toString(16);
}
function confirmed(p,d=data){return p['資料狀態']==='已核對'&&txt(p['核對指紋'])===reviewFingerprint(p,d);}
function reviewState(p,d=data){return confirmed(p,d)?'已核對':p['資料狀態']==='編輯中'||p['資料狀態']==='已核對'&&txt(p['核對指紋'])?'編輯中':'待核對';}
function markEditing(id){const p=data['教師資料'].find(p=>p['教師ID']===id);if(!p)return;p['資料狀態']='編輯中';p['核對指紋']='';p['最後編輯時間']=new Date().toISOString();}
function reviewIssues(id,d=data){
 const p=d['教師資料'].find(p=>p['教師ID']===id);if(!p)return [];
 const issues=[],add=(section,detail,blocking=false)=>issues.push({section,detail,blocking});
 for(const key of ['中文姓名','英文姓名','職稱','職稱（英文）'])if(!txt(p[key]))add('基本資料','未填'+key,true);
 for(const key of ['電郵','相片網址'])if(!txt(p[key]))add('基本資料','未填'+key+'（可確認為不適用）');
 photoInputs(p).forEach((url,i)=>{if(!web(url))add('相片','第'+(i+1)+'個相片網址無效',true);});
 if(Boolean(txt(p['行政職務']))!==Boolean(txt(p['行政職務（英文）'])))add('基本資料','行政職務只有一種語言，請補譯或確認留空');
 const cn=txt(p['職稱']),en=txt(p['職稱（英文）']).toLowerCase();
 if(cn&&en){const rank=cn.includes('助理教授')?'assistant':cn.includes('副教授')?'associate':cn.includes('教授')?'professor':cn.includes('講師')?'lecturer':'';if(rank&&((rank==='assistant'&&!en.includes('assistant'))||(rank==='associate'&&!en.includes('associate'))||(rank==='professor'&&(!en.includes('professor')||/assistant|associate/.test(en)))||(rank==='lecturer'&&!en.includes('lecturer'))))add('基本資料','中英文職稱層級可能不一致：'+cn+'／'+p['職稱（英文）']);}
 if(tagValues(p,'zh').length!==tagValues(p,'en').length)add('亮點標籤','中英文標籤數量不同；未填的語言不會顯示標籤');
 const rows=d['內容明細'].filter(r=>r['教師ID']===id),read=(r,key,lang)=>lang==='en'?txt(r[key+'（英文）'])||(r['語言']==='英文'?txt(r[key]):''):txt(r[key]);
 const compareDate=value=>careerDate(value,'en').replaceAll('Present','至今').replace(/\s/g,'');
 const numbers=value=>[...new Set((txt(value).match(/\d[\d,]*(?:\.\d+)?%?/g)||[]).map(v=>v.replaceAll(',','')))].sort().join(', ');
 for(const module of moduleNames){
  const selected=rows.filter(r=>canonicalModule(r['模組'])===module),zh=selected.filter(r=>read(r,'內容','zh')).length,english=selected.filter(r=>read(r,'內容','en')).length;
  if(module==='個人簡介'&&!zh&&!english)add(module,'中英文均未提供，可確認為不適用');
  else if(zh!==english)add(module,'中英文項目數不同（中文 '+zh+'／英文 '+english+'），請核對缺譯或分段');
  for(const r of selected){
   const label='第'+(r['排序']||selected.indexOf(r)+1)+'項';
   if(txt(r['時間'])&&txt(r['時間（英文）'])&&compareDate(r['時間'])!==compareDate(r['時間（英文）']))add(module,label+'中英文日期不同：'+r['時間']+'／'+r['時間（英文）']);
   const a=read(r,'內容','zh'),b=read(r,'內容','en');
   if(a&&b&&numbers(a)!==numbers(b))add(module,label+'中英內容的數字不同，請人手核對（中：'+(numbers(a)||'無')+'；英：'+(numbers(b)||'無')+'）');
   if(txt(r['補充']).includes('待確認')||txt(r['補充（英文）']).includes('待確認'))add(module,label+'補充欄標示待確認');
  }
 }
 const works=d['研究成果'].filter(r=>r['教師ID']===id);
 for(const r of works){const label='第'+r['排序']+'項「'+txt(r['文章名']||r['完整引用']).slice(0,42)+'」';if(!txt(r['作者']))add('研究成果',label+'未提供作者');if(!txt(r['期刊名'])&&['已發表','已接受'].includes(r['狀態']))add('研究成果',label+'未提供刊物／出版社');if(txt(r['DOI'])&&!doiURL(r['DOI']))add('研究成果',label+'DOI格式無法識別');if(txt(r['原引文年份'])&&txt(r['原引文年份'])!==txt(r['年份']))add('研究成果',label+'原引文年份 '+r['原引文年份']+' 與書目年份 '+r['年份']+' 不同');}
 if(works.some(r=>txt(r['作者資料說明'])))add('研究成果','部分作者資料附有待補／署名範圍說明，請核對相關成果的來源紀錄');
 return issues;
}
function reviewMessages(id,d=data){const p=d['教師資料'].find(p=>p['教師ID']===id);if(!p||confirmed(p,d))return [];const issues=reviewIssues(id,d);return issues.length?issues.map(i=>p['中文姓名']+' · '+i.section+'：'+i.detail):[p['中文姓名']+'：'+reviewState(p,d)+'；請檢查基本資料、已填版塊及研究成果後按「確認資料」。'];}
function renderReview(){
 const selected=data['教師資料'].find(p=>p['教師ID']===$('teacherSelect').value);
 $('reviewStatus').textContent=selected?(selected['中文姓名']+' · '+reviewState(selected)+(confirmed(selected)&&selected['確認時間']?' · '+new Date(selected['確認時間']).toLocaleString('zh-Hant'):'')):'請先選擇老師';
 $('editTeacherButton').disabled=!selected;$('confirmTeacherButton').disabled=!selected||Boolean(selected&&confirmed(selected));
 const counts={待核對:0,編輯中:0,已核對:0};data['教師資料'].forEach(p=>counts[reviewState(p)]++);
 $('reviewCounts').textContent='已核對 '+counts['已核對']+' · 編輯中 '+counts['編輯中']+' · 待核對 '+counts['待核對'];
 $('reviewTable').innerHTML='<table><thead><tr><th scope="col">老師</th><th scope="col">狀態</th><th scope="col">待核對部分</th><th scope="col">操作</th></tr></thead><tbody>'+data['教師資料'].map(p=>{const done=confirmed(p),parts=[...new Set(reviewIssues(p['教師ID']).map(i=>i.section))];return '<tr data-review-teacher="'+esc(p['教師ID'])+'"><th scope="row">'+esc(p['中文姓名'])+'</th><td><span class="review-badge '+(done?'review-done':p['資料狀態']==='編輯中'?'review-editing':'')+'">'+reviewState(p)+'</span></td><td>'+esc(done?'已確認':parts.join('、')||'基本資料及已填內容')+'</td><td><button data-review-action="edit" data-id="'+esc(p['教師ID'])+'">編輯資料</button> <button data-review-action="confirm" data-id="'+esc(p['教師ID'])+'"'+(done?' disabled':'')+'>確認資料</button></td></tr>';}).join('')+'</tbody></table>';
}
function startEditing(id){markEditing(id);activeTab='basic';refreshTeachers(id);renderEditor();persist();message('已開始編輯此老師資料；完成後請按「確認資料」。');}
let confirmingTeacher='';
function requestConfirmation(id){
 const p=data['教師資料'].find(p=>p['教師ID']===id);if(!p)return;
 confirmingTeacher=id;const issues=reviewIssues(id),blocking=issues.some(i=>i.blocking);
 $('confirmationTitle').textContent='確認資料 · '+p['中文姓名'];
 $('confirmationIssues').innerHTML=issues.length?'<ul>'+issues.map(i=>'<li><strong>'+esc(i.section)+'</strong>：'+esc(i.detail)+'</li>').join('')+'</ul>':'<p>未發現缺欄、日期或數字差異，請核對中英文內容後確認。</p>';
 $('confirmationAcknowledgement').checked=false;$('confirmationAcknowledgement').disabled=blocking;$('confirmationBlock').hidden=!blocking;
 $('confirmReviewButton').disabled=issues.length>0;$('confirmationAcknowledgementLabel').hidden=!issues.length||blocking;
 if(!$('confirmationDialog').open)$('confirmationDialog').showModal();
}
function completeConfirmation(){
 const p=data['教師資料'].find(p=>p['教師ID']===confirmingTeacher);if(!p)return;
 const issues=reviewIssues(confirmingTeacher);if(issues.some(i=>i.blocking)||issues.length&&!$('confirmationAcknowledgement').checked)return;
 p['資料狀態']='已核對';p['確認時間']=new Date().toISOString();p['核對指紋']=reviewFingerprint(p);
 $('confirmationDialog').close();refreshTeachers(confirmingTeacher);renderEditor();persist();message('已確認 '+p['中文姓名']+' 的資料；此老師的待核對提示已隱藏。再次修改資料會重新標示為編輯中。');
}
