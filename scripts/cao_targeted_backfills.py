import json, re, traceback
from pathlib import Path
import requests, pandas as pd
OUT=Path('cao_targeted'); OUT.mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'cao-replication-research/1.0'})

def fetch(provider,dataset,code):
 u=f'https://api.db.nomics.world/v22/series/{provider}/{dataset}/{code}?observations=1'
 r=S.get(u,timeout=90)
 if r.status_code!=200: return None, {'status':r.status_code,'url':u,'text':r.text[:300]}
 j=r.json(); docs=((j.get('series') or {}).get('docs') or [])
 return (docs[0] if docs else None), {'status':r.status_code,'url':u}

def rows(doc):
 ps=(doc or {}).get('period') or (doc or {}).get('periods') or []
 vs=(doc or {}).get('value') or (doc or {}).get('values') or []
 return [(str(p),v) for p,v in zip(ps,vs) if v is not None]

area={'AUS':'AU','AUT':'AT','BEL':'BE','CAN':'CA','CHE':'CH','DEU':'DE','ESP':'ES','FIN':'FI','FRA':'FR','GBR':'GB','ITA':'IT','JPN':'JP','NLD':'NL','NOR':'NO','NZL':'NZ','SWE':'SE','EA':'U2'}
name={'AUS':'Australia','AUT':'Austria','BEL':'Belgium','CAN':'Canada','CHE':'Switzerland','DEU':'Germany','ESP':'Spain','FIN':'Finland','FRA':'France','GBR':'United Kingdom','ITA':'Italy','JPN':'Japan','NLD':'Netherlands','NOR':'Norway','NZL':'New Zealand','SWE':'Sweden','EA':'Euro area'}
# Correct DOTS extract: reporter-country vs US; US reporter vs country; reporter vs World.
flow=[]; man=[]
for iso,rc in area.items():
 for reporter,counterpart,direction in [(rc,'US','country_reported_trade_with_US'),('US',rc,'US_reported_trade_with_country'),(rc,'W00','country_total_trade')]:
  for ind in ['TMG_CIF_USD','TMG_FOB_USD','TXG_FOB_USD']:
   code=f'A.{reporter}.{ind}.{counterpart}'
   doc,info=fetch('IMF','DOT',code); rr=rows(doc)
   keep=[(p,v) for p,v in rr if '1973'<=p<='2019']
   if keep:
    man.append({'country':name[iso],'iso3':iso,'direction':direction,'reporter_code':reporter,'counterpart_code':counterpart,'indicator':ind,'exact_series_code':f'IMF/DOT/{code}','series_label':(doc or {}).get('series_name',''),'first':keep[0][0],'last':keep[-1][0],'n':len(keep)})
    for p,v in keep:
     flow.append({'year':p,'country':name[iso],'iso3':iso,'direction':direction,'reporter_code':reporter,'counterpart_code':counterpart,'indicator':ind,'value':v,'unit':'US dollars, millions unless provider metadata indicates otherwise','valuation':'CIF' if ind=='TMG_CIF_USD' else 'FOB','source_database':'IMF Direction of Trade Statistics (legacy DOT) via DBnomics','exact_series_code':f'IMF/DOT/{code}','series_label':(doc or {}).get('series_name',''),'vintage':'IMF/DOT snapshot updated 2025-08-29','retrieval_date':'2026-08-19'})
pd.DataFrame(man).to_csv(OUT/'dots_manifest_corrected.csv',index=False)
pd.DataFrame(flow).to_csv(OUT/'dots_annual_1973_2019_corrected.csv',index=False)

# IFS export-price alternatives including Belgium-Luxembourg union and monthly fallbacks.
export=[]; eman=[]
for country,codes in {
 'Belgium':[('Q','BE'),('Q','R1'),('M','BE'),('M','R1')],
 'Switzerland':[('Q','CH'),('M','CH')]
}.items():
 for freq,ar in codes:
  for ind in ['TXG_D_FOB_IX','PXP_IX']:
   code=f'{freq}.{ar}.{ind}'
   doc,info=fetch('IMF','IFS',code); rr=rows(doc)
   keep=[(p,v) for p,v in rr if (p[:4].isdigit() and 1973<=int(p[:4])<=2019)]
   eman.append({'country':country,'freq':freq,'area':ar,'indicator':ind,'exact_series_code':f'IMF/IFS/{code}','status':info.get('status'),'series_label':(doc or {}).get('series_name',''),'first':keep[0][0] if keep else '', 'last':keep[-1][0] if keep else '', 'n':len(keep)})
   for p,v in keep: export.append({'period':p,'country':country,'frequency':freq,'value':v,'exact_series_code':f'IMF/IFS/{code}','series_label':(doc or {}).get('series_name','')})
pd.DataFrame(eman).to_csv(OUT/'ifs_export_alt_manifest.csv',index=False)
pd.DataFrame(export).to_csv(OUT/'ifs_export_alt_observations.csv',index=False)

# West Germany / Germany legacy IFS reference-area candidate search from metadata labels.
u='https://api.db.nomics.world/v22/series/IMF/IFS?limit=1'; j=S.get(u,timeout=90).json(); ds=j.get('dataset',{})
(Path(OUT/'ifs_meta.json')).write_text(json.dumps(ds,indent=2),encoding='utf-8')
dims=ds.get('dimensions_values_labels') or {}
areas=dims.get('REF_AREA',{}) if isinstance(dims,dict) else {}
west=[(k,v) for k,v in areas.items() if 'german' in str(v).lower()]
pd.DataFrame(west,columns=['area_code','label']).to_csv(OUT/'ifs_germany_area_candidates.csv',index=False)
# Test likely old historical area aliases and selected GDP/consumption series.
wrows=[]; wman=[]
for ar in list(dict.fromkeys([x[0] for x in west]+['DE','DE2'])):
 for freq in ['Q']:
  for ind in ['NGDP_SA_XDC','NGDP_R_SA_XDC','NCP_SA_XDC','NCP_R_SA_XDC','NC_SA_XDC','NC_R_SA_XDC']:
   code=f'{freq}.{ar}.{ind}'; doc,info=fetch('IMF','IFS',code); rr=rows(doc); keep=[(p,v) for p,v in rr if p[:4].isdigit() and 1973<=int(p[:4])<=1998]
   if keep:
    wman.append({'area':ar,'indicator':ind,'series_code':f'IMF/IFS/{code}','label':(doc or {}).get('series_name',''),'first':keep[0][0],'last':keep[-1][0],'n':len(keep)})
    for p,v in keep:wrows.append({'period':p,'area':ar,'indicator':ind,'value':v,'series_code':f'IMF/IFS/{code}','label':(doc or {}).get('series_name','')})
pd.DataFrame(wman).to_csv(OUT/'ifs_west_germany_series_manifest.csv',index=False); pd.DataFrame(wrows).to_csv(OUT/'ifs_west_germany_observations.csv',index=False)

summary={'dots_series':len(man),'dots_obs':len(flow),'export_alt_series_with_obs':sum(1 for x in eman if x['n']>0),'west_germany_series':len(wman)}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8'); print(json.dumps(summary,indent=2))
