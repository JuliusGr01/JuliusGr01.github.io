import json, requests, csv, math, re, datetime, time
from pathlib import Path
from collections import defaultdict

BASE='https://api.db.nomics.world/v22/series/IMF/IFS'
OUT=Path('cao_output'); RAW=OUT/'raw_json'; OUT.mkdir(exist_ok=True); RAW.mkdir(exist_ok=True)
RETRIEVAL=datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
START='1973-Q1'; END='2019-Q4'

countries = {
 'United States':('US','1973-Q1','2019-Q4'),
 'Japan':('JP','1973-Q1','2019-Q4'),
 'United Kingdom':('GB','1973-Q1','2019-Q4'),
 'Canada':('CA','1973-Q1','2019-Q4'),
 'Australia':('AU','1973-Q1','2019-Q4'),
 'Switzerland':('CH','1973-Q1','2019-Q4'),
 'Sweden':('SE','1973-Q1','2019-Q4'),
 'Norway':('NO','1973-Q1','2019-Q4'),
 'New Zealand':('NZ','1973-Q1','2019-Q4'),
 'Germany / West Germany':('DE','1973-Q1','1998-Q4'),
 'France':('FR','1973-Q1','1998-Q4'),
 'Italy':('IT','1973-Q1','1998-Q4'),
 'Spain':('ES','1973-Q1','1998-Q4'),
 'Netherlands':('NL','1973-Q1','1998-Q4'),
 'Belgium':('BE','1973-Q1','1998-Q4'),
 'Austria':('AT','1973-Q1','1998-Q4'),
 'Finland':('FI','1973-Q1','1998-Q4'),
 'Euro area':('U2','1999-Q1','2019-Q4'),
}

# Primary concepts plus useful alternative raw series for replication diagnostics.
series_specs = [
 ('nominal_gdp','NGDP_SA_XDC','Q',None,'Seasonally adjusted','Current prices; domestic currency'),
 ('real_gdp','NGDP_R_SA_XDC','Q',None,'Seasonally adjusted','Constant/volume prices; domestic currency'),
 ('nominal_household_consumption','NCPHI_SA_XDC','Q','NCP_SA_XDC','Seasonally adjusted','Current prices; domestic currency'),
 ('real_household_consumption','NCPHI_R_SA_XDC','Q','NCP_R_SA_XDC','Seasonally adjusted','Constant/volume prices; domestic currency'),
 ('real_gfcf','NFI_R_SA_XDC','Q',None,'Seasonally adjusted','Constant/volume prices; domestic currency'),
 ('employment','LE_PE_NUM','Q',None,'Not specified in indicator code','Persons; level'),
 ('cpi','PCPI_IX','Q',None,'Not specified in indicator code','All-items consumer price index'),
 ('exchange_rate_usd','ENDA_XDC_USD_RATE','Q',None,'Not applicable','Domestic currency per U.S. dollar; period average'),
 ('export_price_deflator','TXG_D_FOB_IX','Q','PXP_IX','Not specified in indicator code','Goods export deflator/unit value, FOB, index'),
 ('export_price_index_alt','PXP_IX','Q',None,'Not specified in indicator code','Export price index, all commodities'),
]

session=requests.Session(); session.headers.update({'User-Agent':'Cao-replication-fetch/1.0'})

# Dataset metadata for exact labels and provider vintage.
meta_url=f'{BASE}?limit=1'
meta=session.get(meta_url,timeout=90).json()
dataset=meta.get('dataset',{})
indicator_labels=dataset.get('dimensions_values_labels',{}).get('INDICATOR',{})
area_labels=dataset.get('dimensions_values_labels',{}).get('REF_AREA',{})
provider_vintage=dataset.get('updated_at') or dataset.get('indexed_at') or dataset.get('provider_name') or 'DBnomics IMF IFS snapshot; dataset metadata does not expose a simple vintage field'
(OUT/'ifs_dataset_metadata.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')


def q_index(p):
    y,q=re.match(r'^(\d{4})-?Q([1-4])$',p).groups(); return int(y)*4+int(q)-1

def norm_q(p):
    m=re.match(r'^(\d{4})-?Q([1-4])$',str(p))
    return f'{m.group(1)}Q{m.group(2)}' if m else None

