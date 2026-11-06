"""Shared MCP Apps avatar UI surface (MCP-AVATAR-UI-V2).

Transport-neutral helpers for the MCP Apps visual contract: each owner
registers a ``ui://delpi/{character}/avatar/v{N}`` resource serving this
HTML (``text/html;profile=mcp-app``) and links a read-only tool to it
through tool ``_meta.ui.resourceUri``.

This module owns *presentation mechanics* only — template, CSP,
alt/fallback — never owner internals, never user-supplied URLs. The
image URL passed in must already be the validated public HTTPS
``avatar_distribution`` URL of the owning service.
"""

from __future__ import annotations

import html
from urllib.parse import urlsplit

AVATAR_UI_MIME = "text/html;profile=mcp-app"


def avatar_ui_resource_uri(character_id: str, version: int = 1) -> str:
    """Versioned ``ui://`` URI for a character's avatar surface."""
    cid = str(character_id or "").strip().lower()
    return f"ui://delpi/{cid}/avatar/v{int(version)}"


def avatar_ui_meta(resource_uri: str) -> dict:
    """Tool ``_meta`` linking a visual tool to its ``ui://`` resource.

    Merge into the tool's existing ``_meta`` (e.g. vendor-namespaced
    securitySchemes): ``{**meta, **avatar_ui_meta(uri)}``.
    """
    # ui.resourceUri — generic MCP Apps link; openai/outputTemplate —
    # the key ChatGPT's Apps SDK recognizes for widget rendering (V2.1).
    return {
        "ui": {"resourceUri": resource_uri},
        "openai/outputTemplate": resource_uri,
    }


def avatar_ui_resource_meta(image_url: str | None) -> dict:
    """Resource ``_meta.ui.csp`` for the avatar ``ui://`` resource.

    Declares the approved image origin so the host can allowlist the
    iframe sandbox — ``connect-src 'none'`` (the component opens no
    connections). Merge into the resource's registration ``meta``.
    """
    origin = _origin(image_url or "")
    domains = [origin] if origin else []
    return {
        "ui": {
            "csp": {
                "resourceDomains": domains,
                "connectDomains": [],
            }
        }
    }


def _origin(url: str) -> str:
    parts = urlsplit(url or "")
    if parts.scheme == "https" and parts.netloc:
        return f"{parts.scheme}://{parts.netloc}"
    return ""


def build_avatar_ui_html(
    *,
    display_name: str,
    specialty: str = "",
    description: str = "",
    image_url: str | None = None,
    alt_text: str | None = None,
) -> str:
    """Minimal responsive avatar card for MCP Apps hosts.

    Render-only component: restrictive CSP allowing the approved image
    origin only, inline styles, light/dark themes, accessible alt text
    and a textual fallback. A tiny bridge reads ``window.openai``
    toolInput/toolOutput when the host injects them — nothing else runs.
    """
    name = html.escape(display_name or "Especialista")
    spec = html.escape(specialty or "")
    desc = html.escape(description or "")
    url = image_url if image_url and image_url.startswith("https://") else ""
    safe_url = html.escape(url, quote=True)
    alt = html.escape(alt_text or f"Avatar oficial de {display_name}")
    origin = _origin(url)
    img_src = f"{origin} {url}".strip() if origin else url
    csp_img = img_src or "'none'"
    csp = (
        "default-src 'none'; "
        f"img-src {csp_img}; "
        "style-src 'unsafe-inline'; "
        "script-src 'unsafe-inline'; "
        "connect-src 'none';"
    )
    img_tag = ""
    if url:
        img_tag = (
            '<img id="avatar-img" src="'
            + safe_url
            + '" alt="'
            + alt
            + '">'
        )
    desc_tag = '<p class="desc">' + desc + "</p>" if desc else ""
    fallback_tag = "" if url else (
        '<p class="fallback">Avatar oficial indisponível no momento.</p>'
    )
    template = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="__CSP__">
