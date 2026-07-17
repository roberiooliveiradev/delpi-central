from types import SimpleNamespace

import pytest

from tv_app.application.services.data.m_query import m_phase7_quality_service as phase7
from tv_app.application.services.data.m_query.m_compiler import MCompileRequest, MQueryCompiler
from tv_app.application.services.data.tv_data_transform_service import execute_transform_plan
from tv_app.application.services.tv_dashboard_content_service import m_query_setting
from tv_app.domain.data_query.m_execution import MExecutionError
from tv_app.infrastructure.cache.bounded_ttl_lru_cache import BoundedTtlLruCache


SCRIPT = "let\n    Ordenado = Table.Sort(Fonte, {{\"valor\", Order.Ascending}})\nin\n    Ordenado"


def _compile(**overrides):
    values = {
        "profile": "m-delpi-v1",
        "script": SCRIPT,
        "source_schema": ({"key": "valor", "type": "number"},),
        "target_step_name": "Ordenado",
        "culture": "pt-BR",
    }
    values.update(overrides)
    return MCompileRequest(**values)


def test_phase7_rollout_flags_are_safe_by_default():
    assert m_query_setting("profilingEnabled", True) is False
    assert m_query_setting("explainPlanEnabled", True) is False
    assert m_query_setting("compileCacheEnabled", True) is False
    assert m_query_setting("previewCacheEnabled", True) is False
    assert m_query_setting("phase7TelemetryEnabled", True) is False


def test_compile_cache_key_covers_full_compilation_contract_without_script():
    base = phase7.compile_cache_key(_compile())
    assert base.startswith("sha256:")
    assert SCRIPT not in base
    assert base != phase7.compile_cache_key(_compile(culture="en-US"))
    assert base != phase7.compile_cache_key(_compile(target_step_name="Fonte"))
    assert base != phase7.compile_cache_key(
        _compile(source_schema=({"key": "outro", "type": "text"},))
    )


def test_bounded_cache_enforces_lru_limit_and_returns_defensive_copy():
    cache = BoundedTtlLruCache[dict](ttl_seconds=60, max_entries=2)
    cache.set("a", {"rows": [1]})
    cache.set("b", {"rows": [2]})
    cached = cache.get("a")
    cached["rows"].append(9)
    cache.set("c", {"rows": [3]})
    assert cache.get("b") is None
    assert cache.get("a") == {"rows": [1]}
    assert cache.stats()["entries"] == 2


def test_compile_cache_reports_hit_and_explain_warns_expensive_operation(monkeypatch):
    original = phase7.m_query_setting
    monkeypatch.setattr(
        phase7,
        "m_query_setting",
        lambda key, default=None: True if key == "compileCacheEnabled" else original(key, default),
    )
    phase7.reset_phase7_caches()
    first = MQueryCompiler().compile(_compile())
    second = MQueryCompiler().compile(_compile())
    assert first.compile_cache == "miss"
    assert second.compile_cache == "hit"
    assert second.explain_plan["warnings"] == [
        {
            "code": "m.expensive_operation",
            "stepName": "Ordenado",
            "operation": "Table.Sort",
        }
    ]


def test_preview_cache_partition_includes_identity_permissions_sources_and_revisions():
    common = {
        "block": {
            "id": "source",
            "revision": 7,
            "dataBinding": {"operationId": "op", "params": {"branch": "01"}},
            "dataTransform": {
                "version": 2,
                "language": "m-delpi-v1",
                "script": SCRIPT,
            },
        },
        "native_config": {"revision": 11, "blocks": []},
        "playlist_defaults": {"branch": "01"},
        "target_step_name": "Ordenado",
        "preview_options": {"maxRows": 20},
        "authorization": "Bearer segredo",
    }
    alice = SimpleNamespace(id="alice", permissions=["tv-dashboard.read"])
    bob = SimpleNamespace(id="bob", permissions=["tv-dashboard.read"])
    alice_key, alice_principal = phase7.preview_cache_key(user=alice, **common)
    bob_key, bob_principal = phase7.preview_cache_key(user=bob, **common)
    assert alice_key != bob_key
    assert alice_principal != bob_principal
    assert "segredo" not in alice_key
    assert SCRIPT not in alice_key


def test_preview_cache_partition_tracks_resolved_branch_scope(monkeypatch):
    user = SimpleNamespace(id="alice", permissions=["tv-dashboard.read"])
    common = {
        "block": {"id": "source", "dataTransform": {"version": 2, "script": SCRIPT}},
        "native_config": {"blocks": []},
        "playlist_defaults": {},
        "target_step_name": None,
        "preview_options": {},
        "user": user,
        "authorization": "Bearer segredo",
    }
    monkeypatch.setattr(
        phase7,
        "resolve_branch_access_scope",
        lambda _user: SimpleNamespace(
            meta=lambda: {"mode": "scoped", "branches": ["01"], "allowConsolidated": False}
        ),
    )
    branch_01, _ = phase7.preview_cache_key(**common)
    monkeypatch.setattr(
        phase7,
        "resolve_branch_access_scope",
        lambda _user: SimpleNamespace(
            meta=lambda: {"mode": "scoped", "branches": ["02"], "allowConsolidated": False}
        ),
    )
    branch_02, _ = phase7.preview_cache_key(**common)

    assert branch_01 != branch_02


def test_profile_is_opt_in_sampled_and_never_emits_top_values(monkeypatch):
    original = phase7.m_query_setting
    settings = {
        "profilingEnabled": True,
        "profileSampleRows": 2,
        "profileMaxColumns": 10,
        "profileTimeoutMs": 500,
    }
    monkeypatch.setattr(
        phase7,
        "m_query_setting",
        lambda key, default=None: settings.get(key, original(key, default)),
    )
    table = {
        "columns": ["valor", "texto"],
        "rows": [
            {"valor": 2, "texto": "secreto-a"},
            {"valor": None, "texto": "secreto-b"},
            {"valor": 9, "texto": "secreto-c"},
        ],
    }
    assert phase7.profile_table(table, requested=False) is None
    result = phase7.profile_table(table, requested=True)
    assert result["sampled"] is True
    assert result["sampleRows"] == 2
    value_profile = result["columns"][0]
    assert value_profile["quality"] == {"valid": 1, "empty": 1, "error": 0}
    assert value_profile["min"] == 2
    assert "secreto-a" not in str(result["columns"][1]["distribution"])


def test_execution_records_per_step_metrics_and_honors_adversarial_deadline():
    compiled = MQueryCompiler().compile(_compile())
    assert compiled.plan is not None
    result = execute_transform_plan(
        {"columns": ["valor"], "rows": [{"valor": 2}, {"valor": 1}]},
        compiled.plan,
        deadline_ms=100,
    )
    assert result.table["rows"] == [{"valor": 1}, {"valor": 2}]
    assert result.step_metrics[0]["inputRows"] == 2
    assert result.step_metrics[0]["outputRows"] == 2

    rows = [{"valor": value} for value in range(20000, 0, -1)]
    with pytest.raises(MExecutionError) as exc:
        execute_transform_plan(
            {"columns": ["valor"], "rows": rows},
            compiled.plan,
            deadline_ms=1,
        )
    assert exc.value.code in {"m.execution_timeout", "m.limit_rows"}
