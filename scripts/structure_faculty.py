"""Populate the Studio's bibliographic fields from citations and verified metadata."""
import copy
import difflib
import html
import json
import re
import unicodedata
import hashlib
from functools import lru_cache
from pathlib import Path

from bs4 import BeautifulSoup

from integrate_faculty import ROOT, OUTPUT, items, strip_bullet, norm, get_doi
from fetch_bibliography_metadata import fetch, doi_url, search_url, CACHE

YEAR=r'(?:19|20)\d{2}'
RANK=r'(?:SSCI|SCI\b|CSSCI|TSSCI|ABDC|ABS\b|ERIM|JCR|FT50|Scimago|Scimago|Q[1-4]\b)'


@lru_cache(maxsize=1)
def reviewed_metadata():
    path=ROOT/'data/bibliography_verified_metadata.json'
    return json.loads(path.read_text()) if path.exists() else {'records':[],'journal_lexicon':[],'citation_matches':[]}


def plain(value):
    return ' '.join(BeautifulSoup(html.unescape(str(value)),'html.parser').get_text(' ',strip=True).split())


def trim(value):
    return value.strip(' \t\n.,，。;；:：·*')


def remove_annotations(value):
    value=re.sub(r'\([^)]*(?:'+RANK+r'|[Cc]orresponding [Aa]uthor|[Cc]o-first [Aa]uthor|[Cc]itations?\s*\d)[^)]*\)','',value)
    value=re.sub(r'（[^）]*(?:'+RANK+r'|通訊作者|通讯作者|第一作者|合著者)[^）]*）','',value)
    return trim(value)


def title_similarity(a,b):
    a,b=norm(a),norm(b)
    if not a or not b:return 0
    if a in b or b in a:return min(len(a),len(b))/max(len(a),len(b))
    return difflib.SequenceMatcher(None,a,b).ratio()


def author_string(metadata):
    return '; '.join(' '.join(str(a.get(k,'')) for k in ['given','family']).strip() or a.get('name','') for a in metadata.get('author',[]))


