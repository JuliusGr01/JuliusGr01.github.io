import json, requests
from pathlib import Path
OUT=Path('cao_oecd_tfp'); OUT.mkdir(exist_ok=True)
base='https://sdmx.oecd.org/archive/rest'
key='USA.A.MFPH..IX....'
data_url=f'{base}/data/OECD.SDD.TPS,DSD_PDB@DF_PDB_GR,1.0/{key}?startPeriod=1973&endPeriod=2019&dimensionAtObservation=AllDimensions'
struct_url=f'{base}/dataflow/OECD.SDD.TPS/DSD_PDB@DF_PDB_GR/1.0?references=all'
log=[]
for name,url,accept in [
 ('oecd_us_mfp_hours_1973_2019_raw.csv',data_url,'text/csv'),
 ('oecd_us_mfp_hours_1973_2019_raw.xml',data_url,'application/vnd.sdmx.genericdata+xml;version=2.1'),
 ('oecd_productivity_growth_structure.xml',struct_url,'application/vnd.sdmx.structure+xml;version=2.1')]:
 try:
  r=requests.get(url,headers={'Accept':accept,'User-Agent':'cao-replication-research/1.0'},timeout=120)
  log.append({'file':name,'url':url,'accept':accept,'status':r.status_code,'content_type':r.headers.get('content-type',''),'bytes':len(r.content)})
  if r.status_code==200: (OUT/name).write_bytes(r.content)
  else: (OUT/(name+'.error.txt')).write_text(r.text[:10000],encoding='utf-8')
 except Exception as e: log.append({'file':name,'url':url,'accept':accept,'status':'ERROR','error':repr(e)})
import csv
with open(OUT/'fetch_log.csv','w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=sorted(set().union(*(x.keys() for x in log)))); w.writeheader(); w.writerows(log)
(OUT/'README.md').write_text('''# OECD US multifactor productivity raw source\n\nRequested series: United States, annual, Multifactor productivity (hours based), index.\nOECD dataflow: `OECD.SDD.TPS,DSD_PDB@DF_PDB_GR,1.0`.\nQuery key: `USA.A.MFPH..IX....`.\nRequested sample: 1973-2019. The source itself begins later if no observations are available before its first year.\nRaw CSV/XML and the full SDMX structure response are preserved without transformation.\n''',encoding='utf-8')
print(json.dumps(log,indent=2))
