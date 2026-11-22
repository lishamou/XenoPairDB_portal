#!/usr/bin/env python3
"""Build the static publication portal from checksummed frozen source tables.

Display transformation only: no new tests, score fitting or biological relabeling.
"""
import argparse,csv,json,hashlib,shutil
from pathlib import Path
from collections import Counter
from decimal import Decimal

STAMP='2026-11-18'
SCENARIOS={
 'M':'Mixed divergence', 'S':'Sequence divergence', 'N':'No divergence · same 61 axes',
 'E':'Sequence divergence · expression multiplier 1', 'L':'Stored ISI',
 'F':'No divergence · full catalogue'}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 with p.open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f,delimiter='\t'))
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n',encoding='utf-8')
def tsv(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else [],delimiter='\t',lineterminator='\n')
  writer.writeheader();writer.writerows(rows)

def build(source,out,templates):
 assert not out.exists(),'Output must be a new directory'
 contract=json.loads((source/'SOURCE_MANIFEST.json').read_text())
 for name,spec in contract['source_files'].items():assert sha(source/name)==spec['sha256'],name
 out.mkdir(parents=True)
 shutil.copytree(source,out/'source_data')
 shutil.copytree(templates,out/'code/templates')
 shutil.copy2(Path(__file__),out/'code/build_portal.py')
 if Path(__file__).with_name('verify_portal.py').is_file():
  shutil.copy2(Path(__file__).with_name('verify_portal.py'),out/'code/verify_portal.py')
 for name in ['LICENSE','DATA_LICENSE.md','THIRD_PARTY_NOTICES.md']:
  shutil.copy2(source/name,out/name)
 datasets={}
 def add(name,label,group,records,columns,note,filter_key=None,default_filter=None,id_key=None,source_names=(),exact=False):
  if exact:
   assert len(source_names)==1
   p=out/'downloads'/f'{name}.tsv';p.parent.mkdir(exist_ok=True)
   shutil.copy2(source/source_names[0],p)
  else:tsv(out/'downloads'/f'{name}.tsv',records)
  # Record keys only affect deep links; they do not alter original values or TSV downloads.
  enriched=[]
  for i,r in enumerate(records):
   key=str(r[id_key]) if id_key else hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:20]
   enriched.append(dict(r,record_key=key))
  assert len({r['record_key'] for r in enriched})==len(records),(name,'ambiguous record key')
  datasets[name]={'dataset':name,'label':label,'group':group,'description':note,
   'record_count':len(records),'columns':columns,'filter_key':filter_key,'default_filter':default_filter,
   'download':f'downloads/{name}.tsv','sha256':sha(out/'downloads'/f'{name}.tsv'),
   'sources':[{'file':f'source_data/{n}',**contract['source_files'][n]} for n in source_names],
   'release':'XenoPairDB publication portal','release_date':STAMP,'records':enriched}

 gold=read(source/'gold.tsv');registry=read(source/'axis_registry.tsv')
 lookup={}
 for r in registry:
  entity=json.loads(r['entity_key']);lookup[tuple(entity)]=r['stable_axis_id']
 for r in gold:assert tuple(r[k] for k in ['pig_gene','human_partner','direction','phenotype']) in lookup
 add('gold','Molecular axes','Catalogue',gold,['pair_id','pig_gene','human_partner','direction','evidence','phenotype','ISI_v2'],
  '75 directional molecular axes: 59 direct-evidence, 4 disputed and 12 compatibility-control annotations. Evidence applies to the recorded endpoint. ISI is the stored-score scenario; missing scores remain unavailable. Molecular features and assay populations can differ.',
  'evidence',id_key='pair_id',source_names=['gold.tsv'],exact=True)
 atlas=read(source/'atlas.tsv')
 add('atlas','Interaction candidates','Candidates',atlas,['rank','ligand','receptor','tier2_score','source','qc_flag'],
  '1,407 membrane-associated interaction records represent 1,348 unordered gene pairs. Pair scores nominate follow-up assays; gene-pair overlap does not establish species direction or functional equivalence. Sequon counts describe sequence potential, not measured glycan occupancy. Selected secreted ligands are included; this is not a comprehensive secreted-ligand screen.',
  'qc_flag',id_key='rank',source_names=['atlas.tsv'],exact=True)
 proteins=read(source/'surfaceome.tsv')
 add('surfaceome','Antigen priorities','Candidates',proteins,['gene','acc','human_gene','perc_id','antigenicity_v2','rank_v2'],
  '4,123 protein records, of which 4,122 have a fixed antigen-priority rank. An unavailable rank means ineligible. Priorities nominate antibody-focused experiments; sequon features do not establish glycan occupancy, human-antibody specificity or pathogenicity. Fixed catalogue scores are retained without refitting.',
  id_key='acc',source_names=['surfaceome.tsv'],exact=True)
 scorecards=read(source/'scorecard.tsv')
 for r in scorecards:
  T,A,R,C=[Decimal(r[k]) for k in ['T','A','R','C']]
  assert abs(T-A-R)<Decimal('0.000001')
  assert T and abs(A/T-C)<Decimal('0.000000001')
 add('scorecard','Weighted coverage','Donor coverage',scorecards,['scenario','donor','n_axes','T','A','R','C','units'],
  'Direct-target masks partition the score into genetically addressed (A) and residual (R) components: T=A+R and coverage=A/T before display rounding. M/S/N/E use the same 61 sequence-available axes; L contains 63 numeric stored-score entries; F uses all 75 axes in different units. Switch scenarios to inspect sensitivity. Genetic targeting is not measured functional rescue or clinical superiority. GTKO targets an unscored glycan axis, which remains visible in axis-count coverage.',
  'scenario','M',source_names=['scorecard.tsv'],exact=True)
 add('count_coverage','Axis-count coverage','Donor coverage',read(source/'count_coverage.tsv'),
  ['donor','addressed_resource_axes','resource_axes','addressed_non_control_axes','non_control_axes','axis_count_coverage_fraction','addressed_unscored_non_control_axes'],
  'Counts use explicit full-catalogue (75) and non-control (63) denominators. The percentage column is targeted non-control axes / 63. Sequence-missing targets remain visible. Counts describe direct genetic targeting, not restoration of function.',
  source_names=['count_coverage.tsv'],exact=True)
 organ=[r for r in read(source/'organ.tsv') if r['variant']=='formula_sequence_available']
 add('organ','Organ-relevant subsets','Donor coverage',organ,
  ['organ','donor','n_axes','n_scored','n_missing_noncontrol','T_scored','A_scored','R_scored','C_scored'],
  'Kidney, heart and liver subsets use recorded tissue/system annotations and available sequence features. Total subset axes include missing records; n_scored is the weighted denominator. These are annotation strata, not organ-expression-calibrated risk estimates. Equal liver scores can follow from masks and subset membership.',
  'organ',source_names=['organ.tsv'])
 add('donor_masks','Direct-target mappings','Donor coverage',read(source/'donor_masks.tsv'),
  ['donor','pair_id','mask','edits','functional_rescue'],
  'One direct-target mask per donor–axis combination. A value of 1 denotes a reported direct genetic-targeting edge; 0 denotes no direct edge under this frozen mapping. Neither value establishes functional rescue or biological absence.',
  'donor',source_names=['donor_masks.tsv'],exact=True)
 add('genotypes','Reported donor edits','Donor coverage',read(source/'genotypes.tsv'),
  ['genotype','edit_type','gene','tier1_pair','literature_basis'],
  'Reported donor-edit definitions are retained as source annotations. Current molecular targeting is represented separately in Direct-target mappings. Presence of an edit does not establish its individual benefit or interactions with other edits.',
  'genotype',source_names=['genotypes.tsv'],exact=True)
 add('sequence','Sequence-feature association','Evidence',read(source/'sequence.tsv'),
  ['scope','n','n_noncontrol','n_control','auroc','auroc_ci_low','auroc_ci_high','average_precision','prevalence'],
  'The fixed severity-free sequence feature is compared with catalogue annotations on 61 available axes. Intervals use dependency-proxy bootstrap resampling and are conditional on this selected catalogue. Severity-containing ISI and severity-alone AUROC against these labels are circular because control severity is defined as zero. This sequence-only association is not independent functional or clinical validation.',
  source_names=['sequence.tsv'],exact=True)
 mult=read(source/'reference_multiplicity.tsv');q={r['comparison']:r for r in mult}
 refs=[]
 for r in read(source/'reference_metrics.tsv'):
  if r['model']!='combined' or r['background'] not in ['full_untested','matched']:continue
  key='|'.join(r[k] for k in ['scope','background','model'])
  assert Decimal(q[key]['p_value'])==Decimal(r['p_value'])
  target='mean_score_difference' if r['background']=='matched' else 'probability_superiority'
  refs.append({'cohort':r['scope'],'background':r['background'],'n_reference':r['n_positive'],'n_background':r['n_background'],
   'estimand':target,'estimate':r[target],'ci_low':r['ci_low'],'ci_high':r['ci_high'],
   'p':r['p_value'],'q_BH_37':q[key]['q_BH_extended_family'],'test':r['test'],'ci_method':r['ci_method']})
 for r in read(source/'reference_sensitivity.tsv'):
  key=r['cohort']+'|conditional_background_mean_p'
  assert Decimal(q[key]['p_value'])==Decimal(r['conditional_background_mean_p'])
  refs.append({'cohort':r['cohort'],'background':'full_untested','n_reference':r['n_positive'],'n_background':r['n_background'],
   'estimand':'probability_superiority','estimate':r['probability_superiority'],
   'ci_low':r['bootstrap_ci_low'],'ci_high':r['bootstrap_ci_high'],'p':r['conditional_background_mean_p'],
   'q_BH_37':q[key]['q_BH_extended_family'],'test':'one_sided_background_mean_Monte_Carlo',
   'ci_method':'protein_percentile_bootstrap_conditional_on_selected_assay_sources'})
 add('antigen_reference','Reference-set enrichment','Evidence',refs,
  ['cohort','background','n_reference','n_background','estimand','estimate','ci_low','ci_high','p','q_BH_37'],
  'Literature-reference annotations are compared with untested background proteins, not a validated antigen-negative class. Full-background intervals target probability of superiority; matched intervals target the mean-score difference. The p values test mean enrichment and do not test the probability-of-superiority estimand. BH q values use the frozen 37-test family. Shared publications and heterogeneous assays limit inference. CD55-specific antigen support is unresolved; the n=7 exclusion is separate from excluding all three complement regulators (n=5).',
  'background',source_names=['reference_metrics.tsv','reference_sensitivity.tsv','reference_multiplicity.tsv'])
 add('reference_clusters','Source-cluster sensitivity','Evidence',read(source/'reference_clusters.tsv'),
  ['scope','n_positive','publication_clusters','n_background','probability_superiority','ci_low','ci_high'],
  'A source-cluster sensitivity addresses shared publications among the reference annotations. Only four source groups are available, including one with unresolved antigen-specific support. This is a conditional resampling range, not an independent validation cohort.',
  source_names=['reference_clusters.tsv'],exact=True)
 add('liu','Liu external assessment','Evidence',read(source/'liu.tsv'),
  ['analysis','n','rho','ci_low','ci_high','p','q_BH_secondary'],
  'Fixed antigen-priority scores were compared with supplied peptide-median log2 enrichment. The primary observed-control comparison contains 6 proteins and 7 unique peptides. The small selected overlap and missing controls make this inconclusive: it did not support the expected positive association and does not establish absence of antigenicity. Measurement replicates are not independent human serum donors. The primary hypothesis is separate from the available secondary-test family.',
  source_names=['liu.tsv'],exact=True)
 add('mapping','Liu mapping sensitivity','Evidence',read(source/'mapping.tsv'),
  ['scheme','endpoint','n','rho','ci_low','ci_high','p','q_BH_mapping_family','new_genes'],
  'M0 is the primary mapping. M1–M5 are post hoc identifier/protein-group sensitivities with fixed scores and endpoint rules. Same-gene group resolution adds RPN1 to the observed-control cohort (7 proteins); ambiguous multi-gene groups are not forced onto a scored member. Source-model fold changes are a separate sensitivity when controls are missing; missing controls are never measured zero. None of these sensitivities supported the expected positive association. Mapping-family BH correction is distinct from Liu secondary comparisons.',
  'endpoint','observed_control',source_names=['mapping.tsv'],exact=True)
 add('anand','Anand functional examples','Evidence',read(source/'anand.tsv'),
  ['comparison','endpoint','species','time','treatment','reference','n_treatment','n_reference','difference','ci_low','ci_high','p','p_Holm','unit'],
  'Reanalysis of already-published source data connects engineering designs with antibody/complement and cell-injury endpoints. Cell-source IDs, not technical wells, are analysis units. Human and cynomolgus serum and exposure times remain separate. Intervals use model-dependent Welch or paired t approximations; exact tests use different assumptions. All 18 exploratory contrasts have Holm-adjusted p=1.00. The bundled design does not isolate individual edit benefits or synergy, and pooled serum does not represent a donor cohort.',
  'species',source_names=['anand.tsv'],exact=True)
 # Supplemental measured observations preserve source values exactly.
 extras=[]
 for name in ['liu_cohort.tsv','mapping_cohort.tsv','anand_points.tsv','axis_registry.tsv','reference_multiplicity.tsv']:
  shutil.copy2(source/name,out/'downloads'/name)
  extras.append({'name':name,'download':'downloads/'+name,'sha256':sha(out/'downloads'/name),'record_count':len(read(source/name))})
 scope={'axes':len(gold),'evidence':dict(Counter(r['evidence'] for r in gold)),
  'sequence_axes':int(read(source/'sequence.tsv')[0]['n']),
  'atlas_records':len(atlas),'unique_unordered_pairs':len({tuple(sorted([r['ligand'],r['receptor']])) for r in atlas}),
  'protein_universe':len(proteins),'ranked_proteins':sum(bool(r['rank_v2']) for r in proteins),
  'donor_designs':len({r['donor'] for r in scorecards})}
 assert scope['evidence']=={'direct':59,'disputed':4,'control':12}
 assert scope['unique_unordered_pairs']==1348 and scope['ranked_proteins']==4122
 release={'release':'XenoPairDB publication portal','portal_build_date':STAMP,
  'science_archive_doi':contract['science_archive_doi'],'concept_doi':contract['concept_doi'],
  'scope':scope,'data_license':'Per-file source conditions; see DATA_LICENSE.md and THIRD_PARTY_NOTICES.md',
  'code_license':'MIT','files':[{'dataset':k,'portal_json':'api/'+k+'.json',
   'download':d['download'],'record_count':d['record_count'],'sha256':d['sha256']} for k,d in datasets.items()],
  'additional_downloads':extras,'interpretation':'Exploratory evidence navigation and direct-target coverage; no clinical donor ranking.'}
 retired={}
 for name in ['priority','loso_units','boundary','engineering']:
  retired[name]={'dataset':name,'status':'retired','record_count':0,'records':[],
   'download':None,'description':('This historical presentation is retired. Use the current evidence and coverage views. No historical metric is presented as current validation.' if name in ['priority','loso_units'] else 'Historical contextual endpoint is not part of the current archived analysis package or the 75-axis denominator. It is not included in the updated publication portal. No original evidence label is changed.'),
   'replacement':['api/scorecard.json','api/sequence.json','api/antigen_reference.json'],
   'release_date':STAMP}
 payload={**datasets,**retired,'release':release,'downloads':{'files':release['files'],'additional_downloads':extras}}
 for name,obj in payload.items():write(out/'api'/f'{name}.json',obj);write(out/f'{name}.json',obj)
 for name in datasets.keys()|retired.keys():
  schema={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object',
   'required':['dataset','record_count','records'],'properties':{'dataset':{'const':name},'record_count':{'type':'integer','minimum':0},'records':{'type':'array','items':{'type':'object'}}}}
  for folder in ['api/schemas','schemas']:write(out/folder/f'{name}.schema.json',schema)
 write(out/'data.json',{'release':release['release'],'scope':scope,'science_archive_doi':contract['science_archive_doi'],'concept_doi':contract['concept_doi']})
 for folder in ['i18n/','']:
  write(out/(folder+'en.json'),{'title':'XenoPairDB','language':'en','isi':'ISI','antigen_priority':'Antigen-priority score','coverage':'Direct-target coverage'})
 html=(templates/'index.html').read_text()
 embedded=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e')
 html=html.replace('__PORTAL_DATA__',embedded)
 (out/'index.html').write_text(html)
 (out/'assets').mkdir(exist_ok=True)
 shutil.copy2(templates/'app.js',out/'assets/app.js');shutil.copy2(templates/'style.css',out/'assets/style.css')
 (out/'.nojekyll').write_text('')
 (out/'README.md').write_text('''# XenoPairDB portal

An evidence-graded resource for pig–human molecular axes, candidate prioritization and donor-target coverage. This static portal uses the same frozen scientific results as the revised article.

Data and code archive: https://doi.org/10.5281/zenodo.24221712 (all versions). Scientific payload used here: https://doi.org/10.5281/zenodo.24221713 (specific archived version). This website update does not create a new Zenodo science version.

## Browse and reuse

Open index.html directly for offline browsing, or serve this complete repository with GitHub Pages. The page has no third-party scripts, fonts, analytics or network dependencies for browsing. Dataset selection, search, filters, sorting, pagination, details and filtered TSV export work offline. External source links need an internet connection.

api/ contains JSON endpoints; downloads/ contains actual TSV files. Paths inside metadata are relative to the portal root. Root-level JSON mirrors preserve existing links. API schemas describe the updated presentation; the retired priority and loso_units endpoints return status=retired and zero records. Their historical validation claims are not retained as current results.

## Rebuild the presentation

Python standard library only. From this repository run:

    python3 code/build_portal.py --source-dir source_data --template-dir code/templates --output-dir /absolute/path/to/new_portal

The output directory must not exist. Every source_data file is verified against SOURCE_MANIFEST.json before building. Rebuilding transforms and joins frozen tables for display; it does not run the underlying scientific analyses. To reproduce those analyses use the exact Zenodo science archive and its documented environment.

## Interpretation and licenses

Direct genetic targeting is not measured functional rescue. Parameter sensitivity, catalogue annotation association, reference-set enrichment, proteomic enrichment, complement deposition and cell injury are distinct endpoints. The resource supports evidence tracing and selection of follow-up assays; independent candidate experiments and clinical-outcome validation remain necessary.

User-facing field names follow the article. Original raw column names and source values are retained in source_data and in exact-source TSVs; DATA_DICTIONARY.md explains the aliases and derived display tables. Missing values are not converted to zero. No weighting, evidence or control labels were adjusted for this portal.

Code is MIT. Original project data are CC BY 4.0 subject to upstream terms; Liu-derived files retain the source CC BY-NC 4.0 restriction. DATA_LICENSE.md and THIRD_PARTY_NOTICES.md describe the source archive conditions. This repository redistributes selected tables and derived summaries, not the full upstream workbooks or literature. Cite the original studies when reusing their results.

The SHA256SUMS.txt manifest covers every delivered file except itself. Portal build date: 2026-11-18.
''')
 (out/'api/README.md').write_text('''# XenoPairDB JSON endpoints

Each active dataset has records, record_count, sources, a TSV download path and its SHA-256. Record keys support unique deep links without altering original identifiers. Download paths are relative to the portal root. Root JSON paths mirror api/ for compatibility. release.json lists the current files and explicit denominators; no historic antigen-classifier benchmark is exposed as validation. priority.json and loso_units.json are retired status endpoints. See the root README and DATA_DICTIONARY.md for rebuild and interpretation.
''')
 (out/'DATA_DICTIONARY.md').write_text((source/'SCIENCE_DATA_DICTIONARY.md').read_text()+'''

## Portal display transformations

- UI label ISI reads raw ISI_v2. Raw ISI is an earlier stored intermediate and is labeled separately in record details. Antigen-priority score/rank read antigenicity_v2/rank_v2. Sequence values in different source tables are not silently substituted for one another.
- scorecard.tsv preserves all 36 frozen scenario–donor rows. M/S/N/E use 61 axes; stored-score L uses 63 numeric entries; full-catalogue F uses 75 axes in different units. C is a fraction in TSV/JSON and a percentage in the UI. n_axes includes zero-score controls.
- count_coverage.tsv preserves the original six rows with separate 75-axis and 63-non-control denominators. No clinical risk or rescue percentage is inferred.
- organ.tsv is a display selection of formula_sequence_available from the frozen organ table (18 rows). Its score definition corresponds to the available-sequence mixed-candidate organ subset reported in the SI; the archived variant name is preserved. Other organ parameter scenarios remain in source_data/organ.tsv and the science archive.
- antigen_reference.tsv selects combined-score full-background and matched comparisons plus the two source-evidence sensitivities. Its q_BH_37 is joined from the frozen 37-test multiplicity table after checking the same p value and comparison key. The earlier 34-test q column in source_data/reference_metrics.tsv is retained only as archived provenance and is not used in the current display. No p or q value is recalculated here. Source-cluster intervals have their own table.
- liu.tsv and mapping.tsv retain separate primary/secondary and post hoc mapping families. M0 is primary; M1–M5 are mapping sensitivities. The fixed antigen score is distinct from the reconstructed reference-set score.
- anand.tsv keeps all 18 exploratory contrasts, cell-source IDs, assay duration, species, units, approximate intervals, exact tests and Holm-adjusted p values. Human pooled serum is not an independent serum-donor cohort.
- record_key is a presentation identifier (original ID when unique, otherwise a deterministic row-content hash), not a new scientific axis ID. Exact source TSV downloads do not add this key. axis_registry.tsv preserves the original entity keys and stable IDs.
- Numeric formatting affects UI precision only. JSON/TSV retain source strings; NA, n/a and empty values render as unavailable, never zero. Filters, sorting and filtered export do not change weights, labels, eligibility or inferential results.
''')
 # Deterministic complete manifest; generated API and offline payload share the same objects.
 manifest={str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
 (out/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in manifest.items()))
 return release

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--template-dir',type=Path,required=True)
 args=p.parse_args();r=build(args.source_dir.resolve(),args.output_dir.resolve(),args.template_dir.resolve())
 print(json.dumps({'status':'BUILT','datasets':len(r['files']),'output':str(args.output_dir),'scope':r['scope']},ensure_ascii=False))
