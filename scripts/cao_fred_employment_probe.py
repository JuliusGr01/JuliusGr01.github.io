import csv, io, json
from pathlib import Path
import requests
OUT=Path('cao_fred_emp'); OUT.mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'cao-replication-research/1.0'})
# OECD Infra-Annual Labour Statistics mirrored by FRED. Pattern: total employment age 15+, persons, SA, quarterly.
areas={'AU':'Australia','AT':'Austria','BE':'Belgium','CA':'Canada','CH':'Switzerland','DE':'Germany','ES':'Spain','FI':'Finland','FR':'France','GB':'United Kingdom','IT':'Italy','JP':'Japan','NL':'Netherlands','NO':'Norway','NZ':'New Zealand','SE':'Sweden'}
rows=[]; manifest=[]
for cc,country in areas.items():
    sid=f'LFEMTTTT{cc}Q647S'
    u=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=1973-01-01&coed=2019-12-31'
    r=S.get(u,timeout=60)
    rec={'country':country,'fred_series_id':sid,'url':u,'http_status':r.status_code}
    if r.status_code==200 and 'DATE' in r.text[:200]:
        data=list(csv.DictReader(io.StringIO(r.text)))
        data=[x for x in data if x.get(sid) not in (None,'','.','NA')]
        rec.update({'n':len(data),'first':data[0]['DATE'] if data else '','last':data[-1]['DATE'] if data else ''})
        for x in data:
            dt=x['DATE']; y=int(dt[:4]); m=int(dt[5:7]); q=(m-1)//3+1
            rows.append({'date':f'{y}Q{q}','country':country,'variable':'employment','value':x[sid],'unit':'Persons','seasonal_adjustment_status':'Seasonally adjusted','price_basis':'Not applicable','source_database':'OECD Infra-Annual Labour Statistics via FRED','exact_series_code':sid,'series_label':'Employment, Total, Persons, age 15+, Seasonally Adjusted, Quarterly','original_frequency':'Q','quarterly_aggregation_method':'direct quarterly observation','vintage_retrieval_date':'2026-08-19','reference_area_code':cc,'reference_area_label':country,'fallback_indicator_used':'True','replication_note':'Employment backfill candidate from OECD infra-annual labor statistics mirrored by FRED; verify concept/splice against Cao author data.'})
    else:
        rec.update({'n':0,'error_head':r.text[:120]})
    manifest.append(rec)
with open(OUT/'fred_oecd_employment_manifest.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(manifest[0])); w.writeheader(); w.writerows(manifest)
if rows:
    with open(OUT/'fred_oecd_employment_observations.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
(OUT/'summary.json').write_text(json.dumps({'series':len(manifest),'series_with_data':sum(1 for x in manifest if x.get('n',0)),'observations':len(rows)},indent=2),encoding='utf-8')
print((OUT/'summary.json').read_text())
