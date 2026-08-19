import os, re, json, csv, io, zipfile, hashlib, traceback, time
from pathlib import Path
from urllib.parse import urljoin
import requests
import pandas as pd
from bs4 import BeautifulSoup

OUT=Path('cao_final_gaps'); OUT.mkdir(exist_ok=True)
for d in ['dots','export_prices','ckm','portfolio','author_search','metadata']:
    (OUT/d).mkdir(exist_ok=True)
S=requests.Session(); S.headers.update({'User-Agent':'cao-replication-research/1.0 (+academic replication)'})
RETRIEVAL='2026-08-19'

def dump_json(path,obj):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str),encoding='utf-8')

def get_json(url,timeout=90):
    r=S.get(url,timeout=timeout); r.raise_for_status(); return r.json(),r

def dbnomics_dataset(provider,dataset):
    u=f'https://api.db.nomics.world/v22/series/{provider}/{dataset}?limit=1'
    j,r=get_json(u); return j.get('dataset',{}),u

def dbnomics_series(provider,dataset,code):
    u=f'https://api.db.nomics.world/v22/series/{provider}/{dataset}/{code}?observations=1'
    try:
        j,r=get_json(u)
        docs=((j.get('series') or {}).get('docs') or [])
        return (docs[0] if docs else None), j, {'status':r.status_code,'url':u}
    except Exception as e:
        return None,None,{'status':None,'url':u,'error':repr(e)}

def obs_rows(doc):
    if not doc: return []
    ps=doc.get('period') or doc.get('periods') or []
    vs=doc.get('value') or doc.get('values') or []
    return [(str(p),v) for p,v in zip(ps,vs) if v is not None]

def series_label(doc):
    return (doc or {}).get('series_name') or (doc or {}).get('series_name_short') or (doc or {}).get('name') or ''

def save_dbnomics_raw(provider,dataset,code,folder,prefix=None,start=None,end=None):
    doc,j,info=dbnomics_series(provider,dataset,code)
    rows=obs_rows(doc)
    if start or end:
        rows=[(p,v) for p,v in rows if (not start or p>=start) and (not end or p<=end)]
    safe=(prefix or code).replace('/','_').replace('.','_')
    if j is not None:
        dump_json(Path(folder)/f'{safe}_raw_response.json',j)
    out=[]
    for p,v in rows:
        out.append({'period':p,'value':v,'provider':provider,'dataset':dataset,'exact_series_code':f'{provider}/{dataset}/{code}','series_label':series_label(doc),'unit':(doc or {}).get('unit_name','') or (doc or {}).get('unit',''),'frequency':(doc or {}).get('dimensions',{}).get('FREQ','') if isinstance((doc or {}).get('dimensions'),dict) else '','retrieval_date':RETRIEVAL})
    if out: pd.DataFrame(out).to_csv(Path(folder)/f'{safe}.csv',index=False)
    meta={'provider':provider,'dataset':dataset,'code':code,'exact_series_code':f'{provider}/{dataset}/{code}','label':series_label(doc),'n':len(rows),'first':rows[0][0] if rows else '', 'last':rows[-1][0] if rows else '',**info}
    return out,meta,doc

# ------------------------------------------------------------------
# 0. Preserve dataset metadata for the near-vintage legacy IMF mirrors
# ------------------------------------------------------------------
for ds in ['IFS','DOT']:
    try:
        meta,u=dbnomics_dataset('IMF',ds)
        dump_json(OUT/'metadata'/f'IMF_{ds}_dataset_metadata.json',meta)
    except Exception as e:
        dump_json(OUT/'metadata'/f'IMF_{ds}_dataset_metadata_ERROR.json',{'error':repr(e)})

# ------------------------------------------------------------------
# 1. Belgian historical DOTS + US total-world trade
# ------------------------------------------------------------------
dot_meta,_=dbnomics_dataset('IMF','DOT')
dims=dot_meta.get('dimensions_values_labels') or {}
# Find any historical area labels involving Belgium and/or Luxembourg.
area_maps=[]
for dimname,dmap in dims.items():
    if not isinstance(dmap,dict): continue
    if 'AREA' in dimname.upper() or 'COUNTERPART' in dimname.upper():
        for k,v in dmap.items():
            lab=str(v)
            if ('belg' in lab.lower()) or ('luxemb' in lab.lower()):
                area_maps.append({'dimension':dimname,'code':k,'label':lab})
