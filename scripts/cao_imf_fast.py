import json, requests, csv, math, re, datetime
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE='https://api.db.nomics.world/v22/series/IMF/IFS'
OUT=Path('cao_output_fast'); RAW=OUT/'raw_json'; OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
RETRIEVAL=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()

countries={
'United States':('US','1973-Q1','2019-Q4'),'Japan':('JP','1973-Q1','2019-Q4'),'United Kingdom':('GB','1973-Q1','2019-Q4'),'Canada':('CA','1973-Q1','2019-Q4'),'Australia':('AU','1973-Q1','2019-Q4'),'Switzerland':('CH','1973-Q1','2019-Q4'),'Sweden':('SE','1973-Q1','2019-Q4'),'Norway':('NO','1973-Q1','2019-Q4'),'New Zealand':('NZ','1973-Q1','2019-Q4'),
'Germany / West Germany':('DE','1973-Q1','1998-Q4'),'France':('FR','1973-Q1','1998-Q4'),'Italy':('IT','1973-Q1','1998-Q4'),'Spain':('ES','1973-Q1','1998-Q4'),'Netherlands':('NL','1973-Q1','1998-Q4'),'Belgium':('BE','1973-Q1','1998-Q4'),'Austria':('AT','1973-Q1','1998-Q4'),'Finland':('FI','1973-Q1','1998-Q4'),'Euro area':('U2','1999-Q1','2019-Q4')}

specs=[
('nominal_gdp','NGDP_SA_XDC',None,'Seasonally adjusted','Current prices; domestic currency'),
('real_gdp','NGDP_R_SA_XDC',None,'Seasonally adjusted','Constant/volume prices; domestic currency'),
('nominal_household_consumption','NCPHI_SA_XDC','NCP_SA_XDC','Seasonally adjusted','Current prices; domestic currency'),
('real_household_consumption','NCPHI_R_SA_XDC','NCP_R_SA_XDC','Seasonally adjusted','Constant/volume prices; domestic currency'),
('real_gfcf','NFI_R_SA_XDC',None,'Seasonally adjusted','Constant/volume prices; domestic currency'),
('employment','LE_PE_NUM',None,'Not specified in indicator code','Persons; level'),
('cpi','PCPI_IX',None,'Not specified in indicator code','All-items consumer price index'),
('exchange_rate_usd','ENDA_XDC_USD_RATE',None,'Not applicable','Domestic currency per U.S. dollar; period average'),
('export_price_deflator','TXG_D_FOB_IX','PXP_IX','Not specified in indicator code','Goods export deflator/unit value, FOB, index'),
('export_price_index_alt','PXP_IX',None,'Not specified in indicator code','Export price index, all commodities')]
monthly_ok={'employment','cpi','exchange_rate_usd','export_price_deflator','export_price_index_alt'}

meta=requests.get(f'{BASE}?limit=1',timeout=30).json(); dataset=meta.get('dataset',{})
ind_labels=dataset.get('dimensions_values_labels',{}).get('INDICATOR',{}); area_labels=dataset.get('dimensions_values_labels',{}).get('REF_AREA',{})
(OUT/'ifs_dataset_metadata.json').write_text(json.dumps(meta),encoding='utf-8')

def fetch_key(key):
    freq,area,ind=key
    url=f'{BASE}/{freq}.{area}.{ind}?observations=1'
    try:
        r=requests.get(url,timeout=20,headers={'User-Agent':'Cao-replication-fetch/1.0'})
        try:o=r.json()
        except:o={'message':r.text[:500]}
        return key,r.status_code,url,o
    except Exception as e:return key,0,url,{'message':repr(e)}

keys=set()
for _,(area,_,_) in countries.items():
  for var,ind,fb,_,_ in specs:
    keys.add(('Q',area,ind))
    if fb:keys.add(('Q',area,fb))
    if var in monthly_ok:
      keys.add(('M',area,ind))
      if fb:keys.add(('M',area,fb))

cache={}; logs=[]
with ThreadPoolExecutor(max_workers=24) as ex:
    futs=[ex.submit(fetch_key,k) for k in keys]
    for fut in as_completed(futs):
        k,status,url,obj=fut.result(); cache[k]=(status,obj)
        logs.append({'series_code':f'IMF/IFS/{k[0]}.{k[1]}.{k[2]}','http_status':status,'url':url,'message':obj.get('message','') if isinstance(obj,dict) else ''})
        if status==200:
            (RAW/f'{k[0]}_{k[1]}_{k[2]}.json').write_text(json.dumps(obj),encoding='utf-8')

def getdoc(freq,area,ind):
    status,o=cache.get((freq,area,ind),(0,{}))
    if status!=200:return None
    docs=o.get('series',{}).get('docs') or []
    return docs[0] if docs else None

def qi(s):
    m=re.match(r'^(\d{4})-?Q([1-4])$',s);return int(m.group(1))*4+int(m.group(2))-1

def normq(p):
    m=re.match(r'^(\d{4})-?Q([1-4])$',str(p));return f'{m.group(1)}Q{m.group(2)}' if m else None

def mtoq(p):
    m=re.match(r'^(\d{4})-(\d{2})$',str(p));
    return f'{m.group(1)}Q{(int(m.group(2))-1)//3+1}' if m else None

