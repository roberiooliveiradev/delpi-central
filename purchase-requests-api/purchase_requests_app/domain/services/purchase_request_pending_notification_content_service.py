"""Plain preview and escaped, complete HTML details for daily reminders."""

import json
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import urlencode


@lru_cache(maxsize=1)
def _content():
    path = (
        Path(__file__).resolve().parents[2]
        / "content/pt-BR/purchase_request_pending_notification.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def build_pending_notification(document: dict, *, recipient_role: str) -> dict:
    content = _content()
    number, branch = document["request_number"], document["branch"]
    names = [
        str(a.get("name") or a.get("code") or content["unknownApprover"])
        for a in document["pending_approvers"]
    ]
    products = [
        " — ".join(str(v) for v in (p["code"], p.get("description")) if v)
        for p in document["products"]
    ]
    title = content[f"{recipient_role}Title"].format(request=number)
    introduction = content[f"{recipient_role}Message"]
    details = " ".join(
        (
            introduction,
            f'{content["approversLabel"]}: {", ".join(names)}.',
            f'{content["productsLabel"]}: {"; ".join(products)}.',
        )
    )
    if len(details) > 500:
        details = (
            details[: (496 - len(content["detailsLabel"]))]
            + "… "
            + content["detailsLabel"]
        )
    html = f'<p><strong>{escape(content["document"].format(request=number, branch=branch))}</strong></p>'
    html += f"<p>{escape(introduction)}</p>"
    for label, entries in (("approversLabel", names), ("productsLabel", products)):
        html += f"<p><strong>{escape(content[label])}</strong></p><ul>"
        html += "".join(f"<li>{escape(value)}</li>" for value in entries) + "</ul>"
    query = {
        "branch": branch,
        "request_number": number,
        "request": f"{branch}:{number}",
    }
    if document.get("request_issue_date"):
        query["date_from"] = document["request_issue_date"]
    return {
        "title": title,
        "message": details,
        "html_content": html,
        "category": content[f"{recipient_role}Category"],
        "action_label": content["actionLabel"],
        "action_target": "/apps/purchase-requests?" + urlencode(query),
    }
