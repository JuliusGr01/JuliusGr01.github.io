import json, os, traceback
from pathlib import Path
import pandas as pd
import sdmx

OUT=Path('cao_patch_probe'); OUT.mkdir(exist_ok=True)
client=sdmx.Client('IMF_DATA')
queries={
 'uk_nominal_gdp':('QNEA','GBR.B1GQ.V.NSA.XDC.Q'),
 'sweden_nominal_gdp':('QNEA','SWE.B1GQ.V.NSA.XDC.Q'),
 'nz_real_gdp':('QNEA','NZL.B1GQ.Q.NSA.XDC.Q'),
 'nz_nom_hh_consumption':('QNEA','NZL.P3_S14.V.NSA.XDC.Q'),
 'france_nominal_gdp':('QNEA','FRA.B1GQ.V.NSA.XDC.Q'),
 'austria_nominal_gdp':('QNEA','AUT.B1GQ.V.NSA.XDC.Q'),
 'finland_nominal_gdp':('QNEA','FIN.B1GQ.V.NSA.XDC.Q'),
 'euro_cpi':('CPI','G163.HICP._T.IX.Q'),
 'che_export_deflator_sa':('QNEA','CHE.P6.PD.SA.IX.Q'),
 'che_export_deflator_nsa':('QNEA','CHE.P6.PD.NSA.IX.Q'),
 'bel_export_deflator_sa':('QNEA','BEL.P6.PD.SA.IX.Q'),
 'bel_export_deflator_nsa':('QNEA','BEL.P6.PD.NSA.IX.Q'),
}
summary={}
frames=[]
for name,(dataset,key) in queries.items():
    try:
        msg=client.data(dataset,key=key,params={'startPeriod':'1973-Q1','endPeriod':'2019-Q4'})
        df=sdmx.to_pandas(msg)
        # save generic representation
        if isinstance(df,pd.Series):
            d=df.rename('value').reset_index()
        else:
            d=df.reset_index()
        d['query_name']=name; d['dataset']=dataset; d['requested_key']=key
        d.to_csv(OUT/f'{name}.csv',index=False)
        frames.append(d)
        summary[name]={'dataset':dataset,'key':key,'ok':True,'rows':len(d),'columns':list(d.columns),'head':d.head(3).astype(str).to_dict('records')}
    except Exception as e:
        summary[name]={'dataset':dataset,'key':key,'ok':False,'error':repr(e),'trace':traceback.format_exc()[-1500:]}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
if frames:
    pd.concat(frames,ignore_index=True,sort=False).to_csv(OUT/'all_results.csv',index=False)
print(json.dumps(summary,indent=2)[:12000])
