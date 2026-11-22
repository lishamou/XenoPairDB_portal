"""Independent source-to-display verification and HTTP checks for a built portal."""
import argparse,csv,hashlib,json,re,urllib.request,concurrent.futures
from pathlib import Path
from decimal import Decimal

def read(p):
 with p.open() as f:return list(csv.DictReader(f,delimiter='\t'))
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(site,output,base_url=None):
 checks=[]
 def check(name,condition,detail=None):
  checks.append({'check':name,'pass':bool(condition),'detail':detail})
  assert condition,(name,detail)
 source=site/'source_data';contract=load(source/'SOURCE_MANIFEST.json')
 for n,v in contract['source_files'].items():check('Frozen source checksum '+n,sha(source/n)==v['sha256'])
 text=(site/'index.html').read_text();embed=json.loads(re.search(r'<script id="portal-data" type="application/json">(.*?)</script>',text,re.S)[1])
 release=load(site/'api/release.json')
 active={x['dataset']:load(site/x['portal_json']) for x in release['files']}
 expected={'gold':75,'atlas':1407,'surfaceome':4123,'scorecard':36,'count_coverage':6,'organ':18,'donor_masks':450,'genotypes':45,'sequence':2,'antigen_reference':8,'reference_clusters':1,'liu':8,'mapping':12,'anand':18}
 check('Active datasets and audited analysis populations',{k:v['record_count'] for k,v in active.items()}==expected)
 for k,d in active.items():
  check('Embedded API equals served API '+k,embed[k]==d)
  check('Root API mirror '+k,load(site/f'{k}.json')==d)
  downloaded=read(site/d['download'])
  clean=[{k:v for k,v in r.items() if k!='record_key'} for r in d['records']]
  check('Downloaded TSV equals API records '+k,downloaded==clean)
  check('Download checksum '+k,sha(site/d['download'])==d['sha256'])
  check('Record keys are unique '+k,len({r['record_key'] for r in d['records']})==len(clean))
  if k not in ['organ','antigen_reference']:
   check('Exact original TSV bytes '+k,(site/d['download']).read_bytes()==(source/f'{k}.tsv').read_bytes())
  else:
   check('Derived table source list '+k,len(d['sources'])>0)
 check('Organ display excludes nominal missing-feature imputation',read(site/'downloads/organ.tsv')==[r for r in read(source/'organ.tsv') if r['variant']=='formula_sequence_available'])
 for r in active['scorecard']['records']:
  T,A,R,C=[Decimal(r[k]) for k in ['T','A','R','C']]
  check('Donor additive and common denominator '+r['scenario']+' '+r['donor'],abs(T-A-R)<Decimal('0.000001') and abs(A/T-C)<Decimal('0.000000001'))
  check('Scenario population '+r['scenario']+' '+r['donor'],int(r['n_axes'])==({'L':63,'F':75}.get(r['scenario'],61)))
 mult={r['comparison']:r for r in read(source/'reference_multiplicity.tsv')}
 metrics={(r['scope'],r['background'],r['model']):r for r in read(source/'reference_metrics.tsv')}
 sens={r['cohort']:r for r in read(source/'reference_sensitivity.tsv')}
 for r in active['antigen_reference']['records']:
  cohort=r['cohort'];background=r['background']
  if cohort in sens:
   orig=sens[cohort];key=cohort+'|conditional_background_mean_p'
   check('Reference sensitivity estimate '+cohort,r['estimate']==orig['probability_superiority'])
   check('Reference sensitivity interval '+cohort,(r['ci_low'],r['ci_high'])==(orig['bootstrap_ci_low'],orig['bootstrap_ci_high']))
  else:
   orig=metrics[(cohort,background,'combined')];key='|'.join([cohort,background,'combined'])
   target='mean_score_difference' if background=='matched' else 'probability_superiority'
   check('Reference estimand/estimate '+key,r['estimand']==target and r['estimate']==orig[target])
   check('Reference interval '+key,(r['ci_low'],r['ci_high'])==(orig['ci_low'],orig['ci_high']))
  check('Reference p and 37-test q '+key,r['p']==mult[key]['p_value'] and r['q_BH_37']==mult[key]['q_BH_extended_family'])
 check('Anand family retains all 18 adjusted p values',len(active['anand']['records'])==18 and all(Decimal(r['p_Holm'])==1 for r in active['anand']['records']))
 for name in ['priority','loso_units','boundary','engineering']:
  obj=load(site/'api'/f'{name}.json')
  check('Historical endpoint retired '+name,obj['status']=='retired' and obj['records']==[] and obj['download'] is None and load(site/f'{name}.json')==obj)
 check('Legacy classifier benchmark removed from current release metadata','benchmark' not in release and 'benchmark' not in load(site/'data.json'))
 glycan=next(r for r in active['gold']['records'] if r['pair_id']=='XP004')
 source_glycan=next(r for r in read(source/'gold.tsv') if r['pair_id']=='XP004')
 check('Missing glycan scores remain missing',glycan['ISI_v2']==source_glycan['ISI_v2'] and glycan['ISI_v2'] in ['','NA','n/a'])
 check('CFH stored exception remains 0.3',next(r['ISI_v2'] for r in active['gold']['records'] if r['pair_id']=='XP075')=='0.3')
 check('Rank-missing protein retained',sum(r['rank_v2']=='' for r in active['surfaceome']['records'])==1)
 manifest={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (site/'SHA256SUMS.txt').read_text().splitlines()}
 actual={str(p.relative_to(site)) for p in site.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt'}
 check('Full deployment manifest includes every file',set(manifest)==actual)
 for p,h in manifest.items():check('Manifest checksum '+p,sha(site/p)==h)
 for path in ['assets/app.js','assets/style.css']:
  check('Runtime asset exists '+path,(site/path).is_file())
 # Published prose values are derived at runtime from these checked records.
 primary=next(r for r in active['liu']['records'] if r['analysis']=='primary_exclude_legacy8')
 check('Primary external result remains unchanged',primary['n']=='6' and primary['rho']=='-0.714285714286' and primary['p']=='0.13803')
 if base_url:
  urls=[f['download'] for f in release['files']]+[f['download'] for f in release['additional_downloads']]+[f['portal_json'] for f in release['files']]+['assets/app.js','assets/style.css','api/release.json']
  def get(p):
   with urllib.request.urlopen(base_url.rstrip('/')+'/'+p,timeout=10) as r:data=r.read();status=r.status
   return p,status,hashlib.sha256(data).hexdigest()
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(get,urls))
  for p,status,h in results:check('HTTP file matches packaged bytes '+p,status==200 and h==sha(site/p))
 output.parent.mkdir(parents=True,exist_ok=True)
 output.write_text(json.dumps({'status':'PASS','assertions':len(checks),'science_recomputed':False,'checks':checks},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':'PASS','assertions':len(checks),'report':str(output)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--site',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--base-url')
 a=p.parse_args();verify(a.site,a.output,a.base_url)
