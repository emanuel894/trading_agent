"""Preserve failed evidence and restrict the adjudicated continuation delta."""
from pathlib import Path
import copy, hashlib, json, unittest
R=Path(__file__).resolve().parent;P=R.parent
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
class Lineage(unittest.TestCase):
 def test_parent_evidence_and_reuse(self):
  for n,h in load(R/'parent-preserved.json').items():self.assertEqual(sha(P/n),h,n)
  attempts=load(P/'evidence/attempts.json');self.assertEqual(len(attempts),33)
  self.assertEqual(sum(a['verdict']=='PASS' for a in attempts),32)
  self.assertEqual(attempts[-1]['verdict'],'LEAN_Q12_Q20_GATE_INCOMPLETE')
  reused=load(R/'reuse-v1.json')['reused'];self.assertEqual(len(reused),16)
  for cid,record in reused.items():
   pair=[a for a in attempts if a['attempt'] in record['attempts']]
   self.assertEqual(len(pair),2)
   for a in pair:
    self.assertEqual(a['case_id'],cid);self.assertEqual(a['binding'],record['original_binding'])
    self.assertEqual(sha(P/'evidence'/a['output']),record['output_sha256'])
 def test_single_scalar_and_two_genuine_duplicates(self):
  original=load(P/'fixtures/input.json');new=load(R/'fixtures/input.json')
  self.assertEqual(new['cases'][:27],original['cases']);self.assertEqual(len(new['cases']),29)
  for p in (P/'fixtures').glob('*.expected.json'):
   expected=load(p)
   if p.name=='Q17_sell_10.expected.json':
    self.assertEqual(expected['fills'][0]['price'],'99.90');expected['fills'][0]['price']='99.9'
   self.assertEqual(load(R/'fixtures'/p.name),expected,p.name)
  for cid,parent,kind in [('Q14_known_duplicate','Q14_known','merger'),('Q15_exact_duplicate','Q15_exact','rename')]:
   case=next(c for c in new['cases'] if c['case_id']==cid)
   base=next(c for c in original['cases'] if c['case_id']==parent)
   original_event=next(e for e in base['events'] if e['kind']==kind)
   copies=[e for e in case['events'] if e['kind']==kind];self.assertEqual(len(copies),2)
   self.assertEqual(copies[0],original_event)
   duplicate=copy.deepcopy(copies[1]);self.assertEqual(duplicate.pop('delivery_sequence'),2)
   self.assertEqual(duplicate,original_event)
   self.assertEqual((R/'fixtures'/(cid+'.expected.json')).read_bytes(),(P/'fixtures'/(parent+'.expected.json')).read_bytes())
 def test_only_two_guard_source_delta(self):
  for p in (P/'host').iterdir():
   if not p.is_file():continue
   new=(R/'host'/p.name).read_text();old=p.read_text()
   if p.name=='Actions.cs':
    for kind in ['merger','rename']:
     guard='            if(!Once("'+kind+'",e))return;\n'
     self.assertEqual(new.count(guard),1);new=new.replace(guard,'')
   self.assertEqual(new,old,p.name)
if __name__=='__main__':unittest.main()