def journal_lexicon(snapshot,backup):
    names=set(reviewed_metadata()['journal_lexicon'])
    for r in backup['data']['研究成果']:
        if r.get('期刊名'):names.add(r['期刊名'])
    for path in CACHE.glob('*.json'):
        for m in json.loads(path.read_text()).get('items',[]):
            names.update(m.get('container-title',[]))
    for profile in snapshot['profiles']:
        for lang in ['zh','en']:
            for work in items(profile[lang])[1]:
                s=BeautifulSoup(work['html'],'html.parser')
                for el in s.select('em,i'):
                    name=trim(el.get_text(' ',strip=True))
                    if len(name)>8 and not re.search(RANK,name):names.add(name)
                text=work['text']
                for match in re.finditer(r'([^,，;.。]{5,130})\s*[(（](?=[^)）]*(?:'+RANK+'))',text):
                    candidate=trim(match.group(1))
                    if not re.search(r'\d|authors?|role|[?]',candidate,re.I) and re.match(r'^(?:The\s+)?(?:Journal|International|Applied|Economic|Economica|Economies|Public|Marine|Aquaculture|Agriculture|Food|Earth|Humanities|Ocean|Singapore|Eastern|European|German|Open|Empirical|Research|Austrian)\b',candidate,re.I):names.add(candidate)
                for match in re.finditer(r'\[J(?:/OL)?\][.。]?\s*([^,，.。(（\d]+)',text,re.I):
                    names.add(trim(match.group(1)))
    extra='''Journal of Finance|The Journal of Finance|Journal of Financial Economics|Journal of Business Ethics|Journal of Real Estate Finance and Economics|Journal of Real Estate Finance & Economics|Ocean and Coastal Management|Ocean & Coastal Management|Economic Modelling|Food and Energy Security|Earth System and Environment|Singapore Economic Review|Journal of Agriculture and Food Research|Journal of Asian Business and Economic Studies|Marine Policy|Aquaculture|Economies|Agriculture|Heliyon|Sustainability|Public Choice|Economica|Applied Economics Letters|Applied Economic Letters|The Chinese Economy|Journal of Institutional Economics|Journal of Financial Economic Policy|Journal of Pension Economics and Finance|Journal of Development Studies|Journal of International Trade and Economic Development|Open Economies Review|Austrian Journal of Statistics|Economics Bulletin|Economic Systems|Economics-the open access open-assessment e-journal|Journal of International Economic Law|Journal of Balkan and Near Eastern Studies|Asian Journal of Applied Economics|Humanities & Social Science Communications|Humanities and Social Sciences Communications|Journal of Economic Behavior and Organization|Journal of Economic Behavior & Organization|Journal of Comparative Economics|Technological and Economic Development of Economy|Physics Letters A|Population and Development|South China Population|Rural Economy|China Public Administration Review|Health Economics|Scandinavian Journal of Public Health|Journal of Happiness Studies|European Journal of Health Economics|Economics & Human Biology|Economy and Human Biology|Social Science & Medicine|Journal of Regulatory Economics|World Development|Energy Economics|Finance Research Letters|Technological Forecasting and Social Change|Technological Forecasting & Social Change|Environmental Science and Pollution Research|Managerial Auditing Journal|Business Strategy and the Environment|Pacific-Basin Finance Journal|Pacific-basin Finance Journal|Land Economics|Journal of Environmental Quality|Journal of Futures Markets|The Journal of Futures Markets|China Economic Journal|Medical Research Archives|African Journal of Reproductive Health|Chaos, Solitons & Fractals|Physica A: Statistical Mechanics and its Applications|Journal of Financial Studies|Journal of Statistics and Data Science Education|Statistical Papers|Journal of Applied Statistics|The American Statistician|Accounting & Finance|Accounting and Finance|會計研究|会计研究|世界經濟|世界经济|經濟研究|经济研究|經濟學（季刊）|經濟學(季刊)|经济学(季刊)|中國農村經濟|中国农村经济|公共管理評論|公共管理评论|決策與諮詢|决策与咨询|人口與發展|人口与发展|勞動經濟研究|劳动经济研究|南方人口|農村經濟|农村经济|教育與經濟|教育与经济|探索|澳門研究|澳門經濟|澳门经济|Journal of Macau Economy|現代金融研究|现代金融研究|世界經濟文匯|世界经济文汇|當代財經|当代财经|財貿經濟|财贸经济|金融論壇|金融论坛|數量經濟技術經濟研究|数量经济技术经济研究|廣東社會科學|广东社会科学|金融經濟學研究|金融经济学研究|稅務研究|税务研究|財政研究|财政研究|財貿研究|财贸研究|經濟資料譯叢|经济资料译丛|人民論壇·學術前沿|人民论坛·学术前沿|系統工程理論與實踐|系统工程理论与实践|中國醫院|中国医院|中國衛生品質管理|中国卫生质量管理|智慧健康|智能健康|管理科學學報|管理科学学报|SSRN|arXiv'''
    names.update(extra.split('|'))
    names.update('城市情報|上海商業|中國市場|中國工業經濟|產經評論|產業經濟評論|金融市場研究|中國經濟問題|經濟學報|經濟評論|廣東工業大學學報（社會科學版）|21世纪经济报道|21世紀經濟報道|當代經濟管理|當代金融家|中國證券報|上海證券報|經濟日報|世界經濟研究|上海經濟研究|國際經貿探索|統計研究|南方經濟|學術研究|Journal of Economics, Business and Management|Academic Journal of Computing & Information Science|Academic Journal of Business & Management|Global Economics and Management Review|Journal of Modern Accounting and Auditing|Economic Vision|Frontiers of Finance and Economics|现代日本经济|新金融|亚太经济|Journal of Modern Japanese Economy|Journal of New Finance|The Journal of New Finance|Journal of Asia-Pacific Economy'.split('|'))
    names={re.sub(r'[,，]\s*$', '',remove_annotations(n)) for n in names}
    short={'Cities','Energy','Economies','Economica','Agriculture','Aquaculture','Sustainability','Mathematics','Heliyon','SSRN','arXiv'}
    names={n for n in names if n and (len(n)>9 or n in short or re.search(r'[\u3400-\u9fff]',n)) and not re.search(r'\b(?:with|Does|How|Why|Protection|Fiscal|Globalisation)\b.*\bJournal\b|[?]',n)}
    return sorted(names,key=len,reverse=True)


@lru_cache(maxsize=None)
def compiled_journal(name):
    pattern=re.escape(name).replace(r'\ ',r'\s+').replace(r'\&',r'(?:&|and)')
    return re.compile(r'(?<!\w)'+pattern+r'(?!\w)',re.I)


