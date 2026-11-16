"""ATLAS P2.2h.2h: hermetic GHCR manifest/OCI ImageID tests.

MockTransport intercepts EVERY request: no real GitHub/registry/Docker/DB/PROD.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone

import httpx
import pytest

from it_portal_app.infrastructure.persistence.atlas_deploy_oci_registry import (
    GHCRImageIdentityReader, OCIRegistryReadError,
)
from it_portal_app.infrastructure.persistence.atlas_deploy_oci_seal import IMAGE

NOW = datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc)
MANIFEST_MEDIA = "application/vnd.oci.image.manifest.v1+json"
INDEX_MEDIA = "application/vnd.oci.image.index.v1+json"
CONFIG_MEDIA = "application/vnd.oci.image.config.v1+json"
TOKEN = "opaque-anonymous-registry-pull-token-123"
CONFIG = "sha256:" + "c" * 64


def encoded(payload):
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest(), body


def image_manifest(*, config=CONFIG, media=MANIFEST_MEDIA):
    return {
        "schemaVersion": 2, "mediaType": media,
        "config": {
            "mediaType": CONFIG_MEDIA, "digest": config, "size": 4096,
        },
        "layers": [],
    }


def index_manifest(child_digest, child_size, *, other_platform=True):
    targets = [{
        "mediaType": MANIFEST_MEDIA,
        "digest": child_digest,
        "size": child_size,
        "platform": {"os": "linux", "architecture": "amd64"},
    }]
    if other_platform:
        targets.append({
            "mediaType": MANIFEST_MEDIA,
            "digest": "sha256:" + "b" * 64,
            "size": 100,
            "platform": {"os": "linux", "architecture": "arm64"},
        })
    return {"schemaVersion": 2, "mediaType": INDEX_MEDIA, "manifests": targets}


class FakeRegistry:
    def __init__(self, *, require_auth=False, token=TOKEN):
        self.objects = {}
        self.require_auth = require_auth
        self.token = token
        self.calls = []
        self.reply_override = None

    def add(self, payload, media):
        digest, body = encoded(payload)
        self.objects[digest] = (media, body)
        return digest

    def add_raw(self, body, media):
        digest = "sha256:" + hashlib.sha256(body).hexdigest()
        self.objects[digest] = (media, body)
        return digest

    def __call__(self, request):
        self.calls.append(request)
        assert request.method == "GET"
        assert request.url.host == "ghcr.io"
        assert request.url.scheme == "https"
        assert request.url.port in (443, None)
        assert request.headers.get("host") == "ghcr.io"
        if self.reply_override:
            r = self.reply_override(request)
            if r is not None:
                return r
        if request.url.path == "/token":
            assert request.url.params["service"] == "ghcr.io"
            assert request.url.params["scope"] == "repository:roberiooliveiradev/delpi-public-hub:pull"
            assert request.headers.get("authorization") is None
            return httpx.Response(200, json={"token": self.token})
        assert request.url.path.startswith(
            "/v2/roberiooliveiradev/delpi-public-hub/manifests/sha256:"
        )
        if self.require_auth and request.headers.get("authorization") != f"Bearer {TOKEN}":
            return httpx.Response(401, headers={"www-authenticate": "Bearer"})
        digest = request.url.path.rsplit("/", 1)[-1]
        if digest not in self.objects:
            return httpx.Response(404, text="secret from upstream")
        media, body = self.objects[digest]
        return httpx.Response(
            200, headers={"content-type": media, "docker-content-digest": digest},
            content=body,
        )


def read(registry, digest, **kw):
    return asyncio.run(
        GHCRImageIdentityReader(
            transport=httpx.MockTransport(registry), clock=lambda: NOW, **kw,
        ).read(manifest_digest=digest)
    )


def reject(registry, digest, code, **kw):
    with pytest.raises(OCIRegistryReadError) as ex:
        read(registry, digest, **kw)
    assert ex.value.code == code
    assert TOKEN not in str(ex.value)
    assert "secret from upstream" not in str(ex.value)


def test_single_oci_manifest_returns_content_addressed_image_id_only():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    resolved = read(registry, digest)
    assert resolved.image == IMAGE
    assert resolved.manifest_digest == digest
    assert resolved.image_manifest_digest == digest
    assert resolved.image_config_id == CONFIG
    # Platform cannot be certified by a standalone manifest alone.
    assert resolved.platform == "unverified"
    assert resolved.read_at == NOW
    assert len(registry.calls) == 1
    assert "authorization" not in registry.calls[0].headers
    assert "application/vnd.oci.image.index.v1+json" in registry.calls[0].headers["accept"]
    assert not hasattr(resolved, "signature_verified")
    assert not hasattr(resolved, "rollback_ready")


def test_index_selects_one_linux_amd64_and_checks_child_digest_and_size():
    registry = FakeRegistry()
    child = image_manifest()
    child_digest = registry.add(child, MANIFEST_MEDIA)
    parent_digest = registry.add(
        index_manifest(child_digest, len(encoded(child)[1])), INDEX_MEDIA,
    )
    image = read(registry, parent_digest)
    assert image.manifest_digest == parent_digest
    assert image.image_manifest_digest == child_digest
    assert image.image_config_id == CONFIG
    assert image.platform == "linux/amd64"
    assert len(registry.calls) == 2
    assert child_digest in registry.calls[1].url.path


def test_immutable_manifest_does_not_need_tags_or_registry_write():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    read(registry, digest)
    for call in registry.calls:
        assert "/manifests/sha256:" in call.url.path
        assert "/blobs/" not in call.url.path
        assert call.method == "GET"


def test_public_ghcr_anonymous_token_is_requested_only_at_pinned_origin():
    registry = FakeRegistry(require_auth=True)
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    identity = read(registry, digest)
    assert identity.image_config_id == CONFIG
    assert len(registry.calls) == 3
    assert [r.url.path for r in registry.calls] == [
        f"/v2/roberiooliveiradev/delpi-public-hub/manifests/{digest}",
        "/token",
        f"/v2/roberiooliveiradev/delpi-public-hub/manifests/{digest}",
    ]
    assert registry.calls[0].headers.get("authorization") is None
    assert registry.calls[1].headers.get("authorization") is None
    assert registry.calls[2].headers["authorization"] == f"Bearer {TOKEN}"


def test_operator_scoped_token_is_never_exchanged_or_forwarded_elsewhere():
    registry = FakeRegistry(require_auth=True)
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    image = read(registry, digest, registry_token=TOKEN)
    assert image.image_config_id == CONFIG
    assert len(registry.calls) == 1
    assert registry.calls[0].headers["authorization"] == f"Bearer {TOKEN}"


@pytest.mark.parametrize("value", [
    None, "", "a" * 64, "sha256:" + "A" * 64,
    "sha256:" + "c" * 63, "sha256:" + "b" * 64 + "/../latest",
])
def test_invalid_manifest_digest_does_not_call_registry(value):
    registry = FakeRegistry()
    reject(registry, value, "OCI_REGISTRY_DIGEST_INVALID")
    assert registry.calls == []


@pytest.mark.parametrize("bad", ["", "short", "Bearer " + TOKEN, "z" * 9 + "\n" + "a" * 19, "\x00" + TOKEN])
def test_bad_scoped_tokens_denied_before_network(bad):
    with pytest.raises(OCIRegistryReadError, match="OCI_REGISTRY_TOKEN_INVALID"):
        GHCRImageIdentityReader(registry_token=bad)


def test_clock_must_be_timezone_aware_and_server_owned():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    for value in (NOW.replace(tzinfo=None), "today"):
        with pytest.raises(OCIRegistryReadError, match="OCI_REGISTRY_CLOCK_INVALID"):
            asyncio.run(GHCRImageIdentityReader(
                transport=httpx.MockTransport(registry),
                clock=lambda v=value: v,
            ).read(manifest_digest=digest))
    assert registry.calls == []


def test_supplied_credentials_do_not_trigger_anonymous_exchange_after_401():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    def reply(request):
        return httpx.Response(401, text="private upstream token")
    registry.reply_override = reply
    reject(registry, digest, "OCI_REGISTRY_AUTH_REQUIRED", registry_token=TOKEN)
    assert len(registry.calls) == 1


@pytest.mark.parametrize("status", [302, 403, 404, 429, 500, 503])
def test_error_redirect_rate_limit_and_not_found_are_fail_closed(status):
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    registry.reply_override = lambda req: httpx.Response(
        status, headers={"location": "https://attacker.example/secret"},
        text="private-server-error",
    )
    reject(registry, digest, "OCI_REGISTRY_UNAVAILABLE")
    assert len(registry.calls) == 1


def test_server_digest_header_disagreement_denied_before_parsing():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    registry.reply_override = lambda req: httpx.Response(
        200,
        content=registry.objects[digest][1],
        headers={
            "content-type": MANIFEST_MEDIA,
            "docker-content-digest": "sha256:" + "f" * 64,
        },
    )
    reject(registry, digest, "OCI_REGISTRY_DIGEST_MISMATCH")


def test_manifest_bytes_must_match_requested_sha_even_with_matching_http_header():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    registry.reply_override = lambda req: httpx.Response(
        200,
        content=b'{"schemaVersion":2,"mediaType":"forged"}',
        headers={"content-type": MANIFEST_MEDIA, "docker-content-digest": digest},
    )
    reject(registry, digest, "OCI_REGISTRY_DIGEST_MISMATCH")


@pytest.mark.parametrize("media", ["text/html", "application/json", "application/vnd.oci.artifact.manifest.v1+json"])
def test_unknown_media_types_denied(media):
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    registry.reply_override = lambda req: httpx.Response(
        200, headers={"content-type": media, "docker-content-digest": digest},
        content=registry.objects[digest][1],
    )
    reject(registry, digest, "OCI_REGISTRY_MEDIA_UNSUPPORTED")


def test_media_type_confusion_and_schema_version_denied():
    registry = FakeRegistry()
    for manifest in [
        dict(image_manifest(), mediaType=INDEX_MEDIA),
        dict(image_manifest(), schemaVersion=1),
        dict(image_manifest(), schemaVersion=True),
    ]:
        digest = registry.add(manifest, MANIFEST_MEDIA)
        reject(registry, digest, "OCI_REGISTRY_MANIFEST_INVALID")


@pytest.mark.parametrize("bad", [
    b'{"schemaVersion":2,"schemaVersion":2}',
    b'{"schemaVersion":NaN}',
    b"\xff",
    b"[]",
])
def test_malformed_utf8_nonfinite_and_duplicate_json_fields_denied(bad):
    registry = FakeRegistry()
    digest = registry.add_raw(bad, MANIFEST_MEDIA)
    reject(registry, digest, "OCI_REGISTRY_MANIFEST_INVALID")


def test_large_manifest_is_rejected_even_if_hash_is_correct():
    registry = FakeRegistry()
    body = b'{' + b' ' * 512_000 + b'}'
    digest = registry.add_raw(body, MANIFEST_MEDIA)
    reject(registry, digest, "OCI_REGISTRY_RESPONSE_TOO_LARGE")


def test_anonymous_token_json_is_untrusted_and_cannot_redirect():
    for bad_token in ("short", "Bearer " + TOKEN, "e" * 8193):
        registry = FakeRegistry(require_auth=True, token=bad_token)
        digest = registry.add(image_manifest(), MANIFEST_MEDIA)
        reject(registry, digest, "OCI_REGISTRY_AUTH_UNAVAILABLE")
        assert len(registry.calls) == 2


def test_auth_token_endpoint_error_is_fail_closed_without_external_redirect():
    registry = FakeRegistry(require_auth=True)
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    def reply(req):
        if req.url.path == "/token":
            return httpx.Response(
                302, headers={"location": "https://attacker.example/token"},
            )
        return None
    registry.reply_override = reply
    reject(registry, digest, "OCI_REGISTRY_AUTH_UNAVAILABLE")
    assert len(registry.calls) == 2


def test_index_with_zero_or_multiple_linux_amd64_candidates_is_denied():
    registry = FakeRegistry()
    child_digest, child_bytes = encoded(image_manifest())
    one = index_manifest(child_digest, len(child_bytes), other_platform=False)
    for entries in ([], [{**one["manifests"][0], "platform": {"os": "windows", "architecture": "amd64"}}], one["manifests"] * 2):
        idx = {**one, "manifests": entries}
        parent = registry.add(idx, INDEX_MEDIA)
        reject(registry, parent, "OCI_REGISTRY_PLATFORM_INVALID")


def test_index_invalid_selected_descriptor_is_denied_before_child_fetch():
    registry = FakeRegistry()
    for edits in (
        {"digest": "latest"},
        {"mediaType": INDEX_MEDIA},
        {"size": 0},
        {"size": 512_001},
    ):
        child_digest, child_bytes = encoded(image_manifest())
        descriptor = index_manifest(child_digest, len(child_bytes), other_platform=False)["manifests"][0]
        descriptor.update(edits)
        root = registry.add({"schemaVersion": 2, "mediaType": INDEX_MEDIA, "manifests": [descriptor]}, INDEX_MEDIA)
        initial = len(registry.calls)
        reject(registry, root, "OCI_REGISTRY_PLATFORM_INVALID")
        assert len(registry.calls) == initial + 1


def test_index_child_bytes_and_declared_size_must_match():
    registry = FakeRegistry()
    child = image_manifest()
    child_digest = registry.add(child, MANIFEST_MEDIA)
    root = registry.add(index_manifest(child_digest, len(encoded(child)[1]) + 1), INDEX_MEDIA)
    reject(registry, root, "OCI_REGISTRY_PLATFORM_INVALID")


@pytest.mark.parametrize("bad_config", [
    {"mediaType": "application/vnd.oci.empty.v1+json", "digest": CONFIG, "size": 100},
    {"mediaType": CONFIG_MEDIA, "digest": "sha256:broken", "size": 100},
    {"mediaType": CONFIG_MEDIA, "digest": CONFIG, "size": 0},
    None,
])
def test_manifest_config_must_be_supported_content_addressed_descriptor(bad_config):
    registry = FakeRegistry()
    payload = image_manifest()
    payload["config"] = bad_config
    digest = registry.add(payload, MANIFEST_MEDIA)
    reject(registry, digest, "OCI_REGISTRY_CONFIG_INVALID")


def test_manifest_must_have_layers_array_even_when_empty():
    registry = FakeRegistry()
    item = image_manifest()
    item.pop("layers")
    digest = registry.add(item, MANIFEST_MEDIA)
    reject(registry, digest, "OCI_REGISTRY_MANIFEST_INVALID")


def test_stray_registry_network_exceptions_are_sanitized():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    def raise_upstream(_):
        raise httpx.ConnectError("private-error-in-network-token")
    registry.reply_override = raise_upstream
    reject(registry, digest, "OCI_REGISTRY_UNAVAILABLE")


def test_ambiguous_descriptor_does_not_create_release_or_execute_deployment():
    registry = FakeRegistry()
    digest = registry.add(image_manifest(), MANIFEST_MEDIA)
    identity = read(registry, digest)
    assert identity.platform == "unverified"
    assert not hasattr(identity, "verified_at")
    assert not hasattr(identity, "host_challenge_sha256")
    assert not hasattr(identity, "approval")
    assert all(call.method == "GET" for call in registry.calls)
