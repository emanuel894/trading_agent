"""Independent opportunity-accounting projection. No forecast, returns or promotion."""
import copy
def evaluate(raw,case):
 arms=raw['arms']
 if set(arms)!={'A','B','C','N'}:raise ValueError('Arm set changed')
 first=arms['A']['accounting']
 for arm in arms:
  if arms[arm]['accounting']!=first:raise ValueError('Cross-arm business accounting differs: '+arm)
 outcome=raw.get('reused_outcome')
 if case['arm_mode']=='unresolved':
  if not outcome or outcome.get('unresolved_claim',{}).get('status')!='UNKNOWN' or outcome['unresolved_claim'].get('terminal_value','MISSING') is not None:raise ValueError('Missing/unresolved outcome evidence')
  denominator=outcome['denominator'];failures=outcome['failures'];terminal=outcome['unresolved_claim']['terminal_value']
 else:denominator=1;failures=0;terminal=None
 def project(accounting,diagnostics):
  # Diagnostics deliberately cannot supply cash, outcomes, denominators or metrics.
  return dict(accounting=copy.deepcopy(accounting),evaluation=dict(opportunities=denominator,failures=failures,run_cost=case['run_cost'],terminal_value=terminal,status=case['arm_mode']))
 result={}
 for arm in ['A','B','C','N']:
  base=project(arms[arm]['accounting'],arms[arm]['diagnostics'])
  changed=project(arms[arm]['accounting'],dict(equity='-999999',sharpe='123456'))
  if base!=changed:raise ValueError('Engine diagnostic dependency')
  result[arm]=base
 return dict(arms=result,diagnostic_invariance=True)
