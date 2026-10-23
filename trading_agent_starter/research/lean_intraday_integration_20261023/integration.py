"""Fixed synthetic minute-feature wiring into the unchanged PR28 input grammar.

Not a research strategy, source adapter, engine replacement or trading entrypoint.
"""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import statistics
import time
import tracemalloc

from agent.offline_chart_gov_demo import Bar, Clocks, Statement, chart_snapshot, statement_snapshot

CUTOFF = datetime(2025, 1, 6, 15, tzinfo=timezone.utc)
START_NS = 1736175600000000000


def clocks(published, revised=False):
    return Clocks(*(published + timedelta(seconds=i) for i in range(5)),
                  revised=published if revised else None)


def fixture():
    sessions = tuple(CUTOFF - timedelta(minutes=6-i) for i in range(6))
    bars = tuple(Bar(f'synthetic:minute:{i}:r1', end, close, close+1,
                     close-1, close, 100, clocks(end+timedelta(seconds=1)))
                 for i, (end, close) in enumerate(zip(sessions, (100,100,100,101,102,103))))
    releases = tuple(Statement(f'synthetic:release:{name}:r1', f'synthetic:release:{name}',
                               f'SYNTHETIC ONLY. Target range: {low} to {high} percent.',
                               published+timedelta(days=1), clocks(published))
                     for name, low, high, published in (
                         ('A','4.50','4.75',CUTOFF-timedelta(minutes=10)),
                         ('B','4.25','4.50',CUTOFF-timedelta(seconds=30))))
    return sessions, bars, releases


def decide(sessions, bars, releases):
    chart = chart_snapshot(sessions, bars, CUTOFF)
    statement = statement_snapshot(releases, CUTOFF)
    row = chart['rows'][-1]
    delta = statement['rate_change_pp']
    sma3, sma5 = row['sma_3'], row['sma_5']
    signal = (sma3 is not None and sma5 is not None and sma3 > sma5
              and delta is not None and Decimal(delta[0]) < 0)
    return {'scope':'SYNTHETIC_WIRING_ONLY', 'cutoff':chart['cutoff'],
            'sma_3':sma3, 'sma_5':sma5,
            'rate_change_pp':delta[0] if delta else None, 'signal':signal,
            'bar_versions':row['input_versions'],
            'release_version':statement['selected']['evidence_id'] if statement['selected'] else None}


def scenarios():
    sessions, bars, releases = fixture()
    future = replace(bars[-1], evidence_id='synthetic:minute:5:r2', close=10000,
                     high=10001, previous_version=bars[-1].evidence_id,
                     clocks=clocks(CUTOFF+timedelta(seconds=1), revised=True))
    future_release = replace(releases[-1], evidence_id='synthetic:release:B:r2',
                             text='Target range: 9.00 to 9.25 percent.',
                             previous_version=releases[-1].evidence_id,
                             clocks=clocks(CUTOFF+timedelta(seconds=1), revised=True))
    equal = replace(releases[-1], clocks=replace(releases[-1].clocks,verified=CUTOFF))
    return {'baseline':(sessions,bars,releases),
            'future_revision':(sessions,bars+(future,),releases+(future_release,)),
            'missing_bar':(sessions,bars[:-1],releases),
            'equal_clock':(sessions,bars,releases[:-1]+(equal,))}


def native_case(name, decision):
    # Q23 is only the accepted host's schema tag; these are new integration IDs.
    steps = []
    if decision['signal']:
        steps.append({'op':'order','at_ns':START_NS,'id':'SYNTHETIC_ENTRY',
                      'instrument':'I1','qty':'9','price':'100.07001','fee':'1','route':'direct'})
    steps += [{'op':'quote','at_ns':START_NS+1_000_000_000,'bid':'100','ask':'100.02',
               'size':'1000','status':'TRADABLE','quote_id':'synthetic:execution:quote'},
              {'op':'snapshot','at_ns':START_NS+1_000_000_100,'label':'final'}]
    return {'case_id':'INTRADAY_'+name, 'fixture':'Q23', 'cash':'10000','holdings':[],
            'checks':['cash','limits','halts'],'mark':'100','start_ns':START_NS,'steps':steps}


def check_native(output, signal):
    assert output['case_complete'] is True and output['execution_complete'] is True
    assert not output.get('technical_error') and not output.get('guard_error')
    assert output['provider_calls'] == 0
    assert output['network_denied'] == {'non_loopback_interfaces':0,'testnet_socket_result':'NetworkUnreachable'}
    native, business = output['native'], output['business']
    assert native['gate_calls'] == int(signal) and native['open_orders'] == 0
    assert native['quantities']['I1'] == ('9' if signal else '0')
    assert native['cash'] == ('9098.36991' if signal else '10000')
    assert len(business['decisions']) == int(signal)
    assert all(d['allowed'] is True for d in business['decisions'])
    assert len(business['fills']) == int(signal)
    if signal:
        fill = business['fills'][0]
        assert (fill['quantity'],fill['price'],fill['fee']) == ('9','100.07001','1')
        assert Decimal(native['cash']) == Decimal('10000')-Decimal('9')*Decimal(fill['price'])-Decimal(fill['fee'])


def measure(repetitions=100):
    """Paired Python assembly cost; container work is measured separately."""
    inputs = fixture()
    frozen = decide(*inputs)
    baseline, integrated = [], []
    for _ in range(repetitions):
        start=time.perf_counter_ns(); native_case('timing',frozen); baseline.append(time.perf_counter_ns()-start)
        start=time.perf_counter_ns(); native_case('timing',decide(*inputs)); integrated.append(time.perf_counter_ns()-start)
    peaks=[]
    for with_features in (False,True):
        tracemalloc.start()
        try:
            native_case('timing',decide(*inputs) if with_features else frozen)
            peaks.append(tracemalloc.get_traced_memory()[1])
        finally:tracemalloc.stop()
    return {'samples':repetitions,'prepared_input_p50_ns':statistics.median(baseline),
            'feature_and_input_p50_ns':statistics.median(integrated),
            'paired_increment_p50_ns':statistics.median(b-a for a,b in zip(baseline,integrated)),
            'paired_increment_p95_ns':sorted(b-a for a,b in zip(baseline,integrated))[94],
            'prepared_input_python_peak_bytes':peaks[0], 'feature_and_input_python_peak_bytes':peaks[1],
            'incremental_python_peak_bytes':peaks[1]-peaks[0],
            'limits':'Warm six-bar/two-release fixture, Python allocations only; no real-time/source/large-scale latency claim.'}