def month_to_q(p):
    m=re.match(r'^(\d{4})-(\d{2})$',str(p))
    if not m:return None
    y=int(m.group(1)); mo=int(m.group(2)); return f'{y}Q{(mo-1)//3+1}'

def in_range(q,a,b):
    qq=q.replace('Q','-Q'); return q_index(a)<=q_index(qq)<=q_index(b)

def extract_doc(obj):
    s=obj.get('series',{})
    docs=s.get('docs') or s.get('series') or []
    if isinstance(docs,list) and docs:return docs[0]
    return None

def fetch(freq,area,indicator):
    code=f'{freq}.{area}.{indicator}'
    url=f'{BASE}/{code}?observations=1'
    r=session.get(url,timeout=90)
    log={'series_code':f'IMF/IFS/{code}','http_status':r.status_code,'url':url,'error':''}
    safe=code.replace('.','_')
    try: obj=r.json()
    except Exception:
        log['error']='non-json response'; return None,log
    (RAW/f'{safe}.json').write_text(json.dumps(obj,indent=2),encoding='utf-8')
    if r.status_code!=200:
        log['error']=obj.get('message',str(obj)[:300]); return None,log
    doc=extract_doc(obj)
    if not doc:
        log['error']='no series document'; return None,log
    periods=doc.get('period') or doc.get('periods') or []
    values=doc.get('value') or doc.get('values') or []
    if not periods or not values:
        log['error']='no observations'; return None,log
    log['n_obs']=len(values)
    return doc,log

def numeric(v):
    try:
        if v is None:return None
        x=float(v)
        return x if math.isfinite(x) else None
    except:return None

def doc_unit(doc,label):
    attrs=doc.get('attributes') or {}
    unit_mult=attrs.get('UNIT_MULT') if isinstance(attrs,dict) else None
    base=attrs.get('BASE_YEAR') if isinstance(attrs,dict) else None
    parts=[]
    if 'Domestic Currency' in label: parts.append('Domestic currency')
    elif 'Percent' in label: parts.append('Percent')
    elif 'Number of' in label or 'Persons' in label: parts.append('Persons')
    elif 'Rate' in label: parts.append('Rate')
    elif 'Index' in label: parts.append('Index')
    else: parts.append('See series label')
    if unit_mult not in (None,'0',0): parts.append(f'UNIT_MULT={unit_mult}')
    if base: parts.append(f'base={base}')
    return '; '.join(parts)

