"""P2.2h.2h: bounded GHCR OCI manifest -> image configuration digest reader.

Backend-only, read-only, inert. No HTTP route, PREPARE, approval, ACT, Docker
operations, or automatic merge. Registry bytes are verified against immutable
SHA-256 references before any field is trusted. A config digest is not by
itself a verified signed release or evidence that a host runs that image.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

import httpx

from .atlas_deploy_oci_seal import IMAGE

_ORIGIN = "https://ghcr.io"
_NAME = "roberiooliveiradev/delpi-public-hub"
_SCOPE = f"repository:{_NAME}:pull"
_HEX_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_OCI_MANIFEST = "application/vnd.oci.image.manifest.v1+json"
_DOCKER_MANIFEST = "application/vnd.docker.distribution.manifest.v2+json"
_OCI_INDEX = "application/vnd.oci.image.index.v1+json"
_DOCKER_LIST = "application/vnd.docker.distribution.manifest.list.v2+json"
_OCI_CONFIG = "application/vnd.oci.image.config.v1+json"
_DOCKER_CONFIG = "application/vnd.docker.container.image.v1+json"
_ACCEPTED = frozenset((_OCI_MANIFEST, _DOCKER_MANIFEST, _OCI_INDEX, _DOCKER_LIST))
_IMAGE_MEDIA = frozenset((_OCI_MANIFEST, _DOCKER_MANIFEST))
_INDEX_MEDIA = frozenset((_OCI_INDEX, _DOCKER_LIST))
_CONFIG_MEDIA = frozenset((_OCI_CONFIG, _DOCKER_CONFIG))
_MAX_MANIFEST = 512_000
_MAX_TOKEN = 8_192
_MAX_DESCRIPTORS = 128


class OCIRegistryReadError(Exception):
    """Sanitized finite codes. Never expose tokens, upstream JSON or HTTP body."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class OCIImageIdentity:
    """Identity from hashed registry bytes, not CI signing or host attestation."""

    image: str
    manifest_digest: str
    image_manifest_digest: str
    image_config_id: str
    platform: str
    read_at: datetime


def _digest(value: object) -> bool:
    return type(value) is str and _HEX_DIGEST.fullmatch(value) is not None


