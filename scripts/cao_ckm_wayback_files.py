import io,json,re,zipfile,hashlib
from pathlib import Path
import requests,pandas as pd
OUT=Path('cao_ckm_wayback'); OUT.mkdir(exist_ok=True); (OUT/'files').mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'cao-replication-research/1.0'})
base='ftp.mpls.frb.fed.us/pub/research/mcgrattan/sr277/*'
urls=[
 f'https://web.archive.org/cdx/search/cdx?url={base}&output=json&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype,statuscode,digest,length',
 f'http://web.archive.org/cdx/search/cdx?url={base}&output=json&filter=statuscode:200&collapse=urlkey&fl=timestamp,original,mimetype,statuscode,digest,length'
]
cdx=[]; logs=[]
for u in urls:
 try:
  r=S.get(u,timeout=120); logs.append({'url':u,'status':r.status_code,'bytes':len(r.content),'type':r.headers.get('content-type','')})
  if r.status_code==200:
   (OUT/'cdx_raw.json').write_bytes(r.content)
   j=r.json(); hdr=j[0] if j else []
   for row in j[1:]: cdx.append(dict(zip(hdr,row)))
   if cdx: break
 except Exception as e: logs.append({'url':u,'status':'ERROR','error':repr(e)})
pd.DataFrame(logs).to_csv(OUT/'cdx_query_log.csv',index=False)
pd.DataFrame(cdx).to_csv(OUT/'cdx_inventory.csv',index=False)

dl=[]
for i,x in enumerate(cdx):
 ts=x.get('timestamp'); orig=x.get('original'); mime=x.get('mimetype','')
 if not ts or not orig: continue
 # prioritize data/code/docs and skip directory HTML unless useful
 u=f'https://web.archive.org/web/{ts}id_/{orig}'
 try:
  r=S.get(u,timeout=180); rec={**x,'archive_url':u,'http_status':r.status_code,'bytes_downloaded':len(r.content),'content_type':r.headers.get('content-type','')}
  if r.status_code==200 and len(r.content)>0:
   nm=Path(orig.rstrip('/')).name or f'item_{i}'
   nm=re.sub('[^A-Za-z0-9._-]+','_',nm)
   if not nm: nm=f'item_{i}'
   # infer extension
   c=r.headers.get('content-type','').lower()
   if not Path(nm).suffix:
    if r.content[:2]==b'PK' or 'zip' in c: nm += '.zip'
    elif 'pdf' in c: nm += '.pdf'
    elif 'text' in c: nm += '.txt'
   # avoid overwrites
   dest=OUT/'files'/nm
   if dest.exists(): dest=OUT/'files'/(f'{i}_'+nm)
   dest.write_bytes(r.content); rec['saved_file']=str(dest.relative_to(OUT)); rec['sha256']=hashlib.sha256(r.content).hexdigest()
   if r.content[:2]==b'PK':
    try:
     ex=OUT/'files'/(dest.stem+'_extracted'); ex.mkdir(exist_ok=True)
     with zipfile.ZipFile(io.BytesIO(r.content)) as z:
      rec['zip_members']=' | '.join(z.namelist()); z.extractall(ex)
    except Exception as e: rec['zip_error']=repr(e)
  dl.append(rec)
 except Exception as e: dl.append({**x,'archive_url':u,'http_status':'ERROR','error':repr(e)})
pd.DataFrame(dl).to_csv(OUT/'download_log.csv',index=False)
# inventory and keyword flags
inv=[]
for p in (OUT/'files').rglob('*'):
 if p.is_file():
  low=p.name.lower(); inv.append({'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'likely_data_or_exchange_rate':any(k in low for k in ['data','exch','rate','euro','nom','cpi','xls','csv','dat','txt'])})
pd.DataFrame(inv).to_csv(OUT/'file_inventory.csv',index=False)
summary={'cdx_items':len(cdx),'downloaded':sum(1 for x in dl if x.get('saved_file')),'files':[x['path'] for x in inv]}
(OUT/'SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
