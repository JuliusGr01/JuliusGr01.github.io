import json, requests, os, datetime
from pathlib import Path

OUT=Path('cao_probe'); OUT.mkdir(exist_ok=True)
urls={
 'QNEA':'https://api.db.nomics.world/v22/series/IMF/QNEA?limit=2',
 'ER':'https://api.db.nomics.world/v22/series/IMF/ER?limit=2',
 'IFS':'https://api.db.nomics.world/v22/series/IMF/IFS?limit=2',
}
summary={}
for k,u in urls.items():
    r=requests.get(u,timeout=60)
    summary[k]={'status':r.status_code,'url':r.url,'text_head':r.text[:1000]}
    (OUT/f'{k}.txt').write_text(r.text,encoding='utf-8')
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2)[:5000])
