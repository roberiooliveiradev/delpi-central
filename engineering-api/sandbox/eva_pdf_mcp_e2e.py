"""E2E DEC-VAL-016 — product.drawing_download via EVA MCP (cliente real).

Fluxo: password grant (delpi-central) → token-exchange (delia-api →
audience mcp-engineering) → MCP streamable HTTP real → tools/list →
tools/call read(product,drawing_download) → EmbeddedResource blob →
materialização .pdf → sha256/size → renderização página 1.
Não imprime tokens, secrets nem blobs.
"""

import asyncio
import base64
import hashlib
import json
import os
import urllib.parse
import urllib.request

from mcp import ClientSession
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client
from mcp.types import EmbeddedResource, TextContent

KC_PUBLIC = "http://delpi-gateway/auth/realms/delpi/protocol/openid-connect/token"
KC_INTERNAL = "http://delpi-keycloak:8080/auth/realms/delpi/protocol/openid-connect/token"
MCP_URL = "http://engineering-api:8000/mcp"
USER = os.environ["E2E_USER"]
PWD = os.environ["E2E_PASS"]
EXCHANGE_SECRET = os.environ["MCP_CLIENT_SECRET"]
OUT = "/tmp/eva_pdf_e2e"


def _post(url, fields, host=None):
    data = urllib.parse.urlencode(fields).encode()
    headers = {"Host": host} if host else {}
    req = urllib.request.Request(url, data=data, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=20).read())


def _claims(tok):
    p = tok.split(".")[1]
    p += "=" * (-len(p) % 4)
    return json.loads(base64.urlsafe_b64decode(p))


def _mint(username):
    t = _post(
        KC_PUBLIC,
        {
            "grant_type": "password",
            "client_id": "delpi-central",
            "username": username,
            "password": PWD,
            "scope": "openid",
        },
        host="localhost",
    )
    return t["access_token"]


def _exchange(subject):
    # mcp-engineering confidential client — direct grant (habilitado
    # temporariamente no realm local para a prova; prod segue auth-code).
    t = _post(
        KC_PUBLIC,
        {
            "grant_type": "password",
            "client_id": "mcp-engineering",
            "client_secret": EXCHANGE_SECRET,
            "username": _current_user,
            "password": PWD,
            "scope": "openid profile email mcp:tools",
        },
        host="localhost",
    )
    return t["access_token"]

_current_user = None


async def _raw_init_probe(headers):
    """POST initialize cru — diagnóstico transporte negativo."""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "eva-e2e", "version": "0"},
        },
    }).encode()
    req = urllib.request.Request(
        MCP_URL, data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Host": "localhost:8000",
            **headers,
        },
    )
    try:
        urllib.request.urlopen(req, timeout=15)
        return "200"
    except urllib.error.HTTPError as e:
        return str(e.code)


async def _download(session, product_code):
    r = await session.call_tool(
        "read",
        {
            "entity": "product",
            "action": "drawing_download",
            "ref": product_code,
        },
    )
    return r


