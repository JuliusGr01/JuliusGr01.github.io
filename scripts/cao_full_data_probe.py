import json, csv, re, traceback, os
from pathlib import Path
from urllib.parse import urljoin
import requests
import pandas as pd
import sdmx

OUT=Path('cao_full_probe'); OUT.mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'cao-replication-research/1.0'})

COUNTRIES={
'AUS':'Australia','AUT':'Austria','BEL':'Belgium','CAN':'Canada','CHE':'Switzerland','DEU':'Germany','ESP':'Spain','FIN':'Finland','FRA':'France','GBR':'United Kingdom','ITA':'Italy','JPN':'Japan','NLD':'Netherlands','NOR':'Norway','NZL':'New Zealand','SWE':'Sweden'}

def db_dataset(provider,dataset):
    u=f'https://api.db.nomics.world/v22/series/{provider}/{dataset}?limit=1'
    r=S.get(u,timeout=90); r.raise_for_status(); return r.json()

def db_series(provider,dataset,code):
    u=f'https://api.db.nomics.world/v22/series/{provider}/{dataset}/{code}?observations=1'
    r=S.get(u,timeout=90)
    if r.status_code!=200: return None, {'url':u,'status':r.status_code,'text':r.text[:500]}
    j=r.json()
    docs=((j.get('series') or {}).get('docs') or [])
    if not docs: return None, {'url':u,'status':200,'reason':'no docs'}
    return docs[0], {'url':u,'status':200}

def obs_rows(doc):
    periods=doc.get('period') or doc.get('periods') or []
    vals=doc.get('value') or doc.get('values') or []
    out=[]
    for p,v in zip(periods,vals):
        if v is None: continue
        out.append((str(p),v))
    return out

summary={}
# 1) OECD QNA metadata + targeted candidate series
try:
    meta=db_dataset('OECD','QNA')
    ds=meta.get('dataset',{})
    (OUT/'oecd_qna_dataset_meta.json').write_text(json.dumps(ds,indent=2),encoding='utf-8')
    dims=ds.get('dimensions_values_labels') or ds.get('dimensions_values') or {}
    summary['oecd_qna_dims_keys']=list(dims.keys()) if isinstance(dims,dict) else str(type(dims))
except Exception as e:
    summary['oecd_qna_meta_error']=repr(e); dims={}

measure_labels={}
if isinstance(dims,dict):
    mv=dims.get('MEASURE',{})
    if isinstance(mv,dict): measure_labels=mv
    elif isinstance(mv,list):
        for item in mv:
            if isinstance(item,dict): measure_labels[item.get('code','')]=item.get('label','')
subject_labels={}
if isinstance(dims,dict):
    sv=dims.get('SUBJECT',{})
    if isinstance(sv,dict): subject_labels=sv

candidate_rows=[]; selected_fetches=[]
# Probe all measure codes for GDP and private consumption for each country; this is only 16*30*2 requests max.
for loc,cname in COUNTRIES.items():
    for subject,var in [('B1_GE','nominal_gdp'),('P31S14_S15','real_household_consumption')]:
        for measure,mlab in measure_labels.items():
            lab=str(mlab).lower()
            if var=='nominal_gdp':
                if not ('current prices' in lab and 'seasonally adjusted' in lab and ('national currency' in lab)):
                    continue
                if any(x in lab for x in ['growth','percentage','contribution','deflator','index']): continue
            else:
                if not (('constant prices' in lab or 'volume' in lab) and 'seasonally adjusted' in lab and ('national currency' in lab)):
                    continue
                if any(x in lab for x in ['growth','percentage','contribution','deflator','index']): continue
            code=f'{loc}.{subject}.{measure}.Q'
            try:
                doc,info=db_series('OECD','QNA',code)
                rows=obs_rows(doc) if doc else []
                pre=[(p,v) for p,v in rows if '1973-Q1'<=p<='1998-Q4']
                candidate_rows.append({'country':cname,'location':loc,'target_variable':var,'series_code':code,'measure':measure,'measure_label':mlab,'series_name':(doc or {}).get('series_name',''),'first':rows[0][0] if rows else '', 'last':rows[-1][0] if rows else '', 'n_pre_euro':len(pre),'status':info.get('status')})
                if pre:
                    for p,v in pre:
                        selected_fetches.append({'date':p.replace('-',''),'country':cname,'variable':var,'value':v,'unit':mlab,'seasonal_adjustment_status':'Seasonally adjusted','price_basis':mlab,'source_database':'OECD Quarterly National Accounts via DBnomics','exact_series_code':f'OECD/QNA/{code}','series_label':(doc or {}).get('series_name',''),'original_frequency':'Q','quarterly_aggregation_method':'direct quarterly observation','vintage_retrieval_date':'2026-08-19','reference_area_code':loc,'reference_area_label':cname,'fallback_indicator_used':'True','replication_note':'Backfill candidate; OECD QNA 2024 snapshot. Added only after local selection/validation.'})
            except Exception as e:
                candidate_rows.append({'country':cname,'location':loc,'target_variable':var,'series_code':code,'measure':measure,'measure_label':mlab,'status':'ERR '+repr(e)[:120]})