def journal_span(text,names):
    found=[]
    for name in names:
        for m in compiled_journal(name).finditer(text):
            if m.start()<6:continue
            if re.search(r'https?://\S*$',text[:m.start()]):continue
            # Avoid a short journal name matching one word inside a paper title.
            if len(name)<10 and not (m.end()==len(text) or re.match(r'\s*[”"’》」]*\s*[,，.(（\d]',text[m.end():])):continue
            found.append((len(name),m.start(),m.end(),text[m.start():m.end()]))
    if found:
        _,start,end,label=max(found,key=lambda x:(x[0],x[1]))
        return start,end,label
    # APA journal names follow a sentence boundary and precede volume/year information.
    text2=re.split(r'https?://|\bDOI\s*:',text,maxsplit=1,flags=re.I)[0]
    candidates=list(re.finditer(r'[.?。]\s+([A-Z][A-Za-z&’\- :]+?)(?=\s*[,，.]?\s*\d{1,4}(?:\(|\b)|\s*\((?:'+RANK+'))',text2))
    if candidates:
        m=candidates[-1]
        label=trim(m.group(1))
        if label.lower() not in {'january','february','march','april','may','june','july','august','september','october','november','december'}:
            return m.start(1),m.end(1),label
    return None


def split_authors_title(before):
    before=trim(before)
    before=re.sub(r'^\[[0-9]+\]\s*','',before)
    quoted=list(re.finditer(r'[“"‘「《<]([^”"’」》>]{8,})[”"’」》>]',before))
    quoted=[m for m in quoted if not re.search(r'\b(?:Impact|Evidence|The|on|from|of)\b',before[:m.start()].split(')')[-1])]
    if quoted:
        m=max(quoted,key=lambda m:len(m.group(1)))
        return trim(re.sub(r'[(（]?'+YEAR+r'(?:\d{2})?[)）]?','',before[:m.start()])),trim(m.group(1))
    chinese_colon=re.search(r'[:：]',before)
    first_year=re.search(YEAR,before)
    if chinese_colon and chinese_colon.start()<50 and (not first_year or chinese_colon.start()<first_year.start()) and re.search(r'[\u3400-\u9fff]',before[:chinese_colon.start()]):
        prefix=before[:chinese_colon.start()]
        if not re.search(r'\b(?:The|How|Does|Why|What)\b|影響|研究|分析',prefix):
            return trim(re.sub(YEAR+r'[.，,]?','',prefix)),trim(before[chinese_colon.end():])
    year=re.search(r'[(（]?'+YEAR+r'(?:\d{2})?(?!\d)[a-z]?[)）]?[.，,:：]?\s*',before)
    if year and (year.start()<160 or before[:year.start()].count(',')>1):
        author=trim(before[:year.start()])
        title=trim(before[year.end():])
        title=re.sub(r'^[（(](?:第一作者|通讯作者|通訊作者)[）)]\s*[,，]?\s*','',title)
        if author and title:return remove_annotations(author),title
    boundary=re.search(r'\.\s+(?=[A-Z][a-z]{2})',before)
    if boundary and boundary.start()>4:
        return remove_annotations(before[:boundary.start()]),trim(before[boundary.end():])
    # Chinese references commonly delimit the author list with a period.
    if re.search(r'[\u3400-\u9fff]',before):
        boundary=re.search(r'[.。]',before)
        if boundary and boundary.start()<100:return trim(before[:boundary.start()]),trim(before[boundary.end():])
    # Full-name author lists followed by a comma and a sentence-style title.
    pieces=re.split(r'[,，]\s*',before)
    authors=[]
    for i,piece in enumerate(pieces):
        words=re.findall(r'[A-Za-zÀ-ÿ]+',piece)
        name_like=bool(words) and len(words)<=7 and all(w[0].isupper() or w.lower() in {'and','et','al','de','van','von'} for w in words)
        if i and (not name_like or re.search(r'\b(?:The|Does|Do|Can|How|Why|Is|Are|An|A|Impact|Evidence|Corporate|Unintended|Reduced|Shushing|Corruption|Peer|School|Intergenerational)\b',piece)):
            return trim(', '.join(authors)),trim(', '.join(pieces[i:]))
        authors.append(piece)
    return '',before


