import hashlib
import json
from pathlib import Path
import unittest

PACKET=Path(__file__).resolve().parents[1]

def differences(a,b,path=''):
    if type(a)!=type(b):return [(path,a,b)]
    if isinstance(a,dict):
        if a.keys()!=b.keys():return [(path,a,b)]
        return [d for k in a for d in differences(a[k],b[k],path+'/'+k)]
    if isinstance(a,list):
        if len(a)!=len(b):return [(path,a,b)]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [(path,a,b)]

class AmendmentTests(unittest.TestCase):
    def test_exact_four_scalar_changes(self):
        self.assertTrue((PACKET/'fixtures_v3/input.json').exists(),'Reviewed v3 amendment is absent')
        old=json.loads((PACKET/'fixtures_v2/input.json').read_text())
        new=json.loads((PACKET/'fixtures_v3/input.json').read_text())
        expected=[]
        for i,c in enumerate(old['cases']):
            if c['case_id'] in ['Q04_missing','Q04_overlap']:
                for k in ['event_ns','available_ns']:
                    expected.append((f'/cases/{i}/events/0/{k}',1736175601000000000,1736260201000000000))
        self.assertEqual(differences(old,new),expected)
    def test_all_expected_records_unchanged(self):
        self.assertTrue((PACKET/'fixtures_v3/manifest.json').exists(),'v3 manifest absent')
        files=list((PACKET/'fixtures_v2').glob('*.expected.json'))
        self.assertEqual(len(files),57)
        for p in files:
            with self.subTest(case=p.name):
                self.assertEqual(p.read_bytes(),(PACKET/'fixtures_v3'/p.name).read_bytes())
    def test_original_packet_bytes_preserved(self):
        manifest=json.loads((PACKET/'continuation_021/preserved_c70aa32_sha256.json').read_text())
        for name,digest in manifest.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((PACKET/name).read_bytes()).hexdigest(),digest)

if __name__=='__main__':unittest.main(verbosity=2)
