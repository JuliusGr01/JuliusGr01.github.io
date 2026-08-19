import io, json, re, zipfile, hashlib
from pathlib import Path
from urllib.parse import urljoin
import requests, pandas as pd
from bs4 import BeautifulSoup

OUT=Path('cao_direct_probe'); OUT.mkdir(exist_ok=True)
(OUT/'export_prices').mkdir(exist_ok=True); (OUT/'ckm').mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'cao-replication-research/1.0 academic replication'})
DATE='2026-08-19'

def fetch_series(code):
    u=f'https://api.db.nomics.world/v22/series/OECD/QNA/{code}?observations=1'
    try:
        r=S.get(u,timeout=90); r.raise_for_status(); j=r.json(); docs=((j.get('series') or {}).get('docs') or []); d=docs[0] if docs else None
        ps=(d or {}).get('period') or []; vs=(d or {}).get('value') or []
        rows=[(str(p),v) for p,v in zip(ps,vs) if v is not None]
        return d,j,rows,{'status':r.status_code,'url':u}
    except Exception as e: return None,None,[],{'status':'ERROR','url':u,'error':repr(e)}

def label(d): return (d or {}).get('series_name') or ''

countries={'Austria':'AUT','Canada':'CAN','Norway':'NOR','United Kingdom':'GBR','Euro area':'EA20','Belgium':'BEL','Switzerland':'CHE'}
rows=[]; man=[]
for country,iso in countries.items():
    start='1999-Q1' if country=='Euro area' else '1973-Q1'
    for measure in ['DNBSA','DOBSA']:
        code=f'{iso}.P6.{measure}.Q'; d,j,rr,info=fetch_series(code)
        keep=[(p,v) for p,v in rr if start<=p<='2019-Q4']
        man.append({'country':country,'measure':measure,'exact_series_code':f'OECD/QNA/{code}','series_label':label(d),'n':len(keep),'first':keep[0][0] if keep else '', 'last':keep[-1][0] if keep else '', 'status':info.get('status'),'retrieval_date':DATE})
        if keep and j:
            (OUT/'export_prices'/f'raw_OECD_QNA_{code.replace(".","_")}.json').write_text(json.dumps(j,indent=2),encoding='utf-8')
            for p,v in keep:
                rows.append({'period':p,'country':country,'value':v,'measure':measure,'source_database':'OECD Quarterly National Accounts via DBnomics','exact_series_code':f'OECD/QNA/{code}','series_label':label(d),'retrieval_date':DATE})
pd.DataFrame(man).to_csv(OUT/'export_prices'/'oecd_direct_export_deflator_manifest.csv',index=False)
pd.DataFrame(rows).drop_duplicates().to_csv(OUT/'export_prices'/'oecd_direct_export_deflators_raw.csv',index=False)

# Legacy CKM recovery attempts: old Minneapolis Fed page and Wayback snapshots of sr277 page.
urls=[
 'http://minneapolisfed.org/research/sr/sr277.html',
 'https://www.minneapolisfed.org/research/sr/sr277.html',
 'http://web.archive.org/cdx/search/cdx?url=minneapolisfed.org/research/sr/sr277.html&output=json&filter=statuscode:200&filter=mimetype:text/html&collapse=digest',
 'https://web.archive.org/cdx/search/cdx?url=minneapolisfed.org/research/sr/sr277.html&output=json&filter=statuscode:200&filter=mimetype:text/html&collapse=digest',
]
log=[]; discovered=[]
for u in urls:
    try:
        r=S.get(u,timeout=90,allow_redirects=True)
        rec={'requested_url':u,'final_url':r.url,'status':r.status_code,'content_type':r.headers.get('content-type',''),'bytes':len(r.content)}
        if r.status_code==200:
            fn='response_'+str(len(log))+('.json' if 'json' in rec['content_type'] else '.html')
            (OUT/'ckm'/fn).write_bytes(r.content); rec['saved_file']=fn
            if 'html' in rec['content_type']:
                soup=BeautifulSoup(r.text,'html.parser')
                for a in soup.find_all('a',href=True):
                    href=urljoin(r.url,a['href']); text=' '.join(a.stripped_strings)
                    if any(x in (href+' '+text).lower() for x in ['zip','data','code','append','xls','csv','download','file']): discovered.append({'source':r.url,'text':text,'url':href})
        log.append(rec)
    except Exception as e: log.append({'requested_url':u,'status':'ERROR','error':repr(e)})