def inside(q,a,b):return qi(a)<=qi(q.replace('Q','-Q'))<=qi(b)
def num(v):
    try:
      x=float(v);return x if math.isfinite(x) else None
    except:return None

def label(doc,ind):return doc.get('series_name') or doc.get('series_label') or ind_labels.get(ind,ind)
def unit(lbl,doc):
    attrs=doc.get('attributes') or {}; um=attrs.get('UNIT_MULT') if isinstance(attrs,dict) else None; by=attrs.get('BASE_YEAR') if isinstance(attrs,dict) else None
    if 'Domestic Currency' in lbl:u='Domestic currency'
    elif 'Persons' in lbl or 'Number of' in lbl:u='Persons'
    elif 'Rate' in lbl:u='Rate'
    elif 'Index' in lbl:u='Index'
    else:u='See series label'
    if um not in (None,'0',0):u+=f'; UNIT_MULT={um}'
    if by:u+=f'; base={by}'
    return u

rows=[]; manifest=[]
for country,(area,a,b) in countries.items():
  for var,ind,fb,sa,pbasis in specs:
    doc=getdoc('Q',area,ind); used=ind; freq='Q'; fallback=False; method='direct quarterly observation'
    if not doc and fb:
      doc=getdoc('Q',area,fb); used=fb if doc else used; fallback=bool(doc)
    if not doc and var in monthly_ok:
      doc=getdoc('M',area,ind); freq='M' if doc else freq
      if not doc and fb:
        doc=getdoc('M',area,fb); used=fb if doc else used; fallback=bool(doc); freq='M' if doc else freq
      if doc:method='arithmetic mean of monthly observations within quarter'
    if not doc:
      manifest.append({'country':country,'area_code':area,'variable':var,'status':'MISSING','exact_series_code':'','series_label':'','frequency':'','fallback_used':fallback,'coverage_start':'','coverage_end':'','n_quarterly_obs':0,'expected_quarters':qi(b)-qi(a)+1,'coverage_ratio':0,'retrieval_date':RETRIEVAL});continue
    periods=doc.get('period') or []; vals=doc.get('value') or []
    obs=[]
    if freq=='Q':
      for p,v in zip(periods,vals):
        q=normq(p);x=num(v)
        if q and x is not None and inside(q,a,b):obs.append((q,x))
    else:
      buck=defaultdict(list)
      for p,v in zip(periods,vals):
        q=mtoq(p);x=num(v)
        if q and x is not None and inside(q,a,b):buck[q].append(x)
      obs=[(q,sum(v)/len(v)) for q,v in sorted(buck.items(),key=lambda z:qi(z[0].replace('Q','-Q'))) if v]
    lbl=label(doc,used); exact=f'IMF/IFS/{freq}.{area}.{used}'
    for q,x in obs:
      rows.append({'date':q,'country':country,'variable':var,'value':x,'unit':unit(lbl,doc),'seasonal_adjustment_status':sa,'price_basis':pbasis,'source_database':'IMF International Financial Statistics (legacy IFS) via DBnomics','exact_series_code':exact,'series_label':lbl,'original_frequency':freq,'quarterly_aggregation_method':method,'vintage_retrieval_date':RETRIEVAL,'reference_area_code':area,'reference_area_label':area_labels.get(area,country),'fallback_indicator_used':str(fallback),'replication_note':('IFS area DE used; Cao states West German macro series pre-reunification. Verify exact author splice.' if country=='Germany / West Germany' else '')})
    exp=qi(b)-qi(a)+1
    manifest.append({'country':country,'area_code':area,'variable':var,'status':'OK' if obs else 'NO_OBS_IN_WINDOW','exact_series_code':exact,'series_label':lbl,'frequency':freq,'fallback_used':fallback,'coverage_start':obs[0][0] if obs else '','coverage_end':obs[-1][0] if obs else '','n_quarterly_obs':len(obs),'expected_quarters':exp,'coverage_ratio':round(len(obs)/exp,4),'retrieval_date':RETRIEVAL})

fields=['date','country','variable','value','unit','seasonal_adjustment_status','price_basis','source_database','exact_series_code','series_label','original_frequency','quarterly_aggregation_method','vintage_retrieval_date','reference_area_code','reference_area_label','fallback_indicator_used','replication_note']
with open(OUT/'cao_macro_panel_raw.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(sorted(rows,key=lambda r:(r['country'],r['variable'],qi(r['date'].replace('Q','-Q')))))
with open(OUT/'cao_series_manifest.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(manifest[0]));w.writeheader();w.writerows(manifest)
with open(OUT/'cao_fetch_log.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=['series_code','http_status','url','message']);w.writeheader();w.writerows(logs)
summary={'retrieval_utc':RETRIEVAL,'rows':len(rows),'manifest_series':len(manifest),'ok_series':sum(m['status']=='OK' for m in manifest),'missing_or_empty_series':sum(m['status']!='OK' for m in manifest),'notes':['No G10 aggregation performed.','Euro area U2 only from 1999Q1; pre-1999 constituent currencies retained separately.','Household consumption uses NCPHI when available, NCP fallback otherwise.','TXG_D_FOB_IX is primary export deflator; PXP_IX also fetched as diagnostic alternative.','Monthly fallbacks are quarterly arithmetic means and marked as such.','Germany/West Germany remains a replication-specific splice issue.']}
(OUT/'README_fetch_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
