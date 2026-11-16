"""Mail adapter for travel expense finance reports.

Uses the existing Microsoft Graph application credentials. Intentionally no
automatic send retry, since a timeout can mean delivery already occurred.
"""
from __future__ import annotations

import base64
import html
import os
from urllib.parse import quote

import httpx


class FinanceMailError(RuntimeError):
    pass


class FinanceReportMailer:
    def __init__(self, *, client: httpx.Client | None = None):
        self.client = client

    def send(self, *, report: dict, pdf: bytes, recipient: str, cc: str) -> None:
        tenant = (os.getenv("GRAPH_REPORTS_TENANT_ID") or os.getenv("GRAPH_TENANT_ID") or "").strip()
        client_id = (os.getenv("GRAPH_REPORTS_CLIENT_ID") or os.getenv("GRAPH_CLIENT_ID") or "").strip()
        secret = (os.getenv("GRAPH_REPORTS_CLIENT_SECRET") or os.getenv("GRAPH_CLIENT_SECRET") or "").strip()
        sender = (os.getenv("GRAPH_REPORTS_MAIL_SENDER") or "minhadelpi@delpi.com.br").strip()
        if not all((tenant, client_id, secret, sender)):
            raise FinanceMailError("Credenciais do Microsoft Graph não configuradas para Despesas de Viagem.")
        number = str(report.get("number") or "")
        subject = f"[DELPI] Prestação de contas de viagem {number}"
        detail_url = ((os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")
                      + "/apps/travel-expenses/reports/" + quote(str(report["id"]), safe=""))
        body = (
            "<p>Uma prestação de despesas de viagem foi encaminhada ao Financeiro.</p>"
            f"<p><strong>Relatório:</strong> {html.escape(number)}<br>"
            f"<strong>Colaborador:</strong> {html.escape(str(report.get('createdByName') or cc))}<br>"
            f"<strong>Unidade:</strong> {html.escape(str(report.get('unitCode') or ''))}<br>"
            f"<strong>Destino:</strong> {html.escape(str(report.get('destination') or ''))}<br>"
            f"<strong>Total:</strong> R$ {float(report.get('totalAmountBrl') or 0):.2f}</p>"
            f'<p><a href="{html.escape(detail_url, quote=True)}">Consultar relatório</a></p>'
            "<p>O PDF consolidado está anexado.</p>"
        )
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body},
                "toRecipients": [{"emailAddress": {"address": recipient}}],
                "ccRecipients": [{"emailAddress": {"address": cc}}],
                "attachments": [{
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": f"prestacao-{number}.pdf",
                    "contentType": "application/pdf",
                    "contentBytes": base64.b64encode(pdf).decode("ascii"),
                }],
            },
            "saveToSentItems": True,
        }
        transport = self.client or httpx.Client(timeout=20.0)
        try:
            response = transport.post(
                f"https://login.microsoftonline.com/{quote(tenant, safe='')}/oauth2/v2.0/token",
                data={"client_id": client_id, "client_secret": secret,
                      "scope": "https://graph.microsoft.com/.default",
                      "grant_type": "client_credentials"},
            )
            if response.status_code != 200:
                raise FinanceMailError(f"Falha de autenticação com Microsoft Graph (HTTP {response.status_code}).")
            token = response.json().get("access_token")
            if not token:
                raise FinanceMailError("O Microsoft Graph não retornou token de acesso.")
            response = transport.post(
                f"https://graph.microsoft.com/v1.0/users/{quote(sender, safe='')}/sendMail",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            if response.status_code != 202:
                raise FinanceMailError(f"Microsoft Graph não aceitou o envio (HTTP {response.status_code}).")
        except httpx.HTTPError as exc:
            raise FinanceMailError("Falha de comunicação com o Microsoft Graph. Verifique o histórico antes de tentar novamente.") from exc
        finally:
            if self.client is None:
                transport.close()