pd.DataFrame(log).to_csv(OUT/'ckm'/'ckm_legacy_page_probe.csv',index=False)
pd.DataFrame(discovered).drop_duplicates().to_csv(OUT/'ckm'/'ckm_legacy_discovered_links.csv',index=False)

# If CDX response gave snapshot timestamps, try a few historical pages and harvest links.
cdx=[]
for p in (OUT/'ckm').glob('response_*.json'):
    try:
        j=json.loads(p.read_text())
        if isinstance(j,list) and len(j)>1:
            hdr=j[0];
            for row in j[1:]: cdx.append(dict(zip(hdr,row)))
    except Exception: pass
snaplog=[]
for rec in cdx[:10]:
    ts=rec.get('timestamp'); orig=rec.get('original') or 'http://minneapolisfed.org/research/sr/sr277.html'
    if not ts: continue
    u=f'https://web.archive.org/web/{ts}id_/{orig}'
    try:
        r=S.get(u,timeout=90); x={'url':u,'status':r.status_code,'bytes':len(r.content),'content_type':r.headers.get('content-type','')}
        if r.status_code==200:
            fn=f'sr277_wayback_{ts}.html'; (OUT/'ckm'/fn).write_bytes(r.content); x['saved_file']=fn
            soup=BeautifulSoup(r.text,'html.parser')
            for a in soup.find_all('a',href=True):
                href=urljoin(r.url,a['href']); text=' '.join(a.stripped_strings)
                if any(z in (href+' '+text).lower() for z in ['zip','data','code','append','xls','csv','download','file']): discovered.append({'source':r.url,'text':text,'url':href})
        snaplog.append(x)
    except Exception as e: snaplog.append({'url':u,'status':'ERROR','error':repr(e)})
pd.DataFrame(snaplog).to_csv(OUT/'ckm'/'ckm_wayback_snapshot_probe.csv',index=False)
pd.DataFrame(discovered).drop_duplicates().to_csv(OUT/'ckm'/'ckm_legacy_discovered_links.csv',index=False)

# Try bounded discovered binary/data links.
download=[]
for i,x in enumerate(discovered[:50]):
    u=x['url']
    try:
        r=S.get(u,timeout=120,allow_redirects=True); c=r.headers.get('content-type','').lower(); rec={'url':u,'final_url':r.url,'status':r.status_code,'bytes':len(r.content),'content_type':c}
        if r.status_code==200 and len(r.content)>300 and 'html' not in c:
            nm=Path(r.url.split('?')[0]).name or f'ckm_file_{i}'
            nm=re.sub('[^A-Za-z0-9._-]+','_',nm)
            if not Path(nm).suffix and r.content[:2]==b'PK': nm+='.zip'
            (OUT/'ckm'/nm).write_bytes(r.content); rec['saved_file']=nm; rec['sha256']=hashlib.sha256(r.content).hexdigest()
            if r.content[:2]==b'PK':
                try:
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        rec['zip_members']=' | '.join(z.namelist()); ex=OUT/'ckm'/'extracted'; ex.mkdir(exist_ok=True); z.extractall(ex)
                except Exception as e: rec['zip_error']=repr(e)
        download.append(rec)
    except Exception as e: download.append({'url':u,'status':'ERROR','error':repr(e)})
pd.DataFrame(download).to_csv(OUT/'ckm'/'ckm_legacy_download_attempts.csv',index=False)

summary={'direct_export_series_with_data':sum(1 for x in man if x['n']>0),'direct_export_observations':len(pd.DataFrame(rows).drop_duplicates()),'ckm_legacy_links_found':len(pd.DataFrame(discovered).drop_duplicates()) if discovered else 0,'ckm_binary_files':[str(p.relative_to(OUT/'ckm')) for p in (OUT/'ckm').rglob('*') if p.is_file() and p.suffix.lower() not in ['.csv','.html','.json']]}
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
