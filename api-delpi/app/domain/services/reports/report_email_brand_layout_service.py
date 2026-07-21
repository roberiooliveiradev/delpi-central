"""Layout HTML de e-mail Delpi Reports — marca (logo CID + faixa + rodapé).

Layout table-based para compatibilidade com Outlook. Cores alinhadas ao
certificado / inspeção-entrada (`#013866` → `#30B8EC`).
"""

from __future__ import annotations

import html

# Content-ID do anexo inline Graph (sem ângulos; HTML usa cid:…).
LOGO_CONTENT_ID = "delpi-logo"

BLUE_900 = "#013866"
BLUE_700 = "#015488"
BLUE_500 = "#208BB8"
BLUE_ACCENT = "#30B8EC"
GRAY_900 = "#1A202C"
GRAY_600 = "#64748B"
GRAY_200 = "#E2E8F0"
GRAY_50 = "#F8FAFC"
HEADER_BG = "#f8fbfd"

_BRAND_COLORS = (BLUE_900, BLUE_700, BLUE_500, BLUE_ACCENT)

_FOOTER_SITE = "www.delpi.com.br"
_FOOTER_META = "Gerado pelo Minha DELPI — Relatórios"


class ReportEmailBrandLayoutService:
    """Monta o envelope de marca em torno do miolo do provider."""

    @staticmethod
    def brand_bar_html() -> str:
        cells = "".join(
            f'<td width="25%" style="background:{color};height:4px;'
            f'font-size:0;line-height:0;">&nbsp;</td>'
            for color in _BRAND_COLORS
        )
        return (
            '<table role="presentation" width="100%" cellpadding="0" '
            'cellspacing="0" border="0" style="border-collapse:collapse;">'
            f"<tr>{cells}</tr></table>"
        )

    @staticmethod
    def data_table_html(
        *,
        headers: list[str],
        rows: list[list[str]],
        column_styles: list[str] | None = None,
        raw_html_columns: frozenset[int] | None = None,
    ) -> str:
        """Tabela de dados com cabeçalho azul e zebra leve.

        ``raw_html_columns``: índices de coluna cujo conteúdo já é HTML seguro
        (não aplicar ``html.escape`` de novo).
        """
        styles = column_styles or []
        raw_indexes = raw_html_columns or frozenset()

        def _col_style(index: int) -> str:
            if index < len(styles) and styles[index]:
                return styles[index]
            return ""

        header_cells = "".join(
            f'<th style="background:{BLUE_900};color:#ffffff;padding:8px 10px;'
            f'text-align:left;font-size:12px;font-weight:700;'
            f'border:1px solid {BLUE_900};{_col_style(i)}">{html.escape(h)}</th>'
            for i, h in enumerate(headers)
        )
        body_rows: list[str] = []
        for index, cells in enumerate(rows):
            bg = "#ffffff" if index % 2 == 0 else GRAY_50
            tds = "".join(
                f'<td style="padding:7px 10px;font-size:12px;color:{GRAY_900};'
                f'border:1px solid {GRAY_200};background:{bg};{_col_style(i)}">'
                f"{cells[i] if i in raw_indexes else html.escape(cells[i])}</td>"
                for i in range(len(cells))
            )
            body_rows.append(f"<tr>{tds}</tr>")

        return (
            '<table role="presentation" width="100%" cellpadding="0" '
            'cellspacing="0" border="0" '
            f'style="border-collapse:collapse;font-family:Arial,Helvetica,'
            f'sans-serif;margin:0 0 8px 0;">'
            f"<thead><tr>{header_cells}</tr></thead>"
            f"<tbody>{''.join(body_rows)}</tbody>"
            "</table>"
        )

    @classmethod
    def wrap(
        cls,
        *,
        title: str,
        body_html: str,
        subtitle: str | None = None,
        logo_content_id: str = LOGO_CONTENT_ID,
    ) -> str:
        safe_title = html.escape(title)
        safe_subtitle = html.escape(subtitle) if subtitle else ""
        logo = (
            f'<img src="cid:{html.escape(logo_content_id)}" '
            'alt="DELPI Conexões Elétricas" width="140" '
            'style="display:block;width:140px;height:auto;border:0;" />'
        )
        subtitle_block = (
            f'<p style="margin:4px 0 0 0;font-size:13px;color:{GRAY_600};'
            f'font-family:Arial,Helvetica,sans-serif;">{safe_subtitle}</p>'
            if safe_subtitle
            else ""
        )
        bar = cls.brand_bar_html()

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8" /><meta name="viewport" content="width=device-width" /></head>
<body style="margin:0;padding:0;background:#ffffff;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
  style="border-collapse:collapse;max-width:860px;margin:0 auto;
  font-family:Arial,Helvetica,sans-serif;color:{GRAY_900};">
  <tr>
    <td style="background:linear-gradient(180deg,{HEADER_BG} 0%,#ffffff 100%);
      border:1px solid {GRAY_200};border-bottom:none;padding:20px 28px 14px 28px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
          <td width="150" valign="middle" style="padding-right:16px;">{logo}</td>
          <td valign="middle">
            <h1 style="margin:0;font-size:18px;line-height:1.25;font-weight:700;
              color:{BLUE_900};font-family:Arial,Helvetica,sans-serif;">{safe_title}</h1>
            {subtitle_block}
          </td>
        </tr>
      </table>
    </td>
  </tr>
  <tr><td>{bar}</td></tr>
  <tr>
    <td style="padding:28px 32px 32px 32px;border-left:1px solid {GRAY_200};
      border-right:1px solid {GRAY_200};font-size:14px;line-height:1.45;">
      {body_html}
    </td>
  </tr>
  <tr><td>{bar}</td></tr>
  <tr>
    <td style="background:{BLUE_900};padding:16px 28px;text-align:center;">
      <p style="margin:0 0 4px 0;font-size:12px;color:#CBD5E1;
        font-family:Arial,Helvetica,sans-serif;">{html.escape(_FOOTER_SITE)}</p>
      <p style="margin:0;font-size:11px;color:#E2E8F0;
        font-family:Arial,Helvetica,sans-serif;">{html.escape(_FOOTER_META)}</p>
    </td>
  </tr>
</table>
</body>
</html>"""
