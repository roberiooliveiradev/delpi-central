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
    return {"ui": {"resourceUri": resource_uri}}


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
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<title>{name}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin: 0; font-family: -apple-system, "Segoe UI", Roboto, sans-serif; }}
  figure {{ margin: 0; padding: 0; }}
  .card {{ display: flex; flex-direction: column; align-items: center;
          padding: 12px; gap: 10px; max-width: 520px; margin: 0 auto; }}
  .card img {{ width: 100%; height: auto; max-height: 560px; object-fit: contain;
              border-radius: 12px; display: block; }}
  .cap {{ text-align: center; }}
  .cap strong {{ display: block; font-size: 1rem; }}
  .cap span {{ display: block; font-size: 0.85rem; opacity: 0.8; margin-top: 2px; }}
  .desc {{ font-size: 0.85rem; opacity: 0.85; text-align: center; margin: 0; }}
  .fallback {{ font-size: 0.85rem; opacity: 0.8; padding: 16px; text-align: center; }}
</style>
</head>
<body>
<figure class="card" id="avatar-card">
  {"<img id=\"avatar-img\" src=\"" + safe_url + "\" alt=\"" + alt + "\">" if url else ""}
  <figcaption class="cap">
    <strong id="avatar-name">{name}</strong>
    <span id="avatar-specialty">{spec}</span>
  </figcaption>
  {"<p class=\"desc\">" + desc + "</p>" if desc else ""}
  {"" if url else "<p class=\"fallback\">Avatar oficial indisponível no momento.</p>"}
</figure>
<script>
(function () {{
  try {{
    var o = (typeof window !== "undefined") && window.openai;
    var out = o && (o.toolOutput || o.toolInput || null);
    if (!out || typeof out !== "object") return;
    var img = document.getElementById("avatar-img");
    var u = out.image_url || out.url;
    if (u && img && /^https:\\/\\//.test(u)) img.src = u;
    var n = out.display_name || out.name;
    if (n) {{
      var el = document.getElementById("avatar-name");
      if (el) el.textContent = n;
      if (img) img.alt = "Avatar oficial de " + n;
    }}
    var s = out.specialty;
    if (s) {{
      var se = document.getElementById("avatar-specialty");
      if (se) se.textContent = s;
    }}
  }} catch (_) {{ /* render-only: never fail the host */ }}
}})();
</script>
</body>
</html>"""
