"""Convert the official bilingual source snapshot into the supplied Studio schema.

Source HTML is parsed as data. Nothing in a fetched page is executed.
"""
import collections
import copy
import difflib
import html
import json
import re
import unicodedata
from urllib.parse import unquote, urlsplit
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'FOF_Profile_Backup_adriancheung_2026-11-17.json'
OUTPUT = ROOT / 'FOF_Profile_Backup_All_Faculty_2026-11-17.json'
MODULES = ['個人簡介', '學歷', '學術工作經驗', '研究方向', '教學科目', '研究項目', '學術服務與指導', '會議與演講', '獎項', '專長與軟件', '其他公開資訊']
BLOCKS = {'article', 'div', 'section', 'p', 'li', 'ul', 'ol', 'table', 'tbody', 'thead', 'tr', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'}


def clean(value):
    return re.sub(r'[ \t\r\f\v\xa0]+', ' ', str(value).replace('\u200b', '').replace('\ufeff', '')).strip()


def norm(value):
    return re.sub(r'[^\w\u3400-\u9fff]', '', unicodedata.normalize('NFKC', value).lower()).replace('学','學')


def blocks(markup):
    root = BeautifulSoup(markup, 'html.parser').select_one('article')
    result = []

    def visit(node):
        inline = []

        def flush():
            if not inline:
                return
            fragment = BeautifulSoup(''.join(str(x) for x in inline), 'html.parser')
            for br in fragment.select('br'):
                br.replace_with('\n')
            text = clean(fragment.get_text('', strip=False))
            text = '\n'.join(clean(line) for line in text.splitlines() if clean(line))
            if text:
                bold = ''.join(x.get_text('', strip=True) for x in fragment.select('strong,b'))
                result.append({'index': len(result), 'text': text, 'html': str(fragment),
                               'bold': len(norm(bold)) >= len(norm(text)) * .8,
                               'heading': node.name.startswith('h') and node.name[1:].isdigit(),
                               'links': [(a.get('href', ''), clean(a.get_text(' ', strip=True))) for a in fragment.select('a[href]')]})
            inline.clear()

        for child in node.children:
            if isinstance(child, Tag) and child.name in {'script', 'style', 'title', 'meta', 'link'}:
                continue
            if isinstance(child, Tag) and child.name in BLOCKS:
                flush()
                visit(child)
            else:
                inline.append(child)
        flush()

    visit(root)
    return result


HEADINGS = {}


def labels(kind, *values):
    for value in values:
        HEADINGS[norm(value)] = kind


labels('contact', '聯絡資料', '聯絡方式', '聯絡資訊', '聯係方式', 'Contact Details', 'Contact Information')
labels('個人簡介', '簡介', '個人簡介', 'Biography', 'Bibliography', 'Short Introduction')
labels('學歷', '學歷', '教育背景', 'Education', 'Academic Qualifications', 'Academic Qualifications 教育经历')
labels('學術工作經驗', '學術工作經驗', '工作經驗', '工作經歷', '主要工作經歷', '相關工作經驗', '學術職務', '訪問學者經歷', '訪問經歷',
       'Work Experience', 'Working Experience', 'Academic Work Experience', 'Academic Work Experiences', 'Professional Experience',
       'Professional Experiences', 'Visiting Scholar Experience', 'Employment', 'Academic Employment', 'Work Experience 工作经验', 'Full-time', '全職', 'Visiting')
labels('研究方向', '研究方向', '研究領域', '主要研究領域', '主要研究方向', '研究興趣', 'Research Area', 'Research Areas', 'Research Interests',
       'Research Fields', 'Research Area / Research Interests', 'Research Areas 研究领域', 'Research and Teaching Fields')
labels('教學科目', '教學科目', '教学科目', '教學領域', '教學', '教授課程', '擔任課程', '主要教授科目', '教學經驗', '教學工作經驗',
       'Teaching Areas', 'Teaching Subjects', 'Teaching Interests', 'Teaching', 'Teaching experience', 'Courses to teach', 'Main teaching subjects', 'Teaching Areas 教学科目')
labels('研究項目', '研究項目', '科研項目', '參與課題', '主持課題', '主要項目經驗', '科研專案經歷', '研究資助', '主持/參與課題',
       '主持國家級科研專案', '主持或參加的研究课题', 'Research Project', 'Research Projects', 'Projects', 'Project', 'Research Grants', 'Research Fundings')
labels('學術服務與指導', '學術服務', '學術任職', '學術兼職', '指導與合作', '審稿人', '審稿經歷', '審稿服務', '審稿歴史', '學術審稿', '期刊審稿',
       '期刊論文評審', '刊物評審', '國際學術組織會員', '專業學會資格', '學術/專業會員資格', '國際編輯服務工作', '編輯經歷',
       '特刊編輯（特刊主編）', '期刊編輯（主編/副主編/領域主編/特刊主編）', 'Supervision', 'Academic services', 'Academic Services', 'Academic Membership',
       'Academic position', 'Referee for', 'Referee Services', 'Referee', 'Referee/Reviewer', 'Reviewer for Academic Journals', 'Referee for Journals/Publishers',
       'Membership', 'Reffree For', 'Editorial Service', 'Editorship', 'Guest Editor of Special issue', 'Editorial board: Editor/Associate Editor/Subject Editor/Guest Editor',
       'Contribution to International Research Councils', 'PhD External Examinership', 'ACADEMIC / PROFESSIONAL MEMBERSHIP')
labels('會議與演講', '學術會議', '國際學術會議', '會議及報告經歷', '主要會議報告', '學術交流', '演講', '受邀講演', '會議與研討會',
       '參加的國內外研討會和講座', '學術會議的參與', '參加的學術會議', '參加的學術會議 (均彙報展示)', '會議論文',
       'Conference', 'Conferences', 'Academic Conference', 'Academic Conferences', 'Conference Paper', 'Conference Papers', 'Conference Presentation', 'Conference Presentations',
       'Conferences and Workshops', 'Confrences and Workshops', 'Conferences Participation', 'Conferences and Presentations', 'Presentations', 'Seminars and workshops',
       'Research Papers Presented at Academic Conference', 'Research Papers Presented at Academic Conferences', 'PARTICIPATION IN ACADEMIC CONFERENCES')
labels('會議與演講', '學術活動', '研討會', 'Research Paper Presented at Academic conference')
labels('學術服務與指導', '審稿人/評審人')
labels('研究項目', 'Selected Projects')
labels('獎項', 'Selected Awards')
labels('獎項', '榮譽', '學術獎項', '所獲獎項', '獲獎情況', '主要獲獎情況', '獲獎經歷', '獲獎榮譽', '獎項與資助', '獎項及獎金',
       '近期教學獎項', '近期研究獎項', '教學成果', 'Award', 'Awards', 'Awards and Distinctions', 'Awards and Grants', 'Honors and Award', 'Honors and Awards',
       'Fellowships And Awards', 'Recent Teaching Awards', 'Recent Research Awards', 'AWARDS AND FUNDING')
labels('專長與軟件', '擅長', '編程軟件', '技能和語言', '編程語言與數據處理', 'Computer software', 'Computer Skills', 'Skills', 'Skills and Additional Information', 'Programming', 'Languages')
labels('其他公開資訊', '其他資訊', '社會榮譽', '社會服務', '媒體報道', '資格證書', 'Other information', 'Social Engagements', 'Media Coverage', 'Qualification')
labels('研究項目', 'Selected Projects', '參與課題')
labels('獎項', 'Selected Awards')
labels('學術服務與指導', '審稿人/評審人')
labels('會議與演講', '研討會', 'Research Paper Presented at Academic conference')
labels('papers', '出版論文精選', '學術出版', '出版論文', '論文', '論文發表', '期刊論文', '代表性論文', '論文代表作', '研究成果', '代表性研究成果',
       '已發表學術論文', '精選發表論文', '發表論文', '學術論文', '文章發表', 'Selected Academic Publications', 'Academic Publication', 'Academic Publications',
       'Publications', 'Publication', 'Articles', 'Papers', 'Journal Paper', 'Journal Papers', 'Journal Publications', 'Published Journal Articles', 'Selected Publications',
       'Selected publications', 'Research output', 'RESEARCH OUTPUT', 'Published Papers', 'Journal Publication', 'Academic Paper and Presentations',
       'Refereed Publications (Selected)', '1. A list of Academic Publication')
labels('working', '工作論文', '主要工作論文', '工作文章', '工作論文與項目', '進展中論文', '進展中學術論文', '一、代表性工作論文',
       'Working papers', 'Working Paper', 'Working Papers', 'Representative working papers', 'Work in progress', 'Papers in progress', 'Working Papers and Projects')
labels('papers', '出版物', '精選期刊發表')
labels('papers', '已發表的著作')
labels('books', '專著', '代表性著作', '主要著作', 'Books', '精選專著（著作、編著、研究報告)', 'Selected Monographs (Books, Edited Books, Research Reports)')
labels('chapters', 'Selected Publications in Books')
labels('review', '審閱中', 'Under Review')
labels('review', '審閱中', 'Under Review')
labels('books', '專著', '代表性著作', '主要著作', 'Books', 'Selected Monographs (Books, Edited Books, Research Reports)', '精選專著（著作、編著、研究報告)')
labels('chapters', 'Selected Publications in Books')


def heading_kind(block, current):
    text = block['text']
    key = norm(text)
    kind = HEADINGS.get(key)
    if key.startswith('selectedjournalpublications') or key.startswith('精選期刊論文') or key.startswith('精選期刊發表'):
        return 'papers'
    if re.match(r'^[一二三四五六七八九十]*[、. ]*已發表期刊論文', text) or re.match(r'^Journal papers\s*\(', text, re.I):
        return 'papers'
    if kind and len(text) < 160:
        # These are common subsection labels as well as top-level headings.
        if key in {norm('Teaching'), norm('教學類')} and current == '獎項':
            return None
        return kind
    return None


def expand_headings(raw):
    """Some CMS paragraphs embed a heading and several entries with <br>."""
    for block in raw:
        lines = block['text'].splitlines()
        if len(lines) == 1 or not any(heading_kind({**block, 'text': line}, None) for line in lines):
            yield block
            continue
        pending = []

        def segment(text):
            return {**block, 'text': text, 'html': html.escape(text),
                    'links': [(url, label) for url, label in block['links'] if norm(label) and norm(label) in norm(text)]}

        for line in lines:
            if heading_kind({**block, 'text': line}, None):
                if pending:
                    yield segment('\n'.join(pending))
                    pending = []
                yield segment(line)
            else:
                pending.append(line)
        if pending:
            yield segment('\n'.join(pending))


def items(record):
    content = collections.defaultdict(list)
    works = []
    audit = []
    current = None
    for block in expand_headings(blocks(record['article_html'])):
        text = block['text']
        kind = heading_kind(block, current)
        if kind:
            current = kind
            audit.append({**block, 'destination': 'heading', 'section': current})
            continue
        if current is None or current == 'contact':
            audit.append({**block, 'destination': 'identity/contact', 'section': current})
            continue
        if current in {'papers', 'working', 'review', 'books', 'chapters'}:
            if re.fullmatch(r'[（(]?\s*[*＊]\s*(?:通訊作者|通讯作者|Corresponding author)\s*[）)]?', text, re.I):
                audit.append({**block, 'destination': 'publication annotation', 'section': current})
                continue
            # Only known topic headings are excluded; a bold paper title is still a paper.
            topic = re.match(r'^(研究領域\s*\d|Research area\s*\d|[一二三][、.]|[ABC]\. (CSSCI|English|报刊))', text, re.I)
            if topic or norm(text) in {norm(s) for s in ['政治、衝突、國際關係','文化、心理、行為','港澳經濟','其他','Politics, Conflict, and International Relations','Culture, Psychology, and Behavior','Economy of Hong Kong and Macao','Other Topics','英文文章','中文文章','English Articles','Chinese Articles','选定出版物']}:
                audit.append({**block, 'destination': 'publication subheading', 'section': current})
                continue
            if re.search(r'^(?:澳門.*(?:研究項目|委員會項目)|橫琴.*聯合研究項目|濠江.*商會項目|Macau Foundation Research Project)', text, re.I):
                content['研究項目'].append({**block, 'source_url': record['url']})
                audit.append({**block, 'destination': 'content', 'section': '研究項目'})
                continue
            segments = citation_segments(text)
            for segment in segments:
                # A source occasionally wraps a journal name in a separate paragraph.
                if segment.startswith('Multinational Business Managemen,') and works:
                    works[-1]['text'] += ' ' + segment
                    continue
                segment_links = [(u,l) for u,l in block['links'] if u in segment or (norm(l) and norm(l) in norm(segment))]
                works.append({**block, 'text': segment, 'links': segment_links, 'kind': current, 'source_url': record['url']})
            audit.append({**block, 'destination': 'research', 'section': current})
        else:
            # Line breaks separate qualifications/appointments in several staff pages.
            lines = text.splitlines() if current in {'學歷','學術工作經驗','研究方向','教學科目','研究項目','獎項','學術服務與指導'} else [text]
            for line in lines:
                destination = '學術服務與指導' if current == '學術工作經驗' and re.search(r'論文導師|科研導師|匿名審稿|Undergraduate Research Mentor', line, re.I) else current
                line_links = [(u,l) for u,l in block['links'] if u in line or (norm(l) and norm(l) in norm(line))]
                content[destination].append({**block, 'text': line, 'links': line_links, 'source_url': record['url']})
            audit.append({**block, 'destination': 'content', 'section': current})
    return content, works, audit


def strip_bullet(text):
    return re.sub(r'^\s*(?:(?:[•·●▪*]|[.])\s*|\[\d+\]\s*|\d{1,3}[.)、]\s*)', '', clean(text))


def citation_segments(text):
    result = []
    for line in text.splitlines():
        if not result or re.match(r'^\s*(?:[•●]|\d+[.)、]|\[\d+\])\s*', line):
            result.append(line)
        else:
            result[-1] += ' ' + line
    return [strip_bullet(x) for x in result if norm(x)]


def content_text(item):
    text = strip_bullet(item['text'])
    for url, label in item.get('links', []):
        if url.startswith(('http://', 'https://')) and url not in text:
            text += '\n' + (label + ': ' if label and label not in text else '') + url
    return text


def contact_record(profile, original):
    row = copy.deepcopy(original) if original else {}
    zh, en = profile['zh'], profile['en']
    contact = '\n'.join(b['text'] for lang in ['zh', 'en'] for b in items(profile[lang])[2] if b['destination'] == 'identity/contact')
    rank = next((v for v in ['助理教授', '副教授', '教授', '講師'] if v in zh['title']), '')
    role = clean(zh['title'].replace(rank, '').strip('，, '))
    en_role = re.split(r'\s+and\s+(?=(?:Associate\s+)?Dean|Course Coordinator)', en['title'], maxsplit=1, flags=re.I)
    defaults = {'教師ID': profile['id'], '中文姓名': zh['name'], '英文姓名': en['name'], '職稱': rank,
                '行政職務': role, '導師標籤': zh['supervision'], '職稱（英文）': en_role[0],
                '行政職務（英文）': en_role[1] if len(en_role) > 1 else '', '導師標籤（英文）': en['supervision'],
                '相片網址': zh['image'], '個人網站': '', '電郵': '', '電話': '', '辦公室': '', 'WOS ID': '', 'Scopus ID': '', 'ORCID': ''}
    patterns = {'電郵': r'([\w.+-]+@cityu\.(?:edu\.)?mo)',
                '電話': r'(?<!\d)(8590[ -]?\d{4})(?!\d)',
                '辦公室': r'(?:辦公室|Office)\s*[:：]\s*((?:aa)?(?:GD|G)?\d{4}[A-Za-z]?)(?!\d)',
                'WOS ID': r'(?:WOS\s*Research(?:er)?\s*(?:ID)?|Web of Science\s*(?:Researcher\s*)?ID)\s*[:：]?\s*([A-Z]{1,4}-\d{4}-\d{4})',
                'Scopus ID': r'Scopus\s*(?:ID)?\s*[:：]?\s*(\d{8,13})',
                'ORCID': r'ORCID\s*[:：]?\s*((?:\d{4}-){3}\d{3}[\dXx])'}
    for key, pattern in patterns.items():
        match = re.search(pattern, contact, re.I)
        if match:
            defaults[key] = match.group(1)
    defaults['電郵'] = defaults['電郵'].replace('@cityu.mo', '@cityu.edu.mo')
    office = re.fullmatch(r'(?:GD|G)?(\d+[A-Za-z]?)', defaults['辦公室'], re.I)
    if office:
        defaults['辦公室'] = 'G' + office.group(1).upper()
    for key, value in defaults.items():
        if not str(row.get(key, '')).strip():
            row[key] = value
    for lang in ['zh', 'en']:
        for block in items(profile[lang])[2]:
            if block['destination'] != 'identity/contact':
                continue
            for url, _ in block['links']:
                if url.startswith('https://') and not any(x in urlsplit(url).netloc for x in ['cityu.edu.mo', 'scopus.com', 'webofscience.com', 'orcid.org']):
                    if not row['個人網站']:
                        row['個人網站'] = url
    row.update({'來源網址': zh['url'], '來源網址（英文）': en['url'], '資料狀態': '待核對'})
    return row


def prepare_content(rows, module):
    output, seen = [], set()
    for item in rows:
        # Semicolon-separated teaching/research lists become individual editable entries.
        parts = re.split(r'[;；]', item['text']) if module in {'教學科目', '研究方向'} else [item['text']]
        for part in parts:
            text = strip_bullet(part)
            if not norm(text) or norm(text) in seen:
                continue
            seen.add(norm(text))
            output.append({**item, 'text': text})
    return output


def leading_date(text):
    text = strip_bullet(text)
    pattern = r'^((?:19|20)\d{2}(?:\s*(?:年\s*\d{1,2}\s*月|[./]\d{1,2}))?\s*(?:[-–—至]\s*(?:(?:19|20)\d{2}(?:\s*(?:年\s*\d{1,2}\s*月|[./]\d{1,2}))?|至今|迄今|今|present|current)?))\s*[:：,]?\s*(.+)$'
    match = re.match(pattern, text, re.I)
    return (match.group(1).strip(), match.group(2).strip()) if match else ('', text)


def merge_content(profile, teacher_id, originals):
    languages = {lang: items(profile[lang])[0] for lang in ['zh', 'en']}
    result = []
    retained = []
    for module in MODULES:
        zh = prepare_content(languages['zh'].get(module, []), module)
        en = prepare_content(languages['en'].get(module, []), module)
        for i in range(max(len(zh), len(en))):
            a = zh[i] if i < len(zh) else None
            b = en[i] if i < len(en) else None
            ztext, etext = content_text(a) if a else '', content_text(b) if b else ''
            zd, ed = '', ''
            if module == '學術工作經驗':
                zd, ztext = leading_date(ztext)
                ed, etext = leading_date(etext)
                # The unmodified Studio falls back to the Chinese date in English.
                # Keep the date in the text if only one side has a date.
                if zd and b and not ed:
                    ztext, zd = content_text(a), ''
            urls = [u for item in [a, b] if item for u, _ in item['links'] if u.startswith(('https://', 'http://'))]
            result.append({'教師ID': teacher_id, '模組': module, '排序': i + 1, '時間': zd, '內容': ztext, '補充': '',
                           '連結': urls[0] if urls else '', '語言': '中文', '雙語欄位版本': 1,
                           '內容（英文）': etext, '時間（英文）': ed, '補充（英文）': '',
                           '來源網址（中文）': profile['zh']['url'] if a else '', '來源網址（英文）': profile['en']['url'] if b else ''})
    for old in originals:
        oldtext = norm(str(old.get('時間', '')) + str(old.get('內容', '')))
        candidates = [r for r in result if r['模組'] == old['模組']]
        if old['模組']=='學術服務與指導':
            terms=[norm(s) for s in re.split('[，,]',str(old.get('內容',''))) if norm(s)]
            corpus=norm(' '.join(r['內容'] for r in candidates))
            if len(terms)>4 and all(term in corpus for term in terms):
                continue  # The original journal list is already included in the newer full list.
        oldbody = norm(str(old.get('內容', '')))
        match = next((r for r in candidates if oldbody and (norm(r['內容']) == oldbody or (min(len(oldbody),len(norm(r['內容']))) > 12 and difflib.SequenceMatcher(None, oldbody, norm(r['內容'])).ratio() > .93))), None)
        if match:
            # Retain manually edited bilingual text and notes when the source item agrees.
            for key in ['內容', '補充', '時間', '內容（英文）', '補充（英文）', '時間（英文）']:
                if str(old.get(key, '')).strip():
                    match[key] = old[key]
        elif oldtext and not any(oldtext in norm(r['時間']+r['內容']) or norm(r['時間']+r['內容']) in oldtext for r in candidates if norm(r['時間']+r['內容'])):
            row = copy.deepcopy(old)
            row['教師ID'] = teacher_id
            row['雙語欄位版本'] = 1
            row['來源'] = '原有JSON備份；保留原編輯內容'
            result.append(row)
            retained.append({'teacher':teacher_id,'module':old['模組'],'text':old.get('內容','')})
    for module in MODULES:
        for i, row in enumerate(r for r in result if r['模組'] == module):
            row['排序'] = i + 1
    return result, retained


def get_doi(text):
    match = re.search(r'10\.\d{4,9}/[^\s<>"?#]+', unquote(text), re.I)
    if not match:
        return ''
    doi = match.group(0).rstrip('.,;:，。；）》')
    while doi.endswith(')') and doi.count(')') > doi.count('('):
        doi = doi[:-1]
    return 'https://doi.org/' + doi


def citation_title(text, markup=''):
    quotes = re.findall(r'[“"]([^”"\n]{18,})[”"]', text)
    if quotes:
        return max(quotes, key=len).strip(), True
    # Italic journal names delimit many unquoted titles without guessing sentence breaks.
    soup = BeautifulSoup(markup, 'html.parser')
    journals = [clean(el.get_text('',strip=True)) for el in soup.select('em,i') if len(clean(el.get_text('',strip=True))) > 8]
    for journal in journals:
        pos = text.find(journal)
        if pos > 25:
            before = text[:pos].strip(' .,;')
            year = re.search(r'[(（]?(?:19|20)\d{2}[)）]?[.,:：]?\s*', before)
            title = before[year.end():].strip(' .,;') if year else before.lstrip('* ')
            if len(title) > 18:
                return title, True
    # Working-paper lists often contain only a title and a coauthor parenthesis.
    stripped = re.sub(r'^(?:First Author|Solo Author|獨立作者|第一作者)\s*[,，]\s*', '', text, flags=re.I)
    stripped = re.split(r'[(（]\s*(?:with\b|與|个體|個體|團隊|軍事|隊友|轉型|基於|基于)', stripped, maxsplit=1, flags=re.I)[0].strip(' .。')
    if stripped != text and len(stripped) > 25 and not re.search(r'\b(?:19|20)\d{2}\b', stripped):
        return stripped, True
    # Standard author (year). Title. Journal references, with conservative boundaries.
    year = re.search(r'[(（](?:19|20)\d{2}[a-z]?[)）]\s*[.,，]?\s*', text)
    if year:
        after = text[year.end():].lstrip(' .,，')
        boundary = re.search(r'[.?]\s+(?=[A-Z][a-z])', after)
        if boundary and boundary.start() > 18:
            return after[:boundary.start()+int(after[boundary.start()]=='?')].strip(), True
    return '', False


def pagination_key(row):
    """Only a unique year + page range is eligible for reviewed bilingual matching."""
    text=row.get('完整引用','')
    if not row.get('年份'):
        return None
    pairs=re.findall(r'(?<!\d)(\d{1,4})\s*[-–—]\s*(\d{1,4})(?!\d)',text)
    pairs=[(a,b) for a,b in pairs if int(b)>int(a) and not (1900<=int(a)<=2100 and 1900<=int(b)<=2100)]
    if not pairs:
        return None
    return str(row['年份']),tuple(pairs[-1])


def research_row(item, teacher_id):
    citation = strip_bullet(item['text'])
    doi = get_doi(citation + ' ' + ' '.join([u for u,_ in item['links']]))
    no_urls = re.sub(r'https?://\S+|10\.\d{4,9}/\S+', '', citation)
    year = re.search(r'(?<!\d)((?:19|20)\d{2})(?!\d)', no_urls)
    status = {'working':'工作論文','review':'審閱中'}.get(item['kind'],'已發表')
    if re.search(r'R\s*&\s*R|revise\s*(?:and|&)\s*resubmit|修改後重投', citation, re.I):
        status = '修改後重投'
    elif item['kind'] not in {'working','review'} and re.search(r'\baccepted\b|\bforthcoming\b|已接受|已錄用|已录用|待刊', citation, re.I):
        status = '已接受'
    kind = {'books':'專著','chapters':'書籍章節'}.get(item['kind'],'期刊論文')
    if kind == '期刊論文' and re.search(r'proceedings|conference|symposium|annual meeting|研討會|論壇|會議', citation, re.I):
        kind = '會議論文'
    if re.search(r'\bChapter\s+\d|\bIn:\s', citation, re.I):
        kind = '書籍章節'
    if 'PhD Thesis' in citation:
        kind = '其他'
    title, reliable = citation_title(citation, item['html'])
    urls = [url for url,_ in item['links'] if url.startswith(('https://','http://'))]
    return {'教師ID':teacher_id,'狀態':status,'類型':kind,'語言':'中文' if re.search(r'[\u3400-\u9fff]', citation) else '英文',
            '排序':0,'年份':int(year.group(1)) if year else '', '完整引用':citation,'連結':doi or (urls[0] if urls else ''),'備註':'',
            # A full citation is the display fallback; inferred titles are deduplication keys only.
            '文章名':'','作者':'','期刊名':'','月份':'','DOI':doi,'期刊類別':'',
            '文章名（中文）':'','文章名（英文）':'','期刊名（中文）':'','期刊名（英文）':'',
            '來源網址':item['source_url'],'來源段落':item['index'],'_title':norm(title) if reliable else '', '_citation':norm(citation)}


def same_research(a,b):
    da,db=get_doi(str(a.get('DOI',''))),get_doi(str(b.get('DOI','')))
    if da and db:
        return da.lower()==db.lower()
    # Identical titles can be reprints in another year; require explicit evidence.
    drafts={'工作論文','審閱中','修改後重投'}
    if a.get('年份') and b.get('年份') and str(a['年份'])!=str(b['年份']) and a.get('狀態') not in drafts and b.get('狀態') not in drafts:
        return False
    ta,tb=a.get('_title','') or norm(a.get('文章名','')), b.get('_title','') or norm(b.get('文章名',''))
    ca,cb=a.get('_citation','') or norm(a.get('完整引用','')), b.get('_citation','') or norm(b.get('完整引用',''))
    if ta and tb and (ta==tb or (min(len(ta),len(tb))>35 and difflib.SequenceMatcher(None,ta,tb).ratio()>.96)):
        return True
    if ta and len(ta)>22 and ta in cb or tb and len(tb)>22 and tb in ca:
        return True
    if ca and cb and (ca==cb or (min(len(ca),len(cb))>55 and difflib.SequenceMatcher(None,ca,cb).ratio()>.94)):
        return True
    return False


def merge_research(profile, teacher_id, originals):
    result=[]
    for original in originals:
        row=copy.deepcopy(original)
        row['_title']=norm(row.get('文章名','')) or norm(citation_title(row.get('完整引用',''))[0])
        row['_citation']=norm(row.get('完整引用',''))
        result.append(row)
    parsed={lang:[research_row(item,teacher_id) for item in items(profile[lang])[1]] for lang in ['zh','en']}
    reviewed_path=ROOT/'data/reviewed_bilingual_pairs.json'
    reviewed=[p for p in json.loads(reviewed_path.read_text()) if p['teacher']==profile['id']]
    for lang in ['zh','en']:
        for item,row in zip(items(profile[lang])[1],parsed[lang]):
            existing=next((r for r in result if same_research(r,row)),None)
            if not existing and lang=='en':
                pair=next((p for p in reviewed if norm(p['en'])==norm(row['完整引用'])),None)
                if pair:
                    existing=next((r for r in result if norm(r.get('原始引用（中文）',''))==norm(pair['zh']) or norm(r.get('完整引用',''))==norm(pair['zh'])),None)
                    if existing:
                        existing['雙語配對依據']=pair['basis']
            original_reference='原始引用（中文）' if lang=='zh' else '原始引用（英文）'
            if existing:
                for key,value in row.items():
                    if key not in {'排序','狀態','類型'} and not existing.get(key) and value:
                        existing[key]=value
                key='來源網址（中文）' if lang=='zh' else '來源網址（英文）'
                existing[key]=item['source_url']
                if not existing.get(original_reference):
                    existing[original_reference]=row['完整引用']
                elif norm(row['完整引用'])!=norm(existing[original_reference]):
                    existing[original_reference]+='\n'+row['完整引用']
            else:
                row['來源網址（中文）' if lang=='zh' else '來源網址（英文）']=item['source_url']
                row[original_reference]=row['完整引用']
                result.append(row)
    for i,row in enumerate(result):
        row['教師ID']=teacher_id
        row['排序']=i+1
        row.pop('_title',None);row.pop('_citation',None)
    return result


def integrate():
    original=json.loads(INPUT.read_text())
    snapshot=json.loads((ROOT/'data/faculty_sources.json').read_text())
    output=copy.deepcopy(original)
    old=original['data']
    data={'教師資料':[],'內容明細':[],'研究成果':[],'共用設定':copy.deepcopy(old['共用設定'])}
    audit=[]
    for profile in snapshot['profiles']:
        base=next((t for t in old['教師資料'] if t['教師ID'].lstrip('_')==profile['id']),None)
        teacher=contact_record(profile,base)
        tid=teacher['教師ID']
        content,retained=merge_content(profile,tid,[r for r in old['內容明細'] if r['教師ID']==tid])
        research=merge_research(profile,tid,[r for r in old['研究成果'] if r['教師ID']==tid])
        data['教師資料'].append(teacher);data['內容明細'].extend(content);data['研究成果'].extend(research)
        audit.append({'id':tid,'source_id':profile['id'],'name':teacher['中文姓名'],'content_rows':len(content),'research_rows':len(research),'retained_original_content':retained,
                      'zh_modules':{m:len(r) for m,r in items(profile['zh'])[0].items()},'en_modules':{m:len(r) for m,r in items(profile['en'])[0].items()}})
        print(tid,len(content),len(research),'retained',len(retained),flush=True)
    output.update({'appVersion':'3.10','savedAt':datetime.now(timezone.utc).isoformat(),'data':data})
    assert len(data['教師資料'])==len(snapshot['profiles'])==43
    assert len({r['教師ID'] for r in data['教師資料']})==43
    assert output['templateCSS']==original['templateCSS']
    assert data['共用設定']==old['共用設定']
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'work/integration_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('OUTPUT',OUTPUT.name,{k:len(v) for k,v in data.items()},OUTPUT.stat().st_size,flush=True)


if __name__ == '__main__':
    (ROOT / 'work').mkdir(exist_ok=True)
    snapshot = json.loads((ROOT / 'data/faculty_sources.json').read_text())
    report = []
    for p in snapshot['profiles']:
        for lang in ['zh', 'en']:
            content, works, audit = items(p[lang])
            report.append({'id': p['id'], 'language': lang, 'content': {m:len(r) for m,r in content.items()},
                           'works':len(works), 'blocks':audit})
            print(p['id'],lang,dict((m,len(v)) for m,v in content.items()),'works',len(works))
    (ROOT/'work/section_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    integrate()
