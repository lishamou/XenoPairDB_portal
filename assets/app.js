'use strict';
(() => {
const BUNDLE=JSON.parse(document.getElementById('portal-data').textContent);
const release=BUNDLE.release;
const datasets=Object.fromEntries(Object.entries(BUNDLE).filter(([,v])=>v.records&&v.status!=='retired'));
const $=id=>document.getElementById(id);
const esc=x=>String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const missing=x=>x===null||x===undefined||['','NA','N/A','n/a','NaN'].includes(String(x));
const scenarios={M:'Mixed divergence (61 axes)',S:'Sequence divergence (61 axes)',N:'No divergence (same 61 axes)',E:'Expression multiplier 1 (61 axes)',L:'Stored ISI (63 numeric entries)',F:'No divergence (full 75 axes)'};
const labels={pair_id:'Axis ID',pig_gene:'Porcine molecule',human_partner:'Human partner / response',direction:'Direction',evidence:'Evidence annotation',phenotype:'Functional endpoint',ISI_v2:'ISI',ISI:'Earlier stored intermediate',ISI_v1:'Earlier stored intermediate',identity:'Catalogue identity (%)',rank:'Candidate rank',ligand:'Ligand',receptor:'Receptor',tier2_score:'Pair priority score',source:'Source',qc_flag:'Sequence QC flag',gene:'Gene',acc:'Porcine accession',human_gene:'Human gene',perc_id:'Catalogue identity (%)',antigenicity_v2:'Antigen-priority score',rank_v2:'Antigen-priority rank',scenario:'Scoring scenario',donor:'Donor design',n_axes:'Included axes',T:'Total score (T)',A:'Addressed score (A)',R:'Residual score (R)',C:'Weighted coverage (%)',units:'Score units',addressed_resource_axes:'Targeted axes / 75',resource_axes:'Resource axes',addressed_non_control_axes:'Targeted non-control axes',non_control_axes:'Non-control axes',axis_count_coverage_fraction:'Non-control count coverage (%)',addressed_unscored_non_control_axes:'Targeted unscored non-controls',organ:'Organ annotation',n_scored:'Scored axes',n_missing_noncontrol:'Unscored non-controls',T_scored:'Total score (T)',A_scored:'Addressed score (A)',R_scored:'Residual score (R)',C_scored:'Weighted coverage (%)',mask:'Direct-target mask',edits:'Reported targeting edit',functional_rescue:'Functional rescue',genotype:'Donor design',edit_type:'Edit type',tier1_pair:'Reported axis mapping',literature_basis:'Source annotation',scope:'Analysis population',n:'Analysis units (n)',n_noncontrol:'Non-controls',n_control:'Controls',auroc:'Sequence-only AUROC',auroc_ci_low:'95% interval lower',auroc_ci_high:'95% interval upper',average_precision:'Average precision',prevalence:'Non-control prevalence',cohort:'Reference subset',background:'Background',n_reference:'Reference proteins',n_background:'Background proteins',estimand:'Interval estimand',estimate:'Estimate',ci_low:'95% interval lower',ci_high:'95% interval upper',p:'Exact / permutation p',q_BH_37:'BH q (37-test family)',test:'Test',ci_method:'Interval method',n_positive:'Reference proteins',publication_clusters:'Source groups',probability_superiority:'Probability of superiority',analysis:'Comparison',rho:'Spearman rho',q_BH_secondary:'BH q (secondary family)',scheme:'Mapping scheme',endpoint:'Measured endpoint',q_BH_mapping_family:'BH q (mapping family)',new_genes:'Additional target accession',species:'Serum species',time:'Exposure',treatment:'Treatment / blockade',reference:'Reference condition',n_treatment:'Treatment / paired n',n_reference:'Reference / paired n',difference:'Effect difference',p_Holm:'Holm p (18 contrasts)',unit:'Effect unit',mean_treatment:'Treatment mean',mean_reference:'Reference mean',treatment_IDs:'Treatment cell-source IDs',reference_IDs:'Reference cell-source IDs',record_key:'Record link key'};
const aliases={sequence_available:'Sequence available',exclude_disputed:'Excluding disputed axes',historical8:'Literature-reference set (n=8)',exclude_complement5:'Excluding CD46/CD55/CD59',direct_human2:'Human-antibody study subset (n=2)',exclude_unverified_CD55:'Excluding CD55 (n=7)',human_antibody_supported6:'Human-antibody-supported sensitivity (n=6)',full_untested:'Full untested background',matched:'Conservation / length matched',probability_superiority:'Probability of superiority',mean_score_difference:'Mean-score difference',observed_control:'Observed controls',source_model_FC:'Source-model fold-change sensitivity',human:'Human',cyno:'Cynomolgus',CDC:'Serum-mediated cell injury',C3b:'Complement C3b deposition',CDC_ED4:'Cell injury · Extended Data 4',C3b_blocking:'C3b · regulator blockade',percent_CytotoxRed_positive:'Percentage points (CytotoxRed+ cells)',weighted_divergence_percentage:'Weighted-divergence units',severity_evidence_expression:'Severity–evidence–expression units',legacy_stored:'Stored-score units',MFI_x1000:'Thousand MFI units',percentage_points:'Percentage points',UNKNOWN:'Unknown',pig_missing_identity:'Sequence missing'};
let current='gold',rows=[],filtered=[],page=1,pageSize=50,sortKey='',sortDir=1,request=0;
function fieldLabel(k){if(current==='antigen_reference'&&k==='n_reference')return 'Reference proteins';return labels[k]||k.replaceAll('_',' ')}
function valueText(k,v,r={}){
 if(missing(v))return '—';
 if(k==='scenario')return scenarios[v]||v;
 if(k==='direction')return {'pig->human':'Pig → human','pig<-human':'Human → pig'}[v]||v;
 if(['C','C_scored','axis_count_coverage_fraction','count_coverage_noncontrol'].includes(k))return (Number(v)*100).toFixed(2);
 if(['p','p_value','p_Holm','q_BH_37','q_BH_secondary','q_BH_mapping_family'].includes(k))return Number(v)<0.001?Number(v).toPrecision(3):String(Number(Number(v).toFixed(6)));
 if(['T','A','R','T_scored','A_scored','R_scored','tier2_score'].includes(k))return Number(v).toFixed(2);
 if(['rho','auroc','auroc_ci_low','auroc_ci_high','average_precision','prevalence','probability_superiority','estimate','ci_low','ci_high','difference','antigenicity_v2','mean_treatment','mean_reference'].includes(k))return Number(v).toFixed(3);
 if(['rank_v2'].includes(k))return String(Number(v));
 return aliases[v]||String(v);
}
function numeric(v){return !missing(v)&&/^[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?$/i.test(String(v))}
function renderGroups(){
 const groups=[...new Set(Object.values(datasets).map(d=>d.group))];
 $('groups').innerHTML=groups.map(g=>`<button class="${g===datasets[current].group?'active':''}" aria-pressed="${g===datasets[current].group}" data-group="${esc(g)}">${esc(g)}</button>`).join('');
 $('groups').querySelectorAll('button').forEach(b=>b.onclick=()=>select(Object.keys(datasets).find(k=>datasets[k].group===b.dataset.group)));
 $('tabs').innerHTML=Object.entries(datasets).filter(([,d])=>d.group===datasets[current].group).map(([k,d])=>`<button class="${k===current?'active':''}" aria-pressed="${k===current}" data-dataset="${k}">${esc(d.label)} <small>${d.record_count.toLocaleString()}</small></button>`).join('');
 $('tabs').querySelectorAll('button').forEach(b=>b.onclick=()=>select(b.dataset.dataset));
}
async function get(name){
 const bundled=BUNDLE[name];
 if(location.protocol==='file:')return bundled;
 try{const r=await fetch(`api/${name}.json`,{cache:'no-cache'});if(r.ok){const online=await r.json();if(JSON.stringify(online)===JSON.stringify(bundled))return online;}}
 catch(_){/* The exact bundled snapshot remains available offline. */}
 $('status').textContent='Showing the frozen data snapshot bundled with this page.';
 return bundled;
}
async function select(name,key=null){
 if(!datasets[name])name='gold';
 const version=++request;current=name;renderGroups();
 ['search','filter','reset','export','pageSize'].forEach(id=>$(id).disabled=true);
 const d=await get(name);if(version!==request)return;
 rows=d.records;page=1;sortKey='';sortDir=1;$('search').value='';$('detail').hidden=true;
 $('datasetTitle').textContent=d.label;$('datasetIntro').textContent=d.description;
 $('datasetDownload').href=d.download;$('datasetDownload').setAttribute('download',d.download.split('/').pop());
 $('filterLabel').hidden=!d.filter_key;
 $('filter').innerHTML='<option value="">All records</option>'+(d.filter_key?[...new Set(rows.map(r=>r[d.filter_key]).filter(x=>!missing(x)))].sort().map(v=>`<option value="${esc(v)}">${esc(valueText(d.filter_key,v))}</option>`).join(''):'');
 if(d.default_filter)$('filter').value=d.default_filter;
 $('tableHint').textContent=name==='antigen_reference'?'Intervals and p values can target different quantities; see the analysis note. Select a row for full precision.':'Select a row for source fields and full precision. Scroll the table horizontally to see all columns.';
 render();
 ['search','filter','reset','export','pageSize'].forEach(id=>$(id).disabled=false);
 if(key){const found=rows.find(r=>r.record_key===key||String(r.pair_id||r.acc||r.rank||'')===key);if(found)showDetail(found);}
 else history.replaceState(null,'',`#dataset=${name}`);
}
function render(){
 const d=datasets[current],q=$('search').value.toLowerCase().trim(),f=$('filter').value;
 filtered=rows.filter(r=>(!q||Object.values(r).join(' ').toLowerCase().includes(q))&&(!f||r[d.filter_key]===f));
 if(sortKey)filtered.sort((a,b)=>{
  const av=a[sortKey],bv=b[sortKey];if(missing(av)&&missing(bv))return 0;if(missing(av))return 1;if(missing(bv))return -1;
  return (numeric(av)&&numeric(bv)?Number(av)-Number(bv):String(av).localeCompare(String(bv),undefined,{numeric:true}))*sortDir;
 });
 const pages=Math.max(1,Math.ceil(filtered.length/pageSize));page=Math.min(Math.max(1,page),pages);
 $('thead').innerHTML='<tr>'+d.columns.map(k=>`<th scope="col" aria-sort="${sortKey===k?(sortDir===1?'ascending':'descending'):'none'}"><button data-sort="${k}">${esc(current==='antigen_reference'&&k==='p'?'Monte Carlo mean-enrichment p':fieldLabel(k))}<span aria-hidden="true">${sortKey===k?(sortDir===1?'↑':'↓'):'↕'}</span></button></th>`).join('')+'</tr>';
 $('thead').querySelectorAll('button').forEach(b=>b.onclick=()=>{sortDir=sortKey===b.dataset.sort?-sortDir:1;sortKey=b.dataset.sort;render()});
 const start=(page-1)*pageSize,view=filtered.slice(start,start+pageSize);
 $('tbody').innerHTML=view.map((r,i)=>`<tr tabindex="0" data-row="${i}" aria-label="Open record ${esc(r.pair_id||r.gene||r.donor||r.analysis||i+1)}">`+d.columns.map(k=>{
  const text=valueText(k,r[k],r);let content=esc(text);
  if(k==='evidence')content=`<span class="badge ${esc(r[k])}">${esc(text)}</span>`;
  return `<td class="${missing(r[k])?'empty':numeric(r[k])?'number':''}" title="${esc(missing(r[k])?'Unavailable':r[k])}">${content}</td>`;
 }).join('')+'</tr>').join('')||`<tr><td colspan="${d.columns.length}">No matching records. Reset the search or filter to browse this dataset.</td></tr>`;
 $('tbody').querySelectorAll('[data-row]').forEach(tr=>{const open=()=>showDetail(view[Number(tr.dataset.row)]);tr.onclick=open;tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();open();}}});
 $('pageInfo').textContent=`${filtered.length.toLocaleString()} of ${rows.length.toLocaleString()} records · Page ${page} of ${pages}`;
 $('prev').disabled=page<=1;$('next').disabled=page>=pages;
}
function sourceLink(v){
 if(/^\d{5,10}$/.test(v))return `<a href="https://pubmed.ncbi.nlm.nih.gov/${esc(v)}/">${esc(v)}</a>`;
 if(/^10\.\d{4,9}\/[^\s]+$/.test(v))return `<a href="https://doi.org/${esc(v)}">${esc(v)}</a>`;
 return esc(v);
}
function showDetail(r){
 $('detail').hidden=false;
 $('detail').innerHTML='<div class="detail-heading"><h4>Record details · full source precision</h4><button class="secondary" id="closeDetail">Close</button></div>'+
 `<p>${esc(datasets[current].label)} · <a href="${esc(datasets[current].download)}" download>Download full table</a></p><dl>`+
 Object.entries(r).map(([k,v])=>`<dt>${esc(fieldLabel(k))}</dt><dd>${missing(v)?'— (unavailable)':k==='source'?sourceLink(String(v)):esc(String(v))}</dd>`).join('')+'</dl>';
 $('closeDetail').onclick=()=>{$('detail').hidden=true;};
 history.replaceState(null,'',`#dataset=${current}&id=${encodeURIComponent(r.record_key)}`);
}
function exportFiltered(){
 const cols=Object.keys(rows[0]||{}).filter(k=>k!=='record_key');
 const cell=v=>/[\t\r\n"]/.test(String(v??''))?'"'+String(v??'').replaceAll('"','""')+'"':String(v??'');
 const data=cols.join('\t')+'\n'+filtered.map(r=>cols.map(k=>cell(r[k])).join('\t')).join('\n')+'\n';
 const url=URL.createObjectURL(new Blob([data],{type:'text/tab-separated-values;charset=utf-8'}));
 const a=document.createElement('a');a.href=url;a.download=`XenoPairDB_${current}_filtered.tsv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
function evidenceCards(){
 const ref=BUNDLE.antigen_reference.records.find(r=>r.cohort==='historical8'&&r.background==='full_untested');
 const liu=BUNDLE.liu.records.find(r=>r.analysis==='primary_exclude_legacy8');
 const mapped=BUNDLE.mapping.records.find(r=>r.scheme==='M4'&&r.endpoint==='observed_control');
 const c3=BUNDLE.anand.records.find(r=>r.comparison==='C3b_human_30min_3KO.7TG_minus_3KO');
 const injury=BUNDLE.anand.records.find(r=>r.comparison==='CDC_human_45min_3KO.7TG_minus_3KO');
 const card=(title,result,note,link,source)=>`<article class="evidence-card"><h3>${title}</h3><p class="result">${result}</p><p>${note}</p><a href="#browser" data-open="${link}">Inspect the results →</a>${source?`<p><a href="${source[0]}">${source[1]}</a></p>`:''}</article>`;
 $('evidenceCards').innerHTML=
 card('Reference-set enrichment',`${ref.n_reference} reference proteins · ${Number(ref.n_background).toLocaleString()} untested proteins<br>Probability of superiority ${Number(ref.estimate).toFixed(3)} (${Number(ref.ci_low).toFixed(3)}–${Number(ref.ci_high).toFixed(3)})`,
 'The conditional protein-bootstrap interval describes reference-set enrichment. Reference annotations span different assays; the untested background is not an antigen-negative class. This reconstructed score differs from the fixed catalogue predictor.','antigen_reference')+
 card('Public proteomics · Liu',`${liu.n} proteins · Spearman rho ${Number(liu.rho).toFixed(3)}<br>Permutation p=${liu.p}`,
 `The primary comparison did not support the expected positive association. Post hoc same-gene mapping adds RPN1 (${mapped.n} proteins). Limited target overlap and missing controls leave the external assessment inconclusive. These findings do not establish absence of antigenicity.`,
 'liu',['https://doi.org/10.1021/acs.jproteome.5c01244','Liu et al. · public proteomics'])+
 card('Functional endpoints · Anand',`Human-serum C3b: ${Number(c3.mean_treatment).toFixed(3)} vs ${Number(c3.mean_reference).toFixed(3)} thousand MFI<br>45-min injury: ${Number(injury.mean_treatment).toFixed(3)}% vs ${Number(injury.mean_reference).toFixed(3)}%`,
 `3KO.7TG versus 3KO, n=${c3.n_treatment} cell sources per group. Published data illustrate distinct readouts; all 18 exploratory contrasts have Holm p=1.00. This is functional context, not validation of individual edit efficacy or synergy.`,
 'anand',['https://doi.org/10.1038/s41586-023-06594-4','Anand et al. · published functional data']);
}
async function init(){
 const s=release.scope;
 $('stats').innerHTML=[[s.axes,'Molecular axes',`${s.evidence.direct} direct · ${s.evidence.disputed} disputed · ${s.evidence.control} control`],[s.atlas_records,'Interaction records',`${s.unique_unordered_pairs.toLocaleString()} unordered gene pairs`],[s.ranked_proteins,'Ranked proteins',`${s.protein_universe.toLocaleString()} records in the full universe`],[s.donor_designs,'Donor designs','Direct-target masks · explicit denominators']].map(([n,t,d])=>`<div class="stat"><strong>${Number(n).toLocaleString()}</strong><span>${t}</span><small>${d}</small></div>`).join('');
 evidenceCards();
 $('downloadList').innerHTML=release.files.map(f=>`<div class="download-item"><span>${esc(datasets[f.dataset].label)}<small>${f.record_count.toLocaleString()} rows · full precision</small></span><a href="${f.download}" download>TSV ↓</a></div>`).join('')+release.additional_downloads.map(f=>`<div class="download-item"><span>${esc(f.name.replace('.tsv','').replaceAll('_',' '))}<small>${f.record_count.toLocaleString()} source rows</small></span><a href="${f.download}" download>TSV ↓</a></div>`).join('');
 $('footerMeta').textContent=`Portal updated ${release.portal_build_date} · Frozen science archive ${release.science_archive_doi}`;
 $('status').textContent=location.protocol==='file:'?'Offline copy · frozen data bundled with this page.':'Frozen scientific snapshot · archived data and reproducible code linked below.';
 document.querySelectorAll('[data-open]').forEach(b=>b.onclick=e=>{e.preventDefault();select(b.dataset.open);$('browser').scrollIntoView({behavior:'smooth'});});
 $('search').oninput=()=>{page=1;render();};$('filter').onchange=()=>{page=1;render();};
 $('reset').onclick=()=>{$('search').value='';$('filter').value=datasets[current].default_filter||'';$('detail').hidden=true;sortKey='';page=1;render();};
 $('pageSize').onchange=()=>{pageSize=Number($('pageSize').value);page=1;render();};
 $('prev').onclick=()=>{page--;render();};$('next').onclick=()=>{page++;render();};$('export').onclick=exportFiltered;
 const params=new URLSearchParams(location.hash.slice(1));await select(params.get('dataset')||'gold',params.get('id'));
 window.addEventListener('hashchange',()=>{const p=new URLSearchParams(location.hash.slice(1));if(p.has('dataset'))select(p.get('dataset'),p.get('id'));});
}
init().catch(e=>{$('status').textContent='The resource could not be loaded. Please reload the page or use the frozen science archive linked above.';$('status').className='status error';console.error(e);});
})();