pd.DataFrame(area_maps).drop_duplicates().to_csv(OUT/'dots'/'dot_belgium_luxembourg_area_candidates.csv',index=False)

candidate_areas=[]
for x in area_maps: candidate_areas.append(x['code'])
for c in ['BE','R1','BLX','BLEU','BLS','BX','LU']:
    if c not in candidate_areas: candidate_areas.append(c)
inds=['TMG_CIF_USD','TMG_FOB_USD','TXG_FOB_USD']
flows=[]; manifest=[]
queries=[]
for ar in candidate_areas:
    for ind in inds:
        queries += [
            ('Belgium_or_BLEU_reporter_vs_US',f'A.{ar}.{ind}.US',ar,'US',ind),
            ('US_reporter_vs_Belgium_or_BLEU',f'A.US.{ind}.{ar}','US',ar,ind),
            ('Belgium_or_BLEU_total_world',f'A.{ar}.{ind}.W00',ar,'W00',ind),
        ]
seen=set()
for direction,code,reporter,counterpart,ind in queries:
    if code in seen: continue
    seen.add(code)
    doc,j,info=dbnomics_series('IMF','DOT',code); rr=obs_rows(doc)
    keep=[(p,v) for p,v in rr if '1973'<=p<='2019']
    early=[(p,v) for p,v in keep if p<='1996']
    manifest.append({'direction':direction,'reporter':reporter,'counterpart':counterpart,'indicator':ind,'exact_series_code':f'IMF/DOT/{code}','series_label':series_label(doc),'n_1973_2019':len(keep),'n_1973_1996':len(early),'first':keep[0][0] if keep else '', 'last':keep[-1][0] if keep else '','status':info.get('status'),'url':info.get('url')})
    if early:
        if j is not None: dump_json(OUT/'dots'/f'raw_{code.replace(".","_")}.json',j)
        for p,v in early:
            flows.append({'year':p,'value':v,'direction':direction,'reporter_code':reporter,'counterpart_code':counterpart,'indicator':ind,'valuation':'CIF' if ind=='TMG_CIF_USD' else 'FOB','currency':'USD','source_database':'IMF Direction of Trade Statistics (legacy DOT) via DBnomics','exact_series_code':f'IMF/DOT/{code}','series_label':series_label(doc),'retrieval_date':RETRIEVAL})
pd.DataFrame(manifest).to_csv(OUT/'dots'/'belgium_historical_dots_probe_manifest.csv',index=False)
pd.DataFrame(flows).to_csv(OUT/'dots'/'belgium_historical_dots_1973_1996_raw.csv',index=False)

# US total-world imports/exports required for absorption denominator checks.
usw=[]; uswman=[]
for ind in inds:
    code=f'A.US.{ind}.W00'
    doc,j,info=dbnomics_series('IMF','DOT',code); rr=[(p,v) for p,v in obs_rows(doc) if '1973'<=p<='2019']
    if j is not None: dump_json(OUT/'dots'/f'raw_{code.replace(".","_")}.json',j)
    uswman.append({'indicator':ind,'exact_series_code':f'IMF/DOT/{code}','series_label':series_label(doc),'n':len(rr),'first':rr[0][0] if rr else '', 'last':rr[-1][0] if rr else '', 'status':info.get('status')})
    for p,v in rr:
        usw.append({'year':p,'value':v,'reporter_code':'US','counterpart_code':'W00','indicator':ind,'valuation':'CIF' if ind=='TMG_CIF_USD' else 'FOB','currency':'USD','source_database':'IMF Direction of Trade Statistics (legacy DOT) via DBnomics','exact_series_code':f'IMF/DOT/{code}','series_label':series_label(doc),'retrieval_date':RETRIEVAL})
