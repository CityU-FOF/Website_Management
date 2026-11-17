"""Save only metadata actually adopted by the reviewed backup for offline rebuilds."""
import copy
import hashlib
import json

from integrate_faculty import ROOT, OUTPUT
from fetch_bibliography_metadata import CACHE
from structure_faculty import journal_lexicon, reviewed_metadata


def main():
    backup=json.loads(OUTPUT.read_text())
    previous=reviewed_metadata()
    pool={m['DOI'].lower():m for m in previous['records']}
    for path in CACHE.glob('*.json'):
        for item in json.loads(path.read_text()).get('items',[]):
            if item.get('DOI'):pool[item['DOI'].lower()]=item
    matches=[];records={}
    for row in backup['data']['研究成果']:
        if not row.get('文獻資料來源','').startswith('https://api.crossref.org'):continue
        doi=row['DOI'].removeprefix('https://doi.org/').lower()
        assert doi in pool,doi
        metadata=copy.deepcopy(pool[doi]);metadata.pop('score',None)
        metadata['author']=[{k:v for k,v in author.items() if k in ['given','family','name']} for author in metadata.get('author',[])]
        records[doi]=metadata
        matches.append({'teacher':row['教師ID'],'citation_sha256':hashlib.sha256(row['完整引用'].encode()).hexdigest(),'DOI':doi})
    snapshot=json.loads((ROOT/'data/faculty_sources.json').read_text())
    out={'source':'Crossref REST API; reviewed title, author and publication-venue matches',
         'retrieved_on':'2026-11-17','records':sorted(records.values(),key=lambda m:m['DOI']),
         'journal_lexicon':journal_lexicon(snapshot,backup),'citation_matches':matches}
    (ROOT/'data/bibliography_verified_metadata.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('Saved metadata records',len(records),'citation matches',len(matches))


if __name__=='__main__':main()