def parse_reference(citation,teacher,names,status='已發表'):
    text=plain(strip_bullet(citation))
    result={'文章名':'','作者':'','期刊名':''}
    drafts=status in {'工作論文','審閱中','修改後重投'}
    span=journal_span(text,names)
    if drafts and not re.search(r'R\s*&\s*R|under review at|submitted to|revision.*(?:at|in)',text,re.I):span=None
    quoted=list(re.finditer(r'[“"‘「]([^”"’」]{10,})[”"’」]',text))
    if teacher['教師ID']=='ygwang':
        journal=re.search(r'《([^》]+)》',text)
        if journal:
            return {'文章名':trim(text[:journal.start()]),'作者':'王應貴','期刊名':journal[1]}
        if re.search(r'[\u3400-\u9fff]',text):
            title=re.sub(r'(?:'+YEAR+r'年\d{1,2}月\d{1,2}(?:日|日?\d{1,2}日)|\d{1,2}/\d{1,2}/'+YEAR+r')\s*$','',text)
            return {'文章名':trim(title),'作者':'王應貴','期刊名':'21世紀經濟報道'}
        if quoted:
            m=max(quoted,key=lambda m:len(m[1]));tail=text[m.end():]
            venue=re.split(r',\s*(?:December|January|February|March|April|May|June|July|August|September|October|November)',re.sub(r'^.*?presented at\s+','',tail,flags=re.I),maxsplit=1)[0]
            return {'文章名':trim(m[1]),'作者':'Yinggui Wang','期刊名':trim(venue)}
        if span:return {'文章名':trim(text[:span[0]]),'作者':'Yinggui Wang','期刊名':span[2]}
        return {'文章名':text,'作者':'','期刊名':''}
    if drafts and re.match(r'^(?:First Author|Solo Author|第一作者|獨立作者)',text,re.I):
        title=re.sub(r'^(?:First Author|Solo Author|第一作者|獨立作者)\s*[,，]\s*','',text,flags=re.I)
        title=re.split(r'[（(](?=[^）)]*[\u3400-\u9fff])',title,maxsplit=1)[0]
        return {'文章名':trim(title),'作者':teacher['英文姓名']+('' if re.match(r'^(?:Solo Author|獨立作者)',text,re.I) else ' et al.'),'期刊名':''}
    if drafts and not span:
        if quoted:
            m=max(quoted,key=lambda m:len(m.group(1)))
            result['文章名']=trim(m.group(1))
            prefix=trim(re.sub(r'[(（]?'+YEAR+r'[)）]?','',text[:m.start()]))
            if prefix and prefix not in {'第一作者','獨立作者','First Author','Solo Author'}:result['作者']=prefix
            co=re.search(r'\bwith\s+(.+?)(?=,\s*(?:under review|submitted|submitting)|[;；]|$)',text[m.end():],re.I)
            if co:result['作者']=teacher['英文姓名']+'（與 '+trim(co.group(1))+' 合作）'
        elif not re.search(r'\b'+YEAR+r'\b|^(?:First Author|Solo Author|第一作者|獨立作者)',text,re.I):
            initial_authors=re.match(r'^((?:[A-Z][a-z]+,\s*(?:[A-Z]\.\s*)+,\s*){2,})(.+)$',text)
            if initial_authors:return {'文章名':trim(initial_authors[2]),'作者':trim(initial_authors[1]),'期刊名':''}
            if re.search(r'\(Solo[- ]authored Paper\)',text,re.I):
                return {'文章名':trim(re.sub(r'\(Solo[- ]authored Paper\)','',text,flags=re.I)),'作者':teacher['英文姓名'],'期刊名':''}
            chinese_co=re.search(r'\s*[(（]合作作者[:：]\s*(.+?)(?:[;；].*)?[)）]\s*$',text)
            if chinese_co:return {'文章名':trim(text[:chinese_co.start()]),'作者':teacher['英文姓名']+'（與 '+trim(chinese_co[1])+' 合作）','期刊名':''}
            co=re.search(r'\s*[(（](?:with\b|與|与)(.+?)[)）]\s*$',text,re.I)
            result['文章名']=trim(text[:co.start()] if co else text)
            if co:result['作者']=teacher['英文姓名']+'（與 '+trim(re.sub(r'共同撰寫|共同撰写','',co.group(1)))+' 合作）'
        if result['文章名']:
            return result
    if teacher['教師ID']=='markusleibrecht':
        if span:
            start,end,journal=span
            result['文章名']=trim(text[:start])
            result['期刊名']=journal
            co=re.search(r'\bwith\s+(.+?)(?=\s*\((?:role|co-first)|\s*https?://|$)',text[end:],re.I)
            if co:result['作者']=teacher['英文姓名']+'（與 '+trim(co.group(1))+' 合作）'
            elif re.search(r'\bsole author\b',text,re.I):result['作者']=teacher['英文姓名']
        elif '. In:' in text:
            result['文章名']=trim(text.split('. In:')[0])
            co=re.search(r'\bwith\s+(.+?)(?=\s*\(|$)',text,re.I)
            result['作者']=teacher['英文姓名']+('; '+trim(co.group(1)) if co else '')
            result['期刊名']=trim(re.split(r',\s*\d|\bpp\.',text.split('. In:')[1])[0])
    elif span:
        start,end,journal=span
        result['期刊名']=journal
        if teacher['教師ID']=='luwang':
            result['文章名']=trim(re.sub(r'\s*'+YEAR+r'\s*[.,]?\s*$','',text[:start]))
        else:result['作者'],result['文章名']=split_authors_title(text[:start])
    else:
        result['作者'],result['文章名']=split_authors_title(text)
    # Chinese [J] markers delimit title and journal even in otherwise irregular references.
    marker=re.search(r'\[J(?:/OL)?\]',result['文章名'],re.I)
    if marker:result['文章名']=trim(result['文章名'][:marker.start()])
    if not span:
        book=re.search(r'《([^》]+)》',text)
        if book:
            result['文章名']=book.group(1)
            result['作者']=trim(re.sub(YEAR+r'[.，,]?','',text[:book.start()]))
            publisher=re.search(r'([^,，。.;]{2,45}出版社)',text[book.end():])
            if publisher:result['期刊名']=trim(publisher.group(1))
        # Quoted references often name their proceedings or publisher immediately after the title.
        if result['文章名']:
            end=text.find(result['文章名'])+len(result['文章名'])
            tail=text[end:].lstrip(' ”"’」》>.,，;；')
            tail=re.sub(r'^\(Chapter\s+\d+\)\s*','',tail,flags=re.I)
            if tail and not re.match(r'\(?\d|\(with\b',tail,re.I):
                venue=re.split(r'\b(?:ISSN|Vol\.|Volume|No\.|Number|https?://)\b|[;；]|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b|\b'+YEAR+r'\b',tail,maxsplit=1,flags=re.I)[0]
                if re.search(r'Journal|Conference|Proceedings|Symposium|Workshop|Press|Review|Centre|College|會刊|學報|專集|論文集',venue,re.I):result['期刊名']=trim(venue)
    result['文章名']=re.sub(r'^(?:First Author|Solo Author|獨立作者|第一作者)\s*[,，]\s*','',result['文章名'],flags=re.I)
    # Working-paper coauthor lists are not part of the article title.
    co=re.search(r'\s*[(（](?:with\b|與|与)(.+?)[)）]\s*$',result['文章名'],re.I)
    if co:
        result['文章名']=trim(result['文章名'][:co.start()])
        if not result['作者']:result['作者']=teacher['英文姓名']+'; '+trim(re.sub(r'共同撰寫|共同撰写','',co.group(1)))
    for k in result:result[k]=trim(result[k])
    return result