pd.DataFrame(usw).to_csv(OUT/'dots'/'us_total_world_trade_1973_2019_raw.csv',index=False)
pd.DataFrame(uswman).to_csv(OUT/'dots'/'us_total_world_trade_manifest.csv',index=False)

# ------------------------------------------------------------------
# 2. Concept-consistent export-price source extracts
#    First try official current IMF QNEA P6 price deflator, then preserve
#    OECD QNA nominal/volume source components as a concept-consistent fallback.
# ------------------------------------------------------------------
try:
    import sdmx
    client=sdmx.Client('IMF_DATA')
    qnea_rows=[]; qnea_man=[]
    refs={'Austria':['AUT'],'Canada':['CAN'],'Norway':['NOR'],'United Kingdom':['GBR'],'Euro area':['G163','EA','EA20','EA19','EUR','U2']}
    for cname,refcands in refs.items():
        for ref in refcands:
            for adj in ['SA','NSA']:
                key=f'{ref}.P6.PD.{adj}.IX.Q'
                try:
                    msg=client.data('QNEA',key=key,params={'startPeriod':'1973-Q1','endPeriod':'2019-Q4'})
                    d=sdmx.to_pandas(msg)
                    if isinstance(d,pd.Series): d=d.rename('value').reset_index()
                    else: d=d.reset_index()
                    n=len(d)
                    qnea_man.append({'country':cname,'requested_key':key,'dataset':'QNEA','adjustment':adj,'n':n,'status':'OK','retrieval_date':RETRIEVAL})
                    if n:
                        d['country']=cname; d['requested_key']=key; d['dataset']='IMF QNEA'; d['retrieval_date']=RETRIEVAL
                        qnea_rows.append(d)
                        d.to_csv(OUT/'export_prices'/f'imf_qnea_{cname.replace(" ","_")}_{ref}_{adj}_raw.csv',index=False)
                except Exception as e:
                    qnea_man.append({'country':cname,'requested_key':key,'dataset':'QNEA','adjustment':adj,'n':0,'status':repr(e)[:300],'retrieval_date':RETRIEVAL})
    if qnea_rows: pd.concat(qnea_rows,ignore_index=True,sort=False).to_csv(OUT/'export_prices'/'imf_qnea_export_deflators_all_raw.csv',index=False)
    pd.DataFrame(qnea_man).to_csv(OUT/'export_prices'/'imf_qnea_export_deflator_manifest.csv',index=False)
except Exception as e:
    dump_json(OUT/'export_prices'/'imf_qnea_client_error.json',{'error':repr(e),'trace':traceback.format_exc()})

# OECD QNA raw P6 nominal and volume components for ALL five gaps.
oecd=[]; oecdman=[]
oecd_country={'Austria':'AUT','Canada':'CAN','Norway':'NOR','United Kingdom':'GBR'}
for cname,iso in oecd_country.items():
    for measure,concept in [('CARSA','exports_current_prices_sa_annual_level'),('VOBARSA','exports_volume_sa_annual_level')]:
        code=f'{iso}.P6.{measure}.Q'; doc,j,info=dbnomics_series('OECD','QNA',code)
        rr=[(p,v) for p,v in obs_rows(doc) if '1973-Q1'<=p<='2019-Q4']
        if j is not None: dump_json(OUT/'export_prices'/f'raw_OECD_QNA_{code.replace(".","_")}.json',j)
        oecdman.append({'country':cname,'concept':concept,'exact_series_code':f'OECD/QNA/{code}','series_label':series_label(doc),'n':len(rr),'first':rr[0][0] if rr else '', 'last':rr[-1][0] if rr else '', 'status':info.get('status')})
        for p,v in rr:
            oecd.append({'period':p,'country':cname,'concept':concept,'value':v,'source_database':'OECD Quarterly National Accounts via DBnomics','exact_series_code':f'OECD/QNA/{code}','series_label':series_label(doc),'retrieval_date':RETRIEVAL})