rows=[]; logs=[]; manifest=[]
for country,(area,active_start,active_end) in countries.items():
  for variable,indicator,qfreq,fallback_indicator,sa_status,price_basis in series_specs:
    chosen=None; used_indicator=indicator; used_freq='Q'; fallback_used=False; method='direct quarterly observation'
    doc,lg=fetch('Q',area,indicator); logs.append({**lg,'country':country,'variable':variable,'attempt':'primary quarterly'})
    if doc is None and fallback_indicator:
        doc,lg=fetch('Q',area,fallback_indicator); logs.append({**lg,'country':country,'variable':variable,'attempt':'indicator fallback quarterly'})
        if doc is not None: used_indicator=fallback_indicator; fallback_used=True
    # For index/rate/level concepts, fall back to monthly and average within quarter.
    if doc is None and variable in {'employment','cpi','exchange_rate_usd','export_price_deflator','export_price_index_alt'}:
        monthly_indicator=used_indicator
        doc,lg=fetch('M',area,monthly_indicator); logs.append({**lg,'country':country,'variable':variable,'attempt':'monthly fallback'})
        if doc is None and fallback_indicator and monthly_indicator!=fallback_indicator:
            doc,lg=fetch('M',area,fallback_indicator); logs.append({**lg,'country':country,'variable':variable,'attempt':'monthly indicator fallback'})
            if doc is not None: used_indicator=fallback_indicator; fallback_used=True
        if doc is not None: used_freq='M'; method='arithmetic mean of monthly observations within quarter'
    if doc is None:
        manifest.append({'country':country,'area_code':area,'variable':variable,'status':'MISSING','exact_series_code':'','series_label':'','frequency':'','fallback_used':fallback_used,'coverage_start':'','coverage_end':'','n_quarterly_obs':0,'retrieval_date':RETRIEVAL,'provider_vintage':str(provider_vintage)})
        continue
    periods=doc.get('period') or doc.get('periods') or []; vals=doc.get('value') or doc.get('values') or []
    label=doc.get('series_name') or doc.get('series_label') or indicator_labels.get(used_indicator,used_indicator)
    exact=f'IMF/IFS/{used_freq}.{area}.{used_indicator}'
    outobs=[]
    if used_freq=='Q':
        for p,v in zip(periods,vals):
            q=norm_q(p); x=numeric(v)
            if q and x is not None and in_range(q,active_start,active_end): outobs.append((q,x))
    else:
        bucket=defaultdict(list)
        for p,v in zip(periods,vals):
            q=month_to_q(p); x=numeric(v)
            if q and x is not None and in_range(q,active_start,active_end): bucket[q].append(x)
        outobs=[(q,sum(vs)/len(vs)) for q,vs in sorted(bucket.items(),key=lambda z:q_index(z[0].replace('Q','-Q'))) if vs]
    unit=doc_unit(doc,label)
    for q,x in outobs:
        rows.append({
          'date':q,'country':country,'variable':variable,'value':x,'unit':unit,
          'seasonal_adjustment_status':sa_status,'price_basis':price_basis,
          'source_database':'IMF International Financial Statistics (legacy IFS) via DBnomics',
          'exact_series_code':exact,'series_label':label,'original_frequency':used_freq,
          'quarterly_aggregation_method':method,'vintage_retrieval_date':RETRIEVAL,
          'reference_area_code':area,'reference_area_label':area_labels.get(area,country),
          'fallback_indicator_used':str(fallback_used),
          'replication_note':('DE is the current IFS Germany reference-area code; Cao states West German data are used pre-reunification. Verify author splice before calling 1:1 exact.' if country=='Germany / West Germany' else '')
        })
    manifest.append({'country':country,'area_code':area,'variable':variable,'status':'OK' if outobs else 'NO_OBS_IN_WINDOW','exact_series_code':exact,'series_label':label,'frequency':used_freq,'fallback_used':fallback_used,'coverage_start':outobs[0][0] if outobs else '','coverage_end':outobs[-1][0] if outobs else '','n_quarterly_obs':len(outobs),'retrieval_date':RETRIEVAL,'provider_vintage':str(provider_vintage)})
    time.sleep(0.05)

# Add completeness expectations.
expected={}
for country,(_,a,b) in countries.items(): expected[country]=q_index(b)-q_index(a)+1
for m in manifest:
    m['expected_quarters']=expected[m['country']]
    m['coverage_ratio']=round(m['n_quarterly_obs']/m['expected_quarters'],4) if m['expected_quarters'] else 0

fields=['date','country','variable','value','unit','seasonal_adjustment_status','price_basis','source_database','exact_series_code','series_label','original_frequency','quarterly_aggregation_method','vintage_retrieval_date','reference_area_code','reference_area_label','fallback_indicator_used','replication_note']
with open(OUT/'cao_macro_panel_raw.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(sorted(rows,key=lambda r:(r['country'],r['variable'],q_index(r['date'].replace('Q','-Q')))))
if manifest:
    with open(OUT/'cao_series_manifest.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(manifest[0])); w.writeheader(); w.writerows(manifest)
if logs:
    keys=[]
    for r in logs:
        for k in r:
            if k not in keys: keys.append(k)
    with open(OUT/'cao_fetch_log.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(logs)
summary={
 'retrieval_utc':RETRIEVAL,'source':'IMF IFS via DBnomics','dataset_metadata_url':meta_url,
 'countries':len(countries),'rows':len(rows),'manifest_series':len(manifest),
 'ok_series':sum(m['status']=='OK' for m in manifest),'missing_series':sum(m['status']!='OK' for m in manifest),
 'important_notes':[
  'Country-level series are not G10-aggregated.',
  'Euro-area reference area U2 is used only from 1999Q1; pre-1999 euro constituents are retained separately.',
  'Germany uses IMF IFS area DE. Cao explicitly states West German macro data pre-reunification; this historical splice needs author verification.',
  'Household consumption uses NCPHI series when available and falls back to broader private-sector consumption NCP only when necessary.',
  'Export-price deflator primary series is TXG_D_FOB_IX; PXP_IX is also fetched as an alternative diagnostic series.',
  'Monthly fallback series are converted to quarterly arithmetic averages and explicitly labelled.'
 ]
}
(OUT/'README_fetch_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