def _no_duplicate_json(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _json_object(content: bytes, code: str) -> dict:
    try:
        parsed = json.loads(
            content.decode("utf-8"), object_pairs_hook=_no_duplicate_json,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON")),
        )
        if type(parsed) is not dict:
            raise ValueError("JSON object required")
        return parsed
    except (ValueError, UnicodeError, TypeError):
        raise OCIRegistryReadError(code) from None


def _valid_token(value: object) -> bool:
    return (type(value) is str and 20 <= len(value) <= _MAX_TOKEN
            and value.isascii() and all(33 <= ord(ch) <= 126 for ch in value)
            and not value.startswith("Bearer "))


class GHCRImageIdentityReader:
    """Fetch immutable GHCR manifests only. No caller-selected URL or platform.

    If a public manifest requires authentication, exchange for an anonymous,
    repository-scoped pull token at the FIXED ghcr.io/token endpoint. A
    server-provided scoped bearer can be supplied for private packages.
    Tokens MUST come from trusted backend configuration, never HTTP/MCP input.
    """

    def __init__(
        self, *, registry_token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        if registry_token is not None and not _valid_token(registry_token):
            raise OCIRegistryReadError("OCI_REGISTRY_TOKEN_INVALID")
        self._token = registry_token
        self._transport = transport
        self._clock = clock

    @staticmethod
    async def _limited_response(response: httpx.Response, maximum: int) -> bytes:
        data = bytearray()
        async for chunk in response.aiter_bytes():
            data.extend(chunk)
            if len(data) > maximum:
                raise OCIRegistryReadError("OCI_REGISTRY_RESPONSE_TOO_LARGE")
        return bytes(data)

    async def _anonymous_pull_token(self, client: httpx.AsyncClient) -> str:
        try:
            async with client.stream(
                "GET", "/token",
                params={"scope": _SCOPE, "service": "ghcr.io"},
                headers={"Accept": "application/json"},
            ) as response:
                if response.status_code != 200:
                    raise OCIRegistryReadError("OCI_REGISTRY_AUTH_UNAVAILABLE")
                mime = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if mime != "application/json":
                    raise OCIRegistryReadError("OCI_REGISTRY_AUTH_UNAVAILABLE")
                raw = await self._limited_response(response, _MAX_TOKEN)
        except (httpx.HTTPError, UnicodeError):
            raise OCIRegistryReadError("OCI_REGISTRY_AUTH_UNAVAILABLE") from None
        token = _json_object(raw, "OCI_REGISTRY_AUTH_UNAVAILABLE").get("token")
        if not _valid_token(token):
            raise OCIRegistryReadError("OCI_REGISTRY_AUTH_UNAVAILABLE")
        return token

    async def _manifest(
        self, client: httpx.AsyncClient, digest: str, token: str | None,
    ) -> tuple[dict, str, int]:
        headers = {"Accept": ", ".join(sorted(_ACCEPTED))}
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        try:
            async with client.stream(
                "GET", f"/v2/{_NAME}/manifests/{digest}", headers=headers,
            ) as response:
                if response.status_code == 401:
                    raise OCIRegistryReadError("OCI_REGISTRY_AUTH_REQUIRED")
                if response.status_code != 200:
                    raise OCIRegistryReadError("OCI_REGISTRY_UNAVAILABLE")
                media = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if media not in _ACCEPTED:
                    raise OCIRegistryReadError("OCI_REGISTRY_MEDIA_UNSUPPORTED")
                header_digest = response.headers.get("docker-content-digest")
                if header_digest is not None and header_digest != digest:
                    raise OCIRegistryReadError("OCI_REGISTRY_DIGEST_MISMATCH")
                raw = await self._limited_response(response, _MAX_MANIFEST)
        except (httpx.HTTPError, UnicodeError):
            raise OCIRegistryReadError("OCI_REGISTRY_UNAVAILABLE") from None

        if not hashlib.sha256(raw).hexdigest() == digest[7:]:
            raise OCIRegistryReadError("OCI_REGISTRY_DIGEST_MISMATCH")
        manifest = _json_object(raw, "OCI_REGISTRY_MANIFEST_INVALID")
        if (type(manifest.get("schemaVersion")) is not int
                or manifest["schemaVersion"] != 2
                or manifest.get("mediaType") != media):
            raise OCIRegistryReadError("OCI_REGISTRY_MANIFEST_INVALID")
        return manifest, media, len(raw)

    async def read(self, *, manifest_digest: str) -> OCIImageIdentity:
        if not _digest(manifest_digest):
            raise OCIRegistryReadError("OCI_REGISTRY_DIGEST_INVALID")
        now = self._clock()
        if type(now) is not datetime or now.tzinfo is None or now.utcoffset() is None:
            raise OCIRegistryReadError("OCI_REGISTRY_CLOCK_INVALID")

        async with httpx.AsyncClient(
            base_url=_ORIGIN, timeout=5, trust_env=False,
            follow_redirects=False, transport=self._transport,
        ) as client:
            token = self._token
            try:
                manifest, media, _ = await self._manifest(client, manifest_digest, token)
            except OCIRegistryReadError as exc:
                if exc.code != "OCI_REGISTRY_AUTH_REQUIRED" or token is not None:
                    raise
                token = await self._anonymous_pull_token(client)
                manifest, media, _ = await self._manifest(client, manifest_digest, token)

            image_manifest_digest = manifest_digest
            resolved_platform = "unverified"
            if media in _INDEX_MEDIA:
                descriptors = manifest.get("manifests")
                if (type(descriptors) is not list or not 1 <= len(descriptors) <= _MAX_DESCRIPTORS):
                    raise OCIRegistryReadError("OCI_REGISTRY_PLATFORM_INVALID")
                matches = []
                for descriptor in descriptors:
                    if type(descriptor) is not dict:
                        raise OCIRegistryReadError("OCI_REGISTRY_PLATFORM_INVALID")
                    platform = descriptor.get("platform")
                    if (type(platform) is dict
                            and platform.get("os") == "linux"
                            and platform.get("architecture") == "amd64"
                            and platform.get("variant") in (None, "v1")):
                        matches.append(descriptor)
                if len(matches) != 1:
                    raise OCIRegistryReadError("OCI_REGISTRY_PLATFORM_INVALID")
                selected = matches[0]
                child_digest = selected.get("digest")
                size = selected.get("size")
                if (not _digest(child_digest) or selected.get("mediaType") not in _IMAGE_MEDIA
                        or type(size) is not int or size <= 0 or size > _MAX_MANIFEST):
                    raise OCIRegistryReadError("OCI_REGISTRY_PLATFORM_INVALID")
                image_manifest_digest = child_digest
                resolved_platform = "linux/amd64"
                manifest, media, actual_size = await self._manifest(client, child_digest, token)
                if media != selected["mediaType"] or actual_size != size:
                    raise OCIRegistryReadError("OCI_REGISTRY_PLATFORM_INVALID")

            if media not in _IMAGE_MEDIA:
                raise OCIRegistryReadError("OCI_REGISTRY_MEDIA_UNSUPPORTED")
            config = manifest.get("config")
            if (type(config) is not dict or config.get("mediaType") not in _CONFIG_MEDIA
                    or not _digest(config.get("digest"))
                    or type(config.get("size")) is not int or config["size"] <= 0):
                raise OCIRegistryReadError("OCI_REGISTRY_CONFIG_INVALID")
            if type(manifest.get("layers")) is not list:
                raise OCIRegistryReadError("OCI_REGISTRY_MANIFEST_INVALID")
            return OCIImageIdentity(
                image=IMAGE,
                manifest_digest=manifest_digest,
                image_manifest_digest=image_manifest_digest,
                image_config_id=config["digest"],
                platform=resolved_platform,
                read_at=now.astimezone(timezone.utc),
            )