pd.DataFrame(candidate_rows).to_csv(OUT/'oecd_qna_candidates.csv',index=False)
pd.DataFrame(selected_fetches).to_csv(OUT/'oecd_qna_candidate_observations.csv',index=False)
summary['oecd_candidate_rows']=len(candidate_rows); summary['oecd_candidate_obs']=len(selected_fetches)

# 2) Current IMF SA-equivalent probes
imf_client=sdmx.Client('IMF_DATA')
sa_queries={
'uk_nominal_gdp_sa':('QNEA','GBR.B1GQ.V.SA.XDC.Q'),
'sweden_nominal_gdp_sa':('QNEA','SWE.B1GQ.V.SA.XDC.Q'),
'nz_real_gdp_sa':('QNEA','NZL.B1GQ.Q.SA.XDC.Q'),
'nz_nom_hh_consumption_sa':('QNEA','NZL.P3_S14.V.SA.XDC.Q'),
'france_nominal_gdp_sa':('QNEA','FRA.B1GQ.V.SA.XDC.Q'),
'austria_nominal_gdp_sa':('QNEA','AUT.B1GQ.V.SA.XDC.Q'),
'finland_nominal_gdp_sa':('QNEA','FIN.B1GQ.V.SA.XDC.Q'),
}
imf_sa_summary={}; imf_sa_frames=[]
for name,(dataset,key) in sa_queries.items():
    try:
        msg=imf_client.data(dataset,key=key,params={'startPeriod':'1973-Q1','endPeriod':'2019-Q4'})
        df=sdmx.to_pandas(msg)
        d=df.rename('value').reset_index() if isinstance(df,pd.Series) else df.reset_index()
        d['query_name']=name; d['dataset']=dataset; d['requested_key']=key
        d.to_csv(OUT/f'imf_sa_{name}.csv',index=False)
        imf_sa_frames.append(d)
        imf_sa_summary[name]={'ok':True,'rows':len(d),'columns':list(d.columns),'first':d.astype(str).to_dict('records')[:1],'last':d.astype(str).to_dict('records')[-1:]}
    except Exception as e:
        imf_sa_summary[name]={'ok':False,'error':repr(e),'trace':traceback.format_exc()[-800:]}
if imf_sa_frames: pd.concat(imf_sa_frames,ignore_index=True,sort=False).to_csv(OUT/'imf_sa_all.csv',index=False)
(OUT/'imf_sa_summary.json').write_text(json.dumps(imf_sa_summary,indent=2),encoding='utf-8')
summary['imf_sa']=imf_sa_summary

# 3) Eurostat HICP 1999 and EA employment level candidates via DBnomics
extra_specs=[
('Eurostat','prc_hicp_midx','M.I05.CP00.EA','ea_hicp_monthly'),
('Eurostat','namq_10_pe','Q.THS_PER.SCA.EMP_DC.EA','ea_employment_sca'),
('Eurostat','namq_10_pe','Q.THS_PER.SA.EMP_DC.EA','ea_employment_sa'),
('Eurostat','namq_10_pe','Q.THS_PER.NSA.EMP_DC.EA','ea_employment_nsa'),
]
extra_summary={}
for provider,dataset,code,name in extra_specs:
    doc,info=db_series(provider,dataset,code)
    rows=obs_rows(doc) if doc else []
    extra_summary[name]={'code':f'{provider}/{dataset}/{code}','info':info,'series_name':(doc or {}).get('series_name',''),'first':rows[0][0] if rows else '', 'last':rows[-1][0] if rows else '', 'n':len(rows)}
    if rows: pd.DataFrame(rows,columns=['period','value']).to_csv(OUT/f'{name}.csv',index=False)
(OUT/'eurostat_extra_summary.json').write_text(json.dumps(extra_summary,indent=2),encoding='utf-8')
summary['eurostat_extra']=extra_summary