<title>__NAME__</title>
<style>
  :root { color-scheme: light dark; }
  body { margin: 0; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }
  figure { margin: 0; padding: 0; }
  .card { display: flex; flex-direction: column; align-items: center;
          padding: 12px; gap: 10px; max-width: 520px; margin: 0 auto; }
  .card img { width: 100%; height: auto; max-height: 560px; object-fit: contain;
              border-radius: 12px; display: block; }
  .cap { text-align: center; }
  .cap strong { display: block; font-size: 1rem; }
  .cap span { display: block; font-size: 0.85rem; opacity: 0.8; margin-top: 2px; }
  .desc { font-size: 0.85rem; opacity: 0.85; text-align: center; margin: 0; }
  .fallback { font-size: 0.85rem; opacity: 0.8; padding: 16px; text-align: center; }
</style>
</head>
<body>
<figure class="card" id="avatar-card">
  __IMG_TAG__
  <figcaption class="cap">
    <strong id="avatar-name">__NAME__</strong>
    <span id="avatar-specialty">__SPEC__</span>
  </figcaption>
  __DESC_TAG__
  __FALLBACK_TAG__
</figure>
<script>
(function () {
  "use strict";
  function applyOutput(out) {
    if (!out || typeof out !== "object") return;
    var img = document.getElementById("avatar-img");
    var u = out.image_url || out.url;
    if (u && img && u.indexOf("https://") === 0) img.src = u;
    var n = out.display_name || out.name;
    if (n) {
      var el = document.getElementById("avatar-name");
      if (el) el.textContent = n;
      if (img) img.alt = "Avatar oficial de " + n;
    }
    var s = out.specialty;
    if (s) {
      var se = document.getElementById("avatar-specialty");
      if (se) se.textContent = s;
    }
  }

  /* --- MCP Apps lifecycle (ui/initialize -> initialized -> tool-result)
     V2.2: the host waits for the widget to ACK initialize and emit
     initialized before delivering the tool result; a static page that
     never answers is exactly the observed timeout. Render-only —
     every handler is wrapped so a protocol mismatch can never reject
     the host promise chain. --- */
  var initialized = false;
  function notify(method, params) {
    try {
      window.parent.postMessage(
        { jsonrpc: "2.0", method: method, params: params || {} }, "*"
      );
    } catch (_) {}
  }
  function onMessage(ev) {
    try {
      var m = ev && ev.data;
      if (!m || m.jsonrpc !== "2.0") return;
      var method = m.method;
      if (method === "ui/initialize" && m.id != null && !initialized) {
        initialized = true;
        window.parent.postMessage(
          {
            jsonrpc: "2.0",
            id: m.id,
            result: {
              protocolVersion: m.params && m.params.protocolVersion,
              clientInfo: { name: "delpi-avatar-card", version: "2.0" },
              clientCapabilities: {},
            },
          },
          "*"
        );
        notify("ui/notifications/initialized");
      } else if (method === "ui/notifications/tool-result") {
        var p = m.params || {};
        applyOutput(
          p.structuredContent || p.structured_content ||
            (p.result && (p.result.structuredContent || p.result)) ||
            p
        );
      } else if (method === "ui/notifications/tool-input") {
        applyOutput(m.params && (m.params.structuredContent || m.params));
      }
    } catch (_) { /* render-only: never fail the host */ }
  }
  window.addEventListener("message", onMessage);
  try {
    // Also ping the host in case it listens for a ready signal
    // instead of driving ui/initialize (older bridges).
    notify("ui/notifications/widget-ready");
  } catch (_) {}

  /* --- window.openai fallback (ChatGPT Apps SDK bridge) --- */
  try {
    var o = (typeof window !== "undefined") && window.openai;
    var out = o && (o.toolOutput || o.toolInput || null);
    if (out) applyOutput(out);
  } catch (_) {}
})();
</script>
</body>
</html>"""
    return (
        template.replace("__CSP__", csp)
        .replace("__NAME__", name)
        .replace("__SPEC__", spec)
        .replace("__IMG_TAG__", img_tag)
        .replace("__DESC_TAG__", desc_tag)
        .replace("__FALLBACK_TAG__", fallback_tag)
    )
