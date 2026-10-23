"""Original-bound reuse and forbidden-scope checks, without native execution."""
from pathlib import Path
import hashlib,importlib.util,json,unittest
R=Path(__file__).resolve().parent;P=R.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class ContinuationTests(unittest.TestCase):
 def test_parent_packet_and_economic_adapter_unchanged(self):
  for n,h in json.loads((R/'parent-preserved.json').read_text()).items():self.assertEqual(sha(P/n),h,n)
  for n in ['host/ResearchAlgorithm.cs','compare.py','evaluate.py','fixtures/input.json','fixtures/manifest.json']:
   self.assertEqual((R/n).read_bytes(),(P/n).read_bytes(),n)
 def test_original_q21_pairs_under_original_binding(self):
  spec=importlib.util.spec_from_file_location('original_compare',P/'compare.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  reused=json.loads((R/'reuse-v1.json').read_text());self.assertEqual(reused['global_attempt_offset'],17);self.assertEqual(len(reused['reused']),8)
  approved=json.loads((P/'ORACLE_REVIEW.json').read_text())['binding']
  for cid,pair in reused['reused'].items():
   self.assertTrue(cid.startswith('Q21_'));self.assertEqual(len(pair),2);self.assertEqual(len({a['output_sha256'] for a in pair}),1)
   for a in pair:
    self.assertEqual(a['binding'],approved);self.assertEqual(sha(P/'evidence'/a['output']),a['output_sha256']);self.assertTrue(m.compare_file(P/'evidence'/a['output'],P/'fixtures'/(cid+'.expected.json'),P/'fixtures/input.json'))
 def test_q21_cannot_launch_in_continuation(self):
  spec=importlib.util.spec_from_file_location('v2_runner',R/'run_gate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  with self.assertRaisesRegex(AssertionError,'Q21 reused only'):m.main(['Q21_compete'])
if __name__=='__main__':unittest.main()