# 4) Export-price backfill candidates from OECD QNA: P6 deflators, especially BEL/CHE
export_rows=[]; export_obs=[]
for loc,cname in [('BEL','Belgium'),('CHE','Switzerland')]:
    for measure,mlab in measure_labels.items():
        lab=str(mlab).lower()
        if 'deflator' not in lab: continue
        code=f'{loc}.P6.{measure}.Q'
        doc,info=db_series('OECD','QNA',code)
        rows=obs_rows(doc) if doc else []
        export_rows.append({'country':cname,'series_code':code,'measure_label':mlab,'series_name':(doc or {}).get('series_name',''),'first':rows[0][0] if rows else '', 'last':rows[-1][0] if rows else '', 'n':len(rows),'status':info.get('status')})
        for p,v in rows:
            if '1973-Q1'<=p<='2019-Q4': export_obs.append({'period':p,'country':cname,'value':v,'exact_series_code':f'OECD/QNA/{code}','series_label':(doc or {}).get('series_name',''),'measure_label':mlab})
pd.DataFrame(export_rows).to_csv(OUT/'export_deflator_candidates.csv',index=False)
pd.DataFrame(export_obs).to_csv(OUT/'export_deflator_candidate_observations.csv',index=False)
summary['export_candidates']=len(export_rows)

# 5) DOTS annual bilateral/total flows: known old DOT codes, all areas.
# Fetch direct series using IMF legacy reference area codes (two-letter) and counterpart US/W0 candidates.
ifs_area={'AUS':'AU','AUT':'AT','BEL':'BE','CAN':'CA','CHE':'CH','DEU':'DE','ESP':'ES','FIN':'FI','FRA':'FR','GBR':'GB','ITA':'IT','JPN':'JP','NLD':'NL','NOR':'NO','NZL':'NZ','SWE':'SE','USA':'US','EA':'U2'}
dot_indicators=['TMG_CIF_USD','TMG_FOB_USD','TXG_FOB_USD']
# obtain DOT dataset metadata to discover counterpart codes and labels
try:
    dotmeta=db_dataset('IMF','DOT').get('dataset',{})
    (OUT/'imf_dot_dataset_meta.json').write_text(json.dumps(dotmeta,indent=2),encoding='utf-8')
    dd=dotmeta.get('dimensions_values_labels') or {}
    cpmap=dd.get('COUNTERPART_AREA',{}) if isinstance(dd,dict) else {}
    # Resolve US and World counterpart codes by labels when possible
    cp_us=[]; cp_world=[]
    if isinstance(cpmap,dict):
        for k,v in cpmap.items():
            vl=str(v).lower()
            if vl in ['united states','united states of america'] or 'united states' in vl: cp_us.append(k)
            if vl in ['world','world (all areas, including reference area, including io)'] or vl.startswith('world'): cp_world.append(k)
    summary['dot_counterpart_us_candidates']=cp_us; summary['dot_counterpart_world_candidates']=cp_world
except Exception as e:
    summary['dot_meta_error']=repr(e); cp_us=['US']; cp_world=['W0']

# DBnomics DOT ordering is FREQ.REF_AREA.INDICATOR.COUNTERPART_AREA
flow_rows=[]; flow_manifest=[]
for iso,cname in {**COUNTRIES,'USA':'United States','EA':'Euro area'}.items():
    reporter=ifs_area.get(iso)
    if not reporter: continue
    cps=list(dict.fromkeys((cp_us or ['US'])+(cp_world or ['W0'])))
    for ind in dot_indicators:
        for cp in cps:
            code=f'A.{reporter}.{ind}.{cp}'
            doc,info=db_series('IMF','DOT',code)
            rows=obs_rows(doc) if doc else []
            kept=[(p,v) for p,v in rows if '1973'<=p<='2019']
            if kept:
                flow_manifest.append({'reporter':cname,'reporter_code':reporter,'indicator':ind,'counterpart_code':cp,'series_code':f'IMF/DOT/{code}','series_label':(doc or {}).get('series_name',''),'first':kept[0][0],'last':kept[-1][0],'n':len(kept)})
                for p,v in kept: flow_rows.append({'year':p,'reporter':cname,'reporter_code':reporter,'indicator':ind,'counterpart_code':cp,'value':v,'unit':'US dollars (legacy DOT indicator)','valuation':'CIF' if 'CIF' in ind else 'FOB','source_database':'IMF Direction of Trade Statistics legacy DOT via DBnomics','exact_series_code':f'IMF/DOT/{code}','series_label':(doc or {}).get('series_name',''),'retrieval_date':'2026-08-19'})