# Discover OECD euro-area reference-area codes and test raw P6 components.
try:
    qna_meta,_=dbnomics_dataset('OECD','QNA'); dump_json(OUT/'metadata'/'OECD_QNA_dataset_metadata.json',qna_meta)
    qdims=qna_meta.get('dimensions_values_labels') or {}
    euro_codes=[]
    for dim,dmap in qdims.items():
        if not isinstance(dmap,dict): continue
        for k,v in dmap.items():
            lab=str(v).lower()
            if ('euro area' in lab or 'euro zone' in lab) and k not in euro_codes: euro_codes.append(k)
    pd.DataFrame([{'code':x} for x in euro_codes]).to_csv(OUT/'export_prices'/'oecd_euro_area_code_candidates.csv',index=False)
    for iso in euro_codes+['EA19','EA20','EA17','EMU']:
        for measure,concept in [('CARSA','exports_current_prices_sa_annual_level'),('VOBARSA','exports_volume_sa_annual_level')]:
            code=f'{iso}.P6.{measure}.Q'; doc,j,info=dbnomics_series('OECD','QNA',code)
            rr=[(p,v) for p,v in obs_rows(doc) if '1999-Q1'<=p<='2019-Q4']
            if rr:
                if j is not None: dump_json(OUT/'export_prices'/f'raw_OECD_QNA_{code.replace(".","_")}.json',j)
                oecdman.append({'country':'Euro area','concept':concept,'exact_series_code':f'OECD/QNA/{code}','series_label':series_label(doc),'n':len(rr),'first':rr[0][0],'last':rr[-1][0],'status':info.get('status')})
                for p,v in rr:
                    oecd.append({'period':p,'country':'Euro area','concept':concept,'value':v,'source_database':'OECD Quarterly National Accounts via DBnomics','exact_series_code':f'OECD/QNA/{code}','series_label':series_label(doc),'retrieval_date':RETRIEVAL})
except Exception as e:
    dump_json(OUT/'export_prices'/'oecd_euro_discovery_error.json',{'error':repr(e)})
pd.DataFrame(oecd).to_csv(OUT/'export_prices'/'oecd_qna_export_components_raw.csv',index=False)
pd.DataFrame(oecdman).drop_duplicates().to_csv(OUT/'export_prices'/'oecd_qna_export_components_manifest.csv',index=False)

# ------------------------------------------------------------------
# 3. Portfolio-equity raw IFS series used as Figure 4 source candidates
# ------------------------------------------------------------------
port=[]; pman=[]
for ind in ['IAPE_BP6_USD','ILPE_BP6_USD','IADE_BP6_USD','ILDE_BP6_USD']:
    code=f'A.US.{ind}'; doc,j,info=dbnomics_series('IMF','IFS',code); rr=obs_rows(doc)
    if j is not None: dump_json(OUT/'portfolio'/f'raw_{code.replace(".","_")}.json',j)
    pman.append({'indicator':ind,'exact_series_code':f'IMF/IFS/{code}','series_label':series_label(doc),'n':len(rr),'first':rr[0][0] if rr else '', 'last':rr[-1][0] if rr else '','status':info.get('status')})
    for p,v in rr:
        port.append({'year':p,'value':v,'indicator':ind,'source_database':'IMF International Financial Statistics legacy snapshot via DBnomics','exact_series_code':f'IMF/IFS/{code}','series_label':series_label(doc),'retrieval_date':RETRIEVAL})
pd.DataFrame(port).to_csv(OUT/'portfolio'/'us_equity_iip_source_candidates_raw.csv',index=False)
pd.DataFrame(pman).to_csv(OUT/'portfolio'/'us_equity_iip_source_candidates_manifest.csv',index=False)