def cached(url):
    import hashlib
    p=CACHE/(hashlib.sha256(url.encode()).hexdigest()+'.json')
    if p.exists():return json.loads(p.read_text()).get('items',[])
    return [m for m in reviewed_metadata()['records'] if doi_url(m['DOI']).lower()==url.lower()]


def book_parts(citation,teacher,kind):
    text=plain(citation)
    result={}
    if teacher['教師ID']=='markusleibrecht':
        chapter=re.search(r'\bIn:\s*',text)
        if chapter:
            title,tail=text[:chapter.start()].rstrip('. '),text[chapter.end():]
            venue=re.split(r',\s*(?=[A-Z][a-z]+\s+[A-Z]\.)|\s*pp\.',tail,maxsplit=1)[0]
        else:
            title=re.split(r'\.\s+(?:Wifo|WIFO|Research Report|Austrian|Wiesbaden)|,\s*Vienna:',text,maxsplit=1)[0]
            tail=text[len(title):].lstrip(' .,')
            venue=re.split(r'[,，]\s*'+YEAR+r'\b|\s+with\s|\s+Editor with\s',tail,maxsplit=1)[0]
        co=re.search(r'\b(?:with|Editor with)\s+(.+?)(?=\s*\(|$)',text,re.I)
        return {'文章名':trim(title),'作者':teacher['英文姓名']+('（與 '+trim(co[1])+' 合作）' if co else ''),'期刊名':trim(venue)}
    publisher=re.search(r'([^,，。.;:：]{2,32}出版社)',text)
    if publisher:
        before=text[:publisher.start()]
        before=re.sub(r'[.。]\s*(?:北京|上海|武漢|南京|澳門)\s*[:：]?\s*$','',before)
        before=before.rstrip(' ,，:：')
        before=re.sub(r'[,，]\s*'+YEAR+r'\s*$','',before)
        authors,title=split_authors_title(before)
        quoted=re.search(r'《([^》]+)》',before)
        if quoted:
            title=quoted[1];authors=trim(re.sub(YEAR,'',before[:quoted.start()]))
        return {'文章名':trim(title),'作者':trim(authors),'期刊名':publisher[1]}
    return result