pd.DataFrame(flow_manifest).to_csv(OUT/'dots_manifest.csv',index=False)
pd.DataFrame(flow_rows).to_csv(OUT/'dots_annual_flows.csv',index=False)
summary['dots_series_found']=len(flow_manifest); summary['dots_obs']=len(flow_rows)

# 6) IFS portfolio candidate indicators for US annual sample
try:
    ifsmeta=db_dataset('IMF','IFS').get('dataset',{})
    idims=ifsmeta.get('dimensions_values_labels') or {}
    indmap=idims.get('INDICATOR',{}) if isinstance(idims,dict) else {}
    port_inds=[]
    if isinstance(indmap,dict):
        for k,v in indmap.items():
            txt=str(v).lower()
            if any(term in txt for term in ['equity','portfolio investment','foreign assets','investment fund shares','shares and other equity']):
                port_inds.append((k,v))
    pd.DataFrame(port_inds,columns=['indicator','label']).to_csv(OUT/'ifs_portfolio_indicator_candidates.csv',index=False)
    port_series=[]; port_obs=[]
    for ind,label in port_inds:
        code=f'A.US.{ind}'
        doc,info=db_series('IMF','IFS',code)
        rows=obs_rows(doc) if doc else []
        if rows:
            port_series.append({'indicator':ind,'label':label,'series_code':f'IMF/IFS/{code}','series_name':(doc or {}).get('series_name',''),'first':rows[0][0],'last':rows[-1][0],'n':len(rows)})
            for p,v in rows: port_obs.append({'period':p,'indicator':ind,'value':v,'series_code':f'IMF/IFS/{code}','series_name':(doc or {}).get('series_name','')})
    pd.DataFrame(port_series).to_csv(OUT/'ifs_us_portfolio_series_candidates.csv',index=False)
    pd.DataFrame(port_obs).to_csv(OUT/'ifs_us_portfolio_candidate_observations.csv',index=False)
    summary['portfolio_indicators']=len(port_inds); summary['portfolio_series_with_data']=len(port_series)
except Exception as e:
    summary['portfolio_error']=repr(e)

# 7) CKM archive page: save page and discovered downloadable links/files
ckm_url='https://researchdatabase.minneapolisfed.org/concern/datasets/7d278t01v?locale=en'
try:
    r=S.get(ckm_url,timeout=90); r.raise_for_status(); (OUT/'ckm_dataset_page.html').write_text(r.text,encoding='utf-8')
    hrefs=re.findall(r'href=[\"\']([^\"\']+)[\"\']',r.text,re.I)
    links=[]
    for h in hrefs:
        u=urljoin(ckm_url,h)
        if any(term in u.lower() for term in ['download','file','zip','mat','xls','csv','txt','technical']): links.append(u)
    links=list(dict.fromkeys(links))
    pd.DataFrame({'url':links}).to_csv(OUT/'ckm_discovered_links.csv',index=False)
    dl=[]
    for idx,u in enumerate(links[:30]):
        try:
            rr=S.get(u,timeout=90,allow_redirects=True)
            ct=rr.headers.get('content-type',''); cd=rr.headers.get('content-disposition','')
            if rr.status_code==200 and len(rr.content)>500 and ('html' not in ct.lower() or any(x in u.lower() for x in ['.zip','.mat','.xls','.csv','.txt'])):
                fn=None
                m=re.search(r'filename\*?=(?:UTF-8\'\')?[\"\']?([^\"\';]+)',cd,re.I)
                if m: fn=m.group(1)
                if not fn: fn=u.split('?')[0].rstrip('/').split('/')[-1] or f'ckm_file_{idx}'
                fn=re.sub(r'[^A-Za-z0-9._-]+','_',fn)
                p=OUT/f'ckm_{idx:02d}_{fn}'; p.write_bytes(rr.content)
                dl.append({'url':u,'final_url':rr.url,'filename':p.name,'bytes':len(rr.content),'content_type':ct})
        except Exception as e: dl.append({'url':u,'error':repr(e)})
    pd.DataFrame(dl).to_csv(OUT/'ckm_download_log.csv',index=False)
    summary['ckm_links']=len(links); summary['ckm_downloaded']=sum(1 for x in dl if x.get('filename'))
except Exception as e:
    summary['ckm_error']=repr(e)

(OUT/'probe_summary.json').write_text(json.dumps(summary,indent=2,default=str),encoding='utf-8')
print(json.dumps(summary,indent=2,default=str)[:20000])
