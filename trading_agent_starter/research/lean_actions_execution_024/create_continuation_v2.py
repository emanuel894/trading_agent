from pathlib import Path
import copy,hashlib,json,shutil
R=Path('/workspace/trading_agent/trading_agent_starter/research/lean_actions_execution_024');N=R/'continuation_v2';F=N/'fixtures';H=N/'host'
if N.exists():raise SystemExit('Versioned continuation already exists; reconcile instead of overwriting')
F.mkdir(parents=True);H.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
parent=json.loads((R/'fixtures/input.json').read_text());bundle=copy.deepcopy(parent);bundle['schema_version']='issue24-v2'
for c in parent['cases']:
 p=F/c['oracle'];p.write_bytes((R/'fixtures'/c['oracle']).read_bytes())
p=F/'Q17_sell_10.expected.json';x=json.loads(p.read_text());assert x['fills'][0]['price']=='99.90';x['fills'][0]['price']='99.9';save(p,x)
for oldid,newid in [('Q14_known','Q14_known_duplicate'),('Q15_exact','Q15_exact_duplicate')]:
 c=copy.deepcopy(next(c for c in parent['cases'] if c['case_id']==oldid));c['case_id']=newid;c['oracle']=newid+'.expected.json';duplicate=copy.deepcopy(c['events'][0]);duplicate['delivery_sequence']=2;c['events'].insert(1,duplicate);bundle['cases'].append(c)
 (F/c['oracle']).write_bytes((R/'fixtures'/(oldid+'.expected.json')).read_bytes())
save(F/'input.json',bundle);save(F/'manifest.json',dict(version='issue24-v2',sha256={p.name:sha(p) for p in sorted(F.iterdir()) if p.name!='manifest.json'}))
for p in (R/'host').iterdir():shutil.copyfile(p,H/p.name)
p=H/'Actions.cs';s=p.read_text().replace('        if((string)e["kind"]! == "merger")\n        {','        if((string)e["kind"]! == "merger")\n        {\n            if(!Once("merger",e))return;').replace('        if((string)e["kind"]! == "rename")\n        {','        if((string)e["kind"]! == "rename")\n        {\n            if(!Once("rename",e))return;');p.write_text(s)
records=json.loads((R/'evidence/attempts.json').read_text());groups={}
for a in records:
 if a['verdict']=='PASS':groups.setdefault(a['case_id'],[]).append(a)
assert len(records)==33 and len(groups)==16 and all(len(v)==2 and len({a['output_sha256'] for a in v})==1 for v in groups.values())
remaining=[c['case_id'] for c in bundle['cases'] if c['case_id'] not in groups];assert len(remaining)==13
save(N/'reuse-v1.json',dict(reused={cid:dict(attempts=[a['attempt'] for a in rows],output_sha256=rows[0]['output_sha256'],original_binding=rows[0]['binding']) for cid,rows in groups.items()},remaining_ids=remaining,old_accepted_processes=32,old_replayed=0,failed_attempt_retained=33,reuse_rule='Original v1 outputs remain bound to original build03/input/oracles. No retagging as v2 and no accepted-case rerun.'))
files=[p for p in R.rglob('*') if p.is_file() and N not in p.parents and '__pycache__' not in p.parts and p.name!='checkpoint.json']
save(N/'parent-preserved.json',{str(p.relative_to(R)):sha(p) for p in sorted(files)})
s=(R/'build_manifest.py').read_text().replace('/workspace/issue-24-lean','/workspace/issue-24-v2').replace("P=R.parent/'lean_identity_time_019'","P=R.parent.parent/'lean_identity_time_019'");(N/'build_manifest.py').write_text(s)
s=(R/'run_gate.py').read_text().replace('Only27 Issue24 cases','Only13 remaining/new Issue24 cases; reuse32 accepted v1 processes').replace('/workspace/issue-24-lean','/workspace/issue-24-v2').replace("R/'compare.py'","R.parent/'compare.py'").replace("ALLOWED=[c['case_id'] for c in json.loads((R/'fixtures/input.json').read_text())['cases']]","ALLOWED=json.loads((R/'reuse-v1.json').read_text())['remaining_ids']").replace('len(ALLOWED)==27','len(ALLOWED)==13').replace("R.parent/'lean_identity_time_019/build/manifest.json'","R.parent.parent/'lean_identity_time_019/build/manifest.json'").replace("'compare.py','reuse-proof.json'","'../compare.py','reuse-v1.json','parent-preserved.json'").replace('number=1+len(records)','number=34+len(records)').replace('issue24-gate-{number:03d}','issue24-v2-{number:03d}')
s=s.replace(' build=json.loads((R/\'build.json\').read_text())\n prior='," for n,h in json.loads((R/'parent-preserved.json').read_text()).items():assert sha(R.parent/n)==h,n\n build=json.loads((R/'build.json').read_text())\n prior=",1)
(N/'run_gate.py').write_text(s)
save(N/'AMENDMENT.json',dict(parent_fixture_manifest_sha256=sha(R/'fixtures/manifest.json'),parent_build_sha256=sha(R/'build.json'),oracle_change=dict(file='Q17_sell_10.expected.json',path='/fills/0/price',old='99.90',new='99.9',reason='Preexisting G29 decimal canonical form; same exact decimal, no tolerance or economic change'),code_delta='Exactly two Once guards before mutation in Merger/Rename. All other host bytes unchanged.',new_cases=['Q14_known_duplicate','Q15_exact_duplicate'],reuse='16 accepted v1 pairs remain original-bound; run only13 remaining/new pairs',failure='Attempt33 remains failed against v1; never relabeled PASS'))
print(json.dumps({'remaining_ids':remaining,'preserved_parent_files':len(files)},indent=2))