def author_matches(metadata,teacher):
    authors=author_string(metadata)
    if not authors:return True
    surname=teacher['英文姓名'].split()[-1].lower()
    if surname and surname in authors.lower():return True
    aliases=str.maketrans({'張':'张','陳':'陈','許':'许','劉':'刘','楊':'杨','蘇':'苏','趙':'赵','鄺':'邝','黃':'黄','華':'华','馬':'马','馮':'冯','龐':'庞'})
    cn=teacher['中文姓名'].translate(aliases)
    return len(cn)<=4 and cn in authors.translate(aliases)


def apply_metadata(row,parts,metadata,source):
    title=plain(metadata.get('title',[''])[0])
    if not title:return False
    sim=max(title_similarity(title,parts.get('文章名','')),title_similarity(title,row.get('文章名','')))
    citation=row.get('完整引用','')
    if sim<.72 and norm(title) not in norm(citation):return False
    if not row.get('文章名'):row['文章名']=title
    if author_string(metadata):row['作者']=author_string(metadata)
    if metadata.get('container-title') or metadata.get('publisher'):
        row['期刊名']=plain((metadata.get('container-title') or [metadata.get('publisher','')])[0])
    new_doi='https://doi.org/'+metadata['DOI']
    if row.get('DOI') and row['DOI'].lower()!=new_doi.lower():row['原引文DOI']=row['DOI']
    row['DOI']=new_doi
    date=next((metadata[k]['date-parts'][0] for k in ['published-print','published','issued','published-online'] if metadata.get(k,{}).get('date-parts')),[])
    if date:
        if row.get('年份') and str(row['年份'])!=str(date[0]):row['原引文年份']=row['年份']
        row['年份']=date[0]
        if len(date)>1:row['月份']=date[1]
    row['文獻資料來源']=doi_url(metadata['DOI'])
    return True