# ------------------------------------------------------------------
# 4. CKM (2002) Additional Files / pre-euro exchange-rate archive
# ------------------------------------------------------------------
ckm_urls=[
 'https://researchdatabase.minneapolisfed.org/concern/datasets/7d278t01v?locale=en',
 'https://researchdatabase.minneapolisfed.org/downloads/7d278t01v?locale=en',
 'https://researchdatabase.minneapolisfed.org/concern/datasets/765371353?locale=en',
 'https://researchdatabase.minneapolisfed.org/downloads/765371353?locale=en',
]
ckm_log=[]; discovered=[]
for u in ckm_urls:
    try:
        r=S.get(u,timeout=90,allow_redirects=True)
        ck={'requested_url':u,'final_url':r.url,'status':r.status_code,'content_type':r.headers.get('content-type',''),'bytes':len(r.content)}
        ck['sha256']=hashlib.sha256(r.content).hexdigest() if r.content else ''
        ctype=ck['content_type'].lower()
        if r.status_code==200 and ('html' in ctype or r.text[:50].lower().find('<!doctype')>=0):
            fname='landing_'+str(len(ckm_log))+'.html'; (OUT/'ckm'/fname).write_bytes(r.content)
            soup=BeautifulSoup(r.text,'html.parser')
            for a in soup.find_all('a',href=True):
                href=urljoin(r.url,a['href']); txt=' '.join(a.stripped_strings)
                if ('download' in href.lower()) or ('zip' in href.lower()) or ('file' in txt.lower()) or ('data' in txt.lower()):
                    discovered.append({'source_page':r.url,'anchor_text':txt,'url':href})
        elif r.status_code==200 and len(r.content)>1000:
            ext='.zip' if ('zip' in ctype or r.content[:2]==b'PK') else '.bin'
            fname='ckm_direct_'+str(len(ckm_log))+ext; (OUT/'ckm'/fname).write_bytes(r.content); ck['saved_file']=fname
        ckm_log.append(ck)
    except Exception as e:
        ckm_log.append({'requested_url':u,'status':'ERROR','error':repr(e)})
pd.DataFrame(ckm_log).to_csv(OUT/'ckm'/'ckm_access_log.csv',index=False)
pd.DataFrame(discovered).drop_duplicates().to_csv(OUT/'ckm'/'ckm_discovered_links.csv',index=False)
# Try discovered download links (bounded to avoid crawling site).
file_log=[]
for i,x in enumerate(discovered[:30]):
    u=x['url']
    try:
        r=S.get(u,timeout=120,allow_redirects=True)
        ctype=r.headers.get('content-type','').lower(); rec={'url':u,'final_url':r.url,'status':r.status_code,'content_type':ctype,'bytes':len(r.content)}
        if r.status_code==200 and len(r.content)>500 and 'html' not in ctype:
            name=Path(r.url.split('?')[0]).name or f'file_{i}'
            if not Path(name).suffix and (r.content[:2]==b'PK' or 'zip' in ctype): name += '.zip'
            name=re.sub(r'[^A-Za-z0-9._-]+','_',name)
            (OUT/'ckm'/name).write_bytes(r.content); rec['saved_file']=name; rec['sha256']=hashlib.sha256(r.content).hexdigest()
            if r.content[:2]==b'PK':
                try:
                    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                        rec['zip_members']=' | '.join(z.namelist())
                        exdir=OUT/'ckm'/'extracted'; exdir.mkdir(exist_ok=True); z.extractall(exdir)
                except Exception as ze: rec['zip_error']=repr(ze)
        file_log.append(rec)
    except Exception as e: file_log.append({'url':u,'status':'ERROR','error':repr(e)})
pd.DataFrame(file_log).to_csv(OUT/'ckm'/'ckm_download_attempts.csv',index=False)
# Inventory any retrieved/extracted CKM files, flag likely exchange-rate files.
inv=[]
for p in (OUT/'ckm').rglob('*'):
    if p.is_file():
        nm=p.name.lower(); inv.append({'relative_path':str(p.relative_to(OUT/'ckm')),'bytes':p.stat().st_size,'likely_exchange_rate_file':any(k in nm for k in ['exch','rate','rer','nom','data','europe','euro','country'])})
pd.DataFrame(inv).to_csv(OUT/'ckm'/'ckm_file_inventory.csv',index=False)

