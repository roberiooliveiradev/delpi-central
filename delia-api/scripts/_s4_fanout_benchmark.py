#!/usr/bin/env python3
"""S4 benchmark: sequential waves vs parallel Send fan-out.

Same 3 independent READ subobjectives, providers with real sleep
latency. Measures wall time + provider invocations for:
  A) dependent chain (forced sequential waves)
  B) independent set (parallel fan-out wave)
"""
import sys, time, tempfile, sqlite3
sys.path.insert(0, "/app"); sys.path.insert(0, "/app/tests")

from tests.test_subobjective_fanout import _cap_s, _engine_a
from tests.test_subobjective_investigation import _decompose, _select
from tests.test_generic_multistep_orchestration import FakeProvider, _group
from app.infrastructure.orchestration.langgraph_engine import LangGraphCapabilityOrchestrator


class _SleepProvider(FakeProvider):
    def __init__(self, provider_id, groups, delay):
        super().__init__(provider_id, groups)
        self._delay = delay
    def invoke(self, capability, arguments, *, correlation_id, timeout_seconds=None):
        self.calls.append((capability.remote_name, dict(arguments)))
        time.sleep(self._delay)
        return super().invoke(capability, arguments,
                              correlation_id=correlation_id,
                              timeout_seconds=timeout_seconds)


def run(dep_indexes):
    caps = [_cap_s(f"g{i}", f"p{i}", f"r{i}") for i in (1, 2, 3)]
    provs = {f"p{i}": _SleepProvider(f"p{i}", [_group(f"p{i}", f"g{i}", [caps[i-1]])], 0.5)
             for i in (1, 2, 3)}
    items = [(f"ler g{i}", dep_indexes[i-1], ("e",)) for i in (1, 2, 3)]
    proposal = [_select("g1", "r1", extra=_decompose(*items)),
                _select("g2", "r2"), _select("g3", "r3")]
    eng = LangGraphCapabilityOrchestrator(
        _engine_a(provs, proposal), subobjective_fanout_enabled=True)
    t0 = time.monotonic()
    att = eng.attempt("investigue os 3 grupos")
    dt = time.monotonic() - t0
    calls = sum(len(p.calls) for p in provs.values())
    return dt, calls, att.status.value


if __name__ == "__main__":
    dt_s, c_s, st_s = run(((), (0,), (1,)))   # sequential chain
    dt_p, c_p, st_p = run(((), (), ()))      # parallel wave
    print(f"SEQUENTIAL deps: {dt_s:.2f}s calls={c_s} status={st_s}")
    print(f"PARALLEL wave:   {dt_p:.2f}s calls={c_p} status={st_p}")
    speedup = dt_s / dt_p if dt_p else 0
    print(f"SPEEDUP: {speedup:.2f}x (providers 0.5s each, 3 subs)")