def run(search=False):
    backup=json.loads(OUTPUT.read_text())
    snapshot=json.loads((ROOT/'data/faculty_sources.json').read_text())
    teachers={p['教師ID']:p for p in backup['data']['教師資料']}
    overrides={ (x['teacher'],x['citation_sha256']):x for x in json.loads((ROOT/'data/bibliography_field_overrides.json').read_text()) }
    names=journal_lexicon(snapshot,backup)
    metadata_pool={}
    verified_by_doi={m['DOI'].lower():m for m in reviewed_metadata()['records']}
    verified_matches={(m['teacher'],m['citation_sha256']):m['DOI'].lower() for m in reviewed_metadata().get('citation_matches',[])}
    if search:
        for m in reviewed_metadata()['records']:metadata_pool[m['DOI']]=m
        for path in CACHE.glob('*.json'):
            for m in json.loads(path.read_text()).get('items',[]):
                if m.get('title') and m.get('DOI'):metadata_pool[m['DOI']]=m
    pooled_titles=[(m,norm(plain(m['title'][0]))) for m in metadata_pool.values()]
    results=[];queries=[]
    for index,row in enumerate(backup['data']['研究成果']):
        teacher=teachers[row['教師ID']]
        refs=[row.get('完整引用',''),row.get('原始引用（英文）',''),row.get('原始引用（中文）','')]
        parsed=[parse_reference(ref,teacher,names,row['狀態']) for ref in refs if ref]
        parts=max(parsed,key=lambda p:bool(p['文章名'])+2*bool(p['作者'])+2*bool(p['期刊名'])+(.25 if len(p['文章名'].split())>4 else 0)-(3 if any(len(word)>45 for word in p['文章名'].split()) else 0)) if parsed else {}
        if row['類型'] in {'專著','書籍章節'}:
            book=book_parts(row.get('完整引用',''),teacher,row['類型'])
            if book.get('文章名'):parts.update(book)
        override=overrides.get((row['教師ID'],hashlib.sha256(row.get('完整引用','').encode()).hexdigest()))
        if override:
            parts.update({k:v for k,v in override['fields'].items() if k in {'文章名','作者','期刊名'}})
            row.update(override['fields'])
            row['分欄人工核對來源']=override['basis']
        row['分欄原始引用']=row.get('完整引用','')
        used=False
        verified_doi=verified_matches.get((row['教師ID'],hashlib.sha256(row.get('完整引用','').encode()).hexdigest()))
        skip_metadata=bool(override and override.get('skip_metadata'))
        if verified_doi and not skip_metadata:
            metadata=verified_by_doi[verified_doi]
            used=apply_metadata(row,parts,metadata,doi_url(verified_doi))
        if row.get('DOI') and not used and not skip_metadata:
            for metadata in cached(doi_url(row['DOI'])):
                if apply_metadata(row,parts,metadata,doi_url(row['DOI'])):used=True;break
        if not used and search and not skip_metadata:
            query=parts.get('文章名','')
            if len(query)>12:
                url=search_url(query+' '+str(row.get('年份','')))
                candidates=list(cached(url))
                source_norm=norm(row.get('完整引用','')+' '+row.get('原始引用（英文）',''))
                query_norm=norm(query)
                candidates.extend(m for m,title_key in pooled_titles if title_key==query_norm or (len(title_key)>30 and title_key in source_norm))
                def preference(m):
                    journal=plain((m.get('container-title') or [''])[0])
                    score=4*title_similarity(journal,parts.get('期刊名',''))
                    if m.get('type')=='journal-article':score+=2
                    if m.get('DOI','').startswith('10.2139/') and parts.get('期刊名')!='SSRN':score-=4
                    return score
                candidates.sort(key=preference,reverse=True)
                for metadata in candidates:
                    meta_title=plain((metadata.get('title') or [''])[0])
                    if title_similarity(query,meta_title)<.92 and (len(norm(meta_title))<30 or norm(meta_title) not in source_norm):continue
                    if not author_matches(metadata,teacher):continue
                    meta_venue=plain((metadata.get('container-title') or [''])[0])
                    if parts.get('期刊名') and meta_venue and title_similarity(parts['期刊名'],meta_venue)<.65:continue
                    if apply_metadata(row,parts,metadata,url):used=True;break
        for key in ['文章名','作者','期刊名']:
            if not row.get(key) and parts.get(key):row[key]=parts[key]
        if override:
            for key in override.get('preserve_fields',[]):row[key]=override['fields'][key]
        if not row.get('文獻資料來源'):row['文獻資料來源']=row.get('來源網址','')+'（原始引用分欄）'
        if not row.get('DOI') and len(parts.get('文章名',''))>12:
            queries.append({'index':index,'teacher':row['教師ID'],'query':parts['文章名']+' '+str(row.get('年份',''))})
        results.append({'index':index,'teacher':row['教師ID'],'source':row.get('完整引用',''),
                        'title':row.get('文章名',''),'authors':row.get('作者',''),'journal':row.get('期刊名',''),
                        'year':row.get('年份',''),'doi':row.get('DOI',''),'metadata':used})
    (ROOT/'work/bibliography').mkdir(parents=True,exist_ok=True)
    (ROOT/'work/bibliography/parsed.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'work/bibliography/queries.json').write_text(json.dumps(queries,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'work/bibliography/candidate_backup.json').write_text(json.dumps(backup,ensure_ascii=False,indent=2)+'\n')
    print('ROWS',len(results),'METADATA',sum(r['metadata'] for r in results))
    for key in ['title','authors','journal','year','doi']:print(key,sum(bool(r[key]) for r in results))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--search',action='store_true');a=p.parse_args();run(a.search)