# ------------------------------------------------------------------
# 5. Search author's PUBLIC website/GitHub footprint for a replication package.
#    This is an audit only; absence here is not proof that private code does not exist.
# ------------------------------------------------------------------
search_rows=[]
# Website links
for u in ['https://nickcao.com/','https://nickcao.com/resources.html']:
    try:
        r=S.get(u,timeout=60); soup=BeautifulSoup(r.text,'html.parser')
        for a in soup.find_all('a',href=True):
            href=urljoin(r.url,a['href']); txt=' '.join(a.stripped_strings)
            search_rows.append({'source':'author_website','container':u,'item':txt,'url':href,'match_terms':','.join([k for k in ['code','data','replication','github','dynare','matlab','exchange'] if k in (txt+' '+href).lower()])})
    except Exception as e: search_rows.append({'source':'author_website','container':u,'item':'ERROR','url':'','match_terms':repr(e)})
# GitHub public repositories and recursive tree filename audit.
try:
    repos=S.get('https://api.github.com/users/nick-cao/repos?per_page=100',timeout=60).json()
    dump_json(OUT/'author_search'/'nick_cao_github_repositories_raw.json',repos)
    terms=['exchange','portfolio','risk','kalman','dynare','matlab','g10','homebias','home_bias']
    ext=['.mod','.m','.mat','.do','.dta','.csv','.xlsx','.xls','.jl','.py']
    hits=[]
    for repo in repos if isinstance(repos,list) else []:
        name=repo.get('name'); branch=repo.get('default_branch') or 'main'
        try:
            br=S.get(f'https://api.github.com/repos/nick-cao/{name}/branches/{branch}',timeout=30).json(); sha=((br.get('commit') or {}).get('sha'))
            if not sha: continue
            tr=S.get(f'https://api.github.com/repos/nick-cao/{name}/git/trees/{sha}?recursive=1',timeout=60).json()
            for x in tr.get('tree',[]):
                path=x.get('path',''); low=path.lower()
                if any(t in low for t in terms) or any(low.endswith(e) for e in ext):
                    hits.append({'repository':f'nick-cao/{name}','path':path,'type':x.get('type'),'size':x.get('size'),'url':x.get('url')})
        except Exception as e:
            hits.append({'repository':f'nick-cao/{name}','path':'TREE_ERROR','type':'','size':'','url':repr(e)})
    pd.DataFrame(hits).to_csv(OUT/'author_search'/'nick_cao_public_repo_candidate_files.csv',index=False)
except Exception as e:
    dump_json(OUT/'author_search'/'github_search_error.json',{'error':repr(e)})
pd.DataFrame(search_rows).to_csv(OUT/'author_search'/'author_website_link_audit.csv',index=False)

# ------------------------------------------------------------------
# 6. Summary / README
# ------------------------------------------------------------------
summary={
 'retrieval_date':RETRIEVAL,
 'belgium_historical_rows':len(flows),
 'us_total_world_rows':len(usw),
 'oecd_export_component_rows':len(oecd),
 'portfolio_rows':len(port),
 'ckm_discovered_links':len(discovered),
 'ckm_saved_files':[str(p.relative_to(OUT/'ckm')) for p in (OUT/'ckm').rglob('*') if p.is_file() and p.suffix.lower() not in ['.csv','.html']],
 'important_note':'Raw source extracts are preserved. Author-specific 2025 IFS pull, private transformed data/code, West-Germany mapping, euro splice and GDP-weight rule cannot be inferred merely from source availability.'
}
dump_json(OUT/'SUMMARY.json',summary)
readme=f'''# Cao replication: final source-gap collection\n\nRetrieval date: {RETRIEVAL}\n\nThis artifact contains raw/untransformed source extracts and metadata for the remaining public-source gaps: historical Belgium/BLEU DOTS, US total-world DOTS, export-price source series, US IIP equity candidates, CKM archive attempts/files, and a public author-code/package audit.\n\nDo not treat reconstructed OECD export deflators or any inferred splice/weighting rule as author-exact. The paper does not disclose the frozen series list, West-Germany mapping, euro splice, weighting frequency/lag convention, or Kalman implementation code.\n'''
(OUT/'README.md').write_text(readme,encoding='utf-8')
print(json.dumps(summary,indent=2))
