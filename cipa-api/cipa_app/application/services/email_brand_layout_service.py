"""Layout HTML de e-mail CIPA — faixa colorida + rodapé (Outlook-safe)."""

from __future__ import annotations

import html

BLUE_900 = "#013866"
BLUE_700 = "#015488"
BLUE_500 = "#208BB8"
BLUE_ACCENT = "#30B8EC"
GRAY_900 = "#1A202C"
GRAY_600 = "#64748B"
GRAY_200 = "#E2E8F0"
HEADER_BG = "#f8fbfd"

_BRAND_COLORS = (BLUE_900, BLUE_700, BLUE_500, BLUE_ACCENT)


class CipaEmailBrandLayoutService:
    """Envelope de marca para e-mails do CIPA."""

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

    @classmethod
    def wrap(
        cls,
        *,
        title: str,
        body_html: str,
        subtitle: str | None = None,
        footer_site: str,
        footer_meta: str,
    ) -> str:
        safe_title = html.escape(title)
        safe_subtitle = html.escape(subtitle) if subtitle else ""
        bar = cls.brand_bar_html()

        subtitle_block = (
            f'<p style="margin:4px 0 0 0;font-size:12px;color:{GRAY_600};'
            f'font-family:Arial,Helvetica,sans-serif;letter-spacing:0.02em;">'
            f"{safe_subtitle}</p>"
            if safe_subtitle
            else ""
        )

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8" /><meta name="viewport" content="width=device-width" /></head>
<body style="margin:0;padding:0;background:#ffffff;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
  style="border-collapse:collapse;max-width:640px;margin:0 auto;
  font-family:Arial,Helvetica,sans-serif;color:{GRAY_900};">
  <tr>
    <td style="background:linear-gradient(180deg,{HEADER_BG} 0%,#ffffff 100%);
      border:1px solid {GRAY_200};border-bottom:none;padding:20px 28px 14px 28px;">
      <h1 style="margin:0;font-size:18px;line-height:1.25;font-weight:700;
        color:{BLUE_900};font-family:Arial,Helvetica,sans-serif;">{safe_title}</h1>
      {subtitle_block}
    </td>
  </tr>
  <tr><td>{bar}</td></tr>
  <tr>
    <td style="padding:28px 32px 28px 32px;border-left:1px solid {GRAY_200};
      border-right:1px solid {GRAY_200};font-size:14px;line-height:1.5;">
      {body_html}
    </td>
  </tr>
  <tr><td>{bar}</td></tr>
  <tr>
    <td style="background:{BLUE_900};padding:16px 28px;text-align:center;">
      <p style="margin:0 0 4px 0;font-size:12px;font-family:Arial,Helvetica,sans-serif;">
        <a href="https://{html.escape(footer_site)}"
          style="color:#FFFFFF !important;text-decoration:none;
          font-family:Arial,Helvetica,sans-serif;">{html.escape(footer_site)}</a>
      </p>
      <p style="margin:0;font-size:11px;color:#E2E8F0;
        font-family:Arial,Helvetica,sans-serif;">{html.escape(footer_meta)}</p>
    </td>
  </tr>
</table>
</body>
</html>"""