async def main():
    os.makedirs(OUT, exist_ok=True)

    # ---- transporte negativo -------------------------------------------------
    no_tok = await _raw_init_probe({})
    print(f"[E] no-token initialize -> HTTP {no_tok}")
    global _current_user
    _current_user = USER
    subject = _mint(USER)
    c = _claims(subject)
    print(f"[E] subject aud={c.get('aud')} scope={c.get('scope')!r}")
    wrong_aud = await _raw_init_probe({"Authorization": f"Bearer {subject}"})
    print(f"[E] wrong-audience initialize -> HTTP {wrong_aud}")

    _current_user = "devin-eva-denied"
    denied_tok = _exchange(None)
    _current_user = USER
    denied_init = await _raw_init_probe({"Authorization": f"Bearer {denied_tok}"})
    print(f"[E] denied-user initialize -> HTTP {denied_init}")

    # ---- token EVA válido ----------------------------------------------------
    token = _exchange(subject)
    c = _claims(token)
    aud = c.get("aud")
    ok_aud = "http://localhost/apps/engineering-api/mcp" in (
        aud if isinstance(aud, list) else [aud]
    )
    print(f"[+] eva-token aud-ok={ok_aud} scope={c.get('scope')!r} azp={c.get('azp')}")

    products = ["99900001",
        "90264302", "90264161", "90263520", "90261606",
        "90263572", "90264178", "90480120",
    ]
    rendered = []

    async with create_mcp_http_client(
        headers={
            "Authorization": f"Bearer {token}",
            "Host": "localhost:8000",
        },
    ) as http_client:
        async with streamable_http_client(
            MCP_URL, http_client=http_client
        ) as (read_s, write_s):
            async with ClientSession(read_s, write_s) as session:
                init = await session.initialize()
                print(f"[A] protocol={init.protocol_version} server={init.server_info.name}")
                tools = await session.list_tools()
                names = [t.name for t in tools.tools]
                print(f"[A] tools/list -> {names}")
                assert names == [
                    "get_context", "read", "analyze",
                    "knowledge", "execute", "delete",
                ], names

                # discovery: action anunciada no get_context
                gctx = await session.call_tool(
                    "get_context", {"entity": "product"}
                )
                gdata = gctx.structured_content["data"]
                actions = {a["action"] for a in gdata["actions"]}
                print(f"[A] product actions -> {sorted(actions)}")
                assert "drawing_download" in actions

                # compat: metadados intactos
                meta = await session.call_tool(
                    "read",
                    {
                        "entity": "product",
                        "action": "drawing",
                        "ref": "90264302",
                    },
                )
                print(f"[F] product.drawing metadata ok={not meta.is_error}")

                for code in products:
                    r = await _download(session, code)
                    if r.is_error:
                        sc = r.structured_content or {}
                        print(f"[B] {code}: isError {sc.get('status_code')} {sc.get('message')}")
                        continue
                    data = r.structured_content["data"]
                    kinds = [type(i).__name__ for i in r.content]
                    emb = next(
                        (i for i in r.content if isinstance(i, EmbeddedResource)),
                        None,
                    )
                    assert emb is not None, f"{code}: no EmbeddedResource {kinds}"
                    blob = base64.b64decode(emb.resource.blob)
                    sha = hashlib.sha256(blob).hexdigest()
                    path = f"{OUT}/{code}.pdf"
                    with open(path, "wb") as f:
                        f.write(blob)
                    ok_sha = sha == data["sha256"]
                    ok_size = len(blob) == data["size_bytes"]
                    print(
                        f"[B/C] {code}: bytes={len(blob)} "
                        f"sha_match={ok_sha} size_match={ok_size} "
                        f"file={data['filename']} mime={emb.resource.mime_type}"
                    )
                    assert ok_sha and ok_size
                    rendered.append((code, path))

                # negativo: produto sem desenho/documento
                nf = await _download(session, "ZZZZZ999")
                print(f"[E] unknown-product isError={nf.is_error} "
                      f"status={(nf.structured_content or {}).get('status_code')}")

    # ---- denied user via client real ------------------------------------------
    async with create_mcp_http_client(
        headers={
            "Authorization": f"Bearer {denied_tok}",
            "Host": "localhost:8000",
        },
    ) as http_client:
        async with streamable_http_client(
            MCP_URL, http_client=http_client
        ) as (read_s, write_s):
            async with ClientSession(read_s, write_s) as session:
                await session.initialize()
                r = await _download(session, "90264302")
                print(
                    f"[E] denied-user tools/call isError={r.is_error} "
                    f"status={(r.structured_content or {}).get('status_code')}"
                )

    # ---- renderização -----------------------------------------------------------
    import pypdfium2 as pdfium

    for code, path in rendered:
        pdf = pdfium.PdfDocument(path)
        n = len(pdf)
        page = pdf[0]
        bitmap = page.render(scale=1.0)
        img = bitmap.to_pil()
        out_png = f"{OUT}/{code}-p1.png"
        img.save(out_png)
        print(
            f"[D] {code}: pages={n} rendered={img.size[0]}x{img.size[1]} "
            f"magic={open(path, 'rb').read(5)}"
        )
        pdf.close()


asyncio.run(main())
