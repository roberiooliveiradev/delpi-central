from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable

from app.domain.propostas_comerciais.ports.proposta_comercial_pdf_renderer_port import (
    PropostaComercialPdfRendererPort,
)

# Paleta institucional DELPI (referencia logo oficial)
DELPI_BLUE = colors.HexColor("#013866")
DELPI_ACCENT = colors.HexColor("#30B8EC")
DELPI_BLUE_MID = colors.HexColor("#015488")
DELPI_BLUE_LIGHT = colors.HexColor("#208BB8")
FOOTER_BRAND_BAR_HEIGHT = 2.5 * mm
FOOTER_BRAND_BAR_COLORS = (DELPI_BLUE, DELPI_BLUE_MID, DELPI_BLUE_LIGHT, DELPI_ACCENT)
SURFACE_SOFT = colors.HexColor("#F8FAFC")
SURFACE_MUTED = colors.HexColor("#F1F5F9")
LINE = colors.HexColor("#E2E8F0")
TEXT = colors.HexColor("#1A202C")
TEXT_MUTED = colors.HexColor("#64748B")
WHITE = colors.white

MARGIN_LEFT = 12 * mm
MARGIN_RIGHT = 12 * mm
MARGIN_TOP = 11 * mm
MARGIN_BOTTOM = 14 * mm
CONTENT_WIDTH = A4[0] - MARGIN_LEFT - MARGIN_RIGHT

LOGO_MAX_WIDTH = 48 * mm
LOGO_MAX_HEIGHT = 13 * mm
_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
_DEFAULT_LOGO = _ASSETS_DIR / "logo_delpi.svg"

FIXED_CONDITION_TEXTS = (
    "Favor informar em seu pedido: o número de nossa proposta.",
    "Cancelamento/Reprogramação de pedido: somente mediante autorização prévia da Delpi.",
)


class _DrawingFlowable(Flowable):
    def __init__(self, drawing, width: float, height: float):
        self.drawing = drawing
        self.width = width
        self.height = height

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        from reportlab.graphics import renderPDF

        renderPDF.draw(self.drawing, self.canv, 0, 0)


class _NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, footer_site: str = "www.delpi.com.br", **kwargs):
        super().__init__(*args, **kwargs)
        self._footer_site = footer_site
        self._page_states: list[dict] = []

    def showPage(self) -> None:
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total_pages = len(self._page_states)
        for state in self._page_states:
            self.__dict__.update(state)
            self._draw_footer(total_pages)
            super().showPage()
        super().save()

    def _draw_footer(self, total_pages: int) -> None:
        self.saveState()
        self.setStrokeColor(LINE)
        self.setLineWidth(0.35)
        self.line(MARGIN_LEFT, 13.5 * mm, A4[0] - MARGIN_RIGHT, 13.5 * mm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(TEXT_MUTED)
        self.drawString(MARGIN_LEFT, 9 * mm, self._footer_site)
        self.drawRightString(A4[0] - MARGIN_RIGHT, 9 * mm, f"Página {self._pageNumber} de {total_pages}")
        if self._pageNumber == total_pages:
            _draw_brand_footer_bar(self)
        self.restoreState()


def _draw_brand_footer_bar(page_canvas: canvas.Canvas) -> None:
    page_width = A4[0]
    segment_width = page_width / len(FOOTER_BRAND_BAR_COLORS)
    for index, color in enumerate(FOOTER_BRAND_BAR_COLORS):
        page_canvas.setFillColor(color)
        page_canvas.setStrokeColor(color)
        page_canvas.rect(
            index * segment_width,
            0,
            segment_width,
            FOOTER_BRAND_BAR_HEIGHT,
            fill=1,
            stroke=0,
        )


class PropostaComercialPdfRenderer(PropostaComercialPdfRendererPort):
    def render(self, detail: dict) -> bytes:
        buffer = _PdfBuffer()
        empresa = detail.get("empresa") or {}
        footer_site = _display(empresa.get("site"), empty="www.delpi.com.br")
        if footer_site == "—":
            footer_site = "www.delpi.com.br"

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=MARGIN_LEFT,
            rightMargin=MARGIN_RIGHT,
            topMargin=MARGIN_TOP,
            bottomMargin=MARGIN_BOTTOM,
            title=self._document_title(detail),
            author="DELPI",
        )
        styles = _build_styles()
        story = self._build_story(detail, styles)

        def on_page(page_canvas, document):
            _draw_running_header(page_canvas, detail, first_page=document.page == 1)

        doc.build(
            story,
            canvasmaker=lambda *args, **kwargs: _NumberedCanvas(
                *args, footer_site=footer_site, **kwargs
            ),
            onFirstPage=on_page,
            onLaterPages=on_page,
        )
        return buffer.getvalue()

    @staticmethod
    def _document_title(detail: dict) -> str:
        cabecalho = detail.get("cabecalho") or {}
        numero_ov = cabecalho.get("numero_ov") or cabecalho.get("proposta_interna") or "Proposta"
        return f"Proposta Comercial {numero_ov}"

    def _build_story(self, detail: dict, styles: dict[str, ParagraphStyle]) -> list[Flowable]:
        cabecalho = detail.get("cabecalho") or {}
        empresa = detail.get("empresa") or {}
        cliente = detail.get("cliente") or {}
        contato = detail.get("contato") or {}
        condicoes = detail.get("condicoes") or {}
        vendedor = detail.get("vendedor") or {}
        itens = detail.get("itens") or []
        observacoes = str(detail.get("observacoes") or "").strip()

        story: list[Flowable] = []
        story.extend(self._build_document_header(cabecalho, empresa, styles))
        story.append(Spacer(1, 2 * mm))
        story.extend(self._build_client_contact_cards(cliente, contato, styles))
        story.append(Spacer(1, 3 * mm))
        story.extend(self._build_items_section(itens, cabecalho, styles))
        story.append(Spacer(1, 3 * mm))
        story.extend(self._build_conditions_section(cabecalho, condicoes, styles))
        story.append(Spacer(1, 2.5 * mm))
        story.extend(self._build_closing_sections(observacoes, vendedor, styles))
        return story

    def _build_document_header(
        self,
        cabecalho: dict,
        empresa: dict,
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        logo = _load_logo_flowable()
        if logo is None:
            logo = Paragraph('<font color="#013866"><b>DELPI</b></font>', styles["logoFallback"])

        numero_ov = _display(cabecalho.get("numero_ov"))
        versao = _display(cabecalho.get("versao"))
        data = _display(cabecalho.get("data"))

        meta = Table(
            [
                [Paragraph("PROPOSTA COMERCIAL", styles["headerLabel"])],
                [Paragraph(f"N° {_escape(numero_ov)}", styles["headerNumber"])],
                [
                    Paragraph(
                        f'<font color="#64748B">Versão</font> {_escape(versao)}'
                        f'&nbsp;&nbsp;&nbsp;<font color="#64748B">Data</font> {_escape(data)}',
                        styles["headerMeta"],
                    )
                ],
            ],
            colWidths=[CONTENT_WIDTH - LOGO_MAX_WIDTH - 6 * mm],
        )
        meta.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 2),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 4),
                    ("BOTTOMPADDING", (0, 2), (0, 2), 0),
                ]
            )
        )

        header_row = Table([[logo, meta]], colWidths=[LOGO_MAX_WIDTH + 4 * mm, CONTENT_WIDTH - LOGO_MAX_WIDTH - 4 * mm])
        header_row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        company_block = Paragraph(_format_empresa_lines(empresa), styles["headerCompany"])

        block = Table(
            [
                [header_row],
                [company_block],
            ],
            colWidths=[CONTENT_WIDTH],
        )
        block.setStyle(
            TableStyle(
                [
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (0, 0), 2),
                    ("BOTTOMPADDING", (0, 1), (0, 1), 0),
                ]
            )
        )

        return [
            block,
            Spacer(1, 2 * mm),
            HRFlowable(width="100%", thickness=0.5, color=LINE, spaceBefore=0, spaceAfter=0),
        ]

    def _build_client_contact_cards(
        self,
        cliente: dict,
        contato: dict,
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        card_width = (CONTENT_WIDTH - 4 * mm) / 2
        client_card = _build_labeled_card(
            "Cliente",
            [
                ("Nome", _display(cliente.get("nome"))),
                ("Endereço", _display(cliente.get("endereco"))),
                (
                    "Cidade/UF",
                    " - ".join(
                        p
                        for p in (
                            _display(cliente.get("cidade"), empty=""),
                            _display(cliente.get("uf"), empty=""),
                        )
                        if p
                    )
                    or "—",
                ),
                ("CNPJ", _display(cliente.get("cnpj"))),
            ],
            styles,
            card_width,
        )
        contact_card = _build_labeled_card(
            "Contato",
            [
                ("Nome", _display(contato.get("nome"))),
                ("Departamento", _display(contato.get("departamento"))),
                ("E-mail", _display(contato.get("email"))),
            ],
            styles,
            card_width,
        )

        row = Table([[client_card, contact_card]], colWidths=[card_width, card_width])
        row.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (0, 0), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 2.5 * mm),
                    ("LEFTPADDING", (1, 0), (1, 0), 2.5 * mm),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                ]
            )
        )
        return [row]

    def _build_items_section(
        self,
        itens: list[dict],
        cabecalho: dict,
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        headers = [
            "Item",
            "Ref. Delpi",
            "Ref. Cliente",
            "NCM",
            "Descrição",
            "Valor R$/mil",
            "Prazo",
            "Lote mín.",
        ]
        widths = [11 * mm, 17 * mm, 17 * mm, 20 * mm, 67 * mm, 27 * mm, 14 * mm, 13 * mm]

        rows: list[list[Flowable | str]] = [
            [_table_header_cell(label, styles) for label in headers]
        ]

        for item in itens:
            prazo = item.get("prazo_dias")
            prazo_text = "—" if prazo in (None, "") else f"{prazo} dias"
            lote = item.get("lote_minimo")
            lote_text = "—" if lote in (None, "") else str(lote)
            rows.append(
                [
                    Paragraph(_escape(_display(item.get("item"))), styles["tableCellCenter"]),
                    Paragraph(_escape(_display(item.get("produto"))), styles["tableCell"]),
                    Paragraph(_escape(_display(item.get("referencia_cliente"))), styles["tableCell"]),
                    Paragraph(_escape(_display(item.get("ncm"))), styles["tableCellNcm"]),
                    Paragraph(_escape_multiline(_display(item.get("descricao"))), styles["tableCell"]),
                    Paragraph(_escape(_display(item.get("valor_total"))), styles["tableCellMoney"]),
                    Paragraph(_escape(prazo_text), styles["tableCellCenter"]),
                    Paragraph(_escape(lote_text), styles["tableCellCenter"]),
                ]
            )

        soma = cabecalho.get("soma_valores_r_mil")
        has_total = bool(soma and soma != "—")
        if has_total:
            rows.append(
                [
                    "",
                    "",
                    "",
                    "",
                    Paragraph("<b>Total da proposta</b>", styles["tableCell"]),
                    Paragraph(f"<b>{_escape(_display(soma))}</b>", styles["tableCellMoneyBold"]),
                    "",
                    "",
                ]
            )

        table = Table(rows, colWidths=widths, repeatRows=1)
        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0), SURFACE_MUTED),
            ("TEXTCOLOR", (0, 0), (-1, 0), DELPI_BLUE),
            ("LINEBELOW", (0, 0), (-1, 0), 0.8, DELPI_BLUE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2 if has_total else -1), [WHITE, SURFACE_SOFT]),
            ("BOX", (0, 0), (-1, -1), 0.35, LINE),
            ("INNERGRID", (0, 0), (-1, -2 if has_total else -1), 0.25, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (3, 0), (3, -1), 2),
            ("RIGHTPADDING", (3, 0), (3, -1), 2),
        ]
        if has_total:
            style_commands.extend(
                [
                    ("LINEABOVE", (0, -1), (-1, -1), 0.6, LINE),
                    ("BACKGROUND", (0, -1), (-1, -1), SURFACE_SOFT),
                ]
            )
        table.setStyle(TableStyle(style_commands))
        return _section_block("Itens", [table], styles, title_spacing=2 * mm)

    def _build_conditions_section(
        self,
        cabecalho: dict,
        condicoes: dict,
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        validade = cabecalho.get("validade_dias")
        validade_text = "—" if validade in (None, "") else f"{validade} dias"

        entries = [
            ("Condição de pagamento", _display(condicoes.get("descricao"))),
            ("ICMS", _format_icms_display(_display(condicoes.get("icms")))),
            ("IPI", _display(condicoes.get("ipi"))),
            ("Embalagem", _format_embalagem_display(_display(condicoes.get("embalagem")))),
            ("Frete", _format_frete_display(_display(condicoes.get("frete")))),
            ("Validade da proposta", validade_text),
        ]

        rows = [
            [
                Paragraph(f"<font color='#64748B'>{_escape(label)}</font>", styles["conditionLabel"]),
                Paragraph(_escape_multiline(value), styles["conditionValue"]),
            ]
            for label, value in entries
        ]
        for note in FIXED_CONDITION_TEXTS:
            rows.append(
                [
                    Paragraph("", styles["conditionLabel"]),
                    Paragraph(f"<i>{_escape(note)}</i>", styles["conditionNote"]),
                ]
            )

        inner = Table(rows, colWidths=[42 * mm, CONTENT_WIDTH - 42 * mm - 20])
        inner.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        wrapper = Table([[inner]], colWidths=[CONTENT_WIDTH])
        wrapper.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), SURFACE_SOFT),
                    ("BOX", (0, 0), (-1, -1), 0.45, LINE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        title = Paragraph("Condições comerciais", styles["sectionTitle"])
        return [title, Spacer(1, 2 * mm), wrapper]

    def _build_closing_sections(
        self,
        observacoes: str,
        vendedor: dict,
        styles: dict[str, ParagraphStyle],
    ) -> list[Flowable]:
        text = observacoes or "Sem observações registradas."
        obs_body = Paragraph(_escape_multiline(text), styles["observations"])
        obs_wrapper = Table([[obs_body]], colWidths=[CONTENT_WIDTH])
        obs_wrapper.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), SURFACE_SOFT),
                    ("BOX", (0, 0), (-1, -1), 0.45, LINE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        obs_section = [
            Paragraph("Observações", styles["sectionTitle"]),
            Spacer(1, 2 * mm),
            obs_wrapper,
        ]

        signature_block = Table(
            [
                [Paragraph(f"<b>{_escape(_display(vendedor.get('nome')))}</b>", styles["signatureName"])],
                [Paragraph(_escape(_display(vendedor.get("cargo"))), styles["signatureMeta"])],
                [Paragraph(_escape(_display(vendedor.get("telefone"))), styles["signatureMeta"])],
                [Paragraph(_escape(_display(vendedor.get("email"))), styles["signatureMeta"])],
            ],
            colWidths=[CONTENT_WIDTH],
            hAlign="LEFT",
        )
        signature_block.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )

        return [
            *obs_section,
            Spacer(1, 2.5 * mm),
            Paragraph("Atenciosamente,", styles["closingSalutation"]),
            Spacer(1, 2.5 * mm),
            signature_block,
        ]


class _PdfBuffer:
    def __init__(self) -> None:
        self._chunks: list[bytes] = []

    def write(self, data: bytes) -> None:
        self._chunks.append(data)

    def getvalue(self) -> bytes:
        return b"".join(self._chunks)


def _section_block(
    title: str,
    body: list[Flowable],
    styles: dict[str, ParagraphStyle],
    *,
    title_spacing: float = 2.5 * mm,
) -> list[Flowable]:
    return [
        Paragraph(title, styles["sectionTitle"]),
        Spacer(1, title_spacing),
        *body,
    ]


def _format_empresa_lines(empresa: dict) -> str:
    lines = [
        f"<b>{_escape(_display(empresa.get('nome')))}</b>",
        _escape(_display(empresa.get("endereco"))),
    ]
    bairro = _display(empresa.get("bairro"), empty="")
    if bairro and bairro != "—":
        lines.append(_escape(bairro))

    cidade = _display(empresa.get("cidade"), empty="")
    uf = _display(empresa.get("uf"), empty="")
    cep = _display(empresa.get("cep"), empty="")
    city_parts = []
    if cidade and uf:
        city_parts.append(f"{cidade}/{uf}")
    elif cidade or uf:
        city_parts.append(cidade or uf)
    if cep and cep != "—":
        city_parts.append(f"CEP {cep}")
    if city_parts:
        lines.append(_escape(" - ".join(city_parts)))

    meta = " | ".join(
        part
        for part in (
            f"CNPJ {_display(empresa.get('cnpj'))}" if empresa.get("cnpj") else "",
            f"IE {_display(empresa.get('inscricao_estadual'))}" if empresa.get("inscricao_estadual") else "",
            _display(empresa.get("telefone")) if empresa.get("telefone") else "",
            _display(empresa.get("site")) if empresa.get("site") else "",
        )
        if part and part != "—"
    )
    if meta:
        lines.append(_escape(meta))

    return "<br/>".join(lines)


def _table_header_cell(label: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(f"<b>{_escape(label)}</b>", styles["tableHeader"])


def _build_labeled_card(
    title: str,
    fields: list[tuple[str, str]],
    styles: dict[str, ParagraphStyle],
    width: float,
) -> Table:
    rows: list[list[Flowable]] = [[Paragraph(title, styles["cardTitle"])]]
    for label, value in fields:
        rows.append(
            [
                Paragraph(
                    f"<font color='#64748B' size='7'>{_escape(label)}</font><br/>"
                    f"{_escape(value)}",
                    styles["cardValue"],
                )
            ]
        )

    card = Table(rows, colWidths=[width])
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), WHITE),
                ("BOX", (0, 0), (-1, -1), 0.4, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (0, 0), 5),
                ("BOTTOMPADDING", (0, 0), (0, 0), 4),
                ("TOPPADDING", (0, 1), (-1, -1), 2),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
            ]
        )
    )
    return card


def _resolve_logo_path() -> Path | None:
    env_path = (os.getenv("PROPOSTAS_COMERCIAIS_PDF_LOGO_PATH") or "").strip()
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(_DEFAULT_LOGO)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _load_logo_flowable() -> Flowable | None:
    path = _resolve_logo_path()
    if path is None:
        return None
    try:
        from svglib.svglib import svg2rlg

        drawing = svg2rlg(str(path))
        if drawing is None:
            return None

        scale_w = LOGO_MAX_WIDTH / drawing.width
        scale_h = LOGO_MAX_HEIGHT / drawing.height
        scale = min(scale_w, scale_h)
        width = drawing.width * scale
        height = drawing.height * scale
        drawing.width = width
        drawing.height = height
        drawing.scale(scale, scale)
        return _DrawingFlowable(drawing, width, height)
    except Exception:
        return None


def _draw_running_header(page_canvas, detail: dict, *, first_page: bool) -> None:
    if first_page:
        return

    cabecalho = detail.get("cabecalho") or {}
    numero_ov = _display(cabecalho.get("numero_ov"))
    page_canvas.saveState()
    page_canvas.setStrokeColor(LINE)
    page_canvas.setLineWidth(0.35)
    page_canvas.line(MARGIN_LEFT, A4[1] - 11 * mm, A4[0] - MARGIN_RIGHT, A4[1] - 11 * mm)
    page_canvas.setFillColor(DELPI_BLUE)
    page_canvas.setFont("Helvetica-Bold", 8)
    page_canvas.drawString(MARGIN_LEFT, A4[1] - 9 * mm, "DELPI")
    page_canvas.setFillColor(TEXT_MUTED)
    page_canvas.setFont("Helvetica", 7.5)
    page_canvas.drawRightString(
        A4[0] - MARGIN_RIGHT,
        A4[1] - 9 * mm,
        f"Proposta Comercial N° {numero_ov}",
    )
    page_canvas.restoreState()


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "logoFallback": ParagraphStyle(
            "LogoFallback",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=20,
            textColor=DELPI_BLUE,
        ),
        "headerLabel": ParagraphStyle(
            "HeaderLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            alignment=TA_RIGHT,
            textColor=TEXT_MUTED,
        ),
        "headerNumber": ParagraphStyle(
            "HeaderNumber",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=17,
            alignment=TA_RIGHT,
            textColor=DELPI_BLUE,
        ),
        "headerMeta": ParagraphStyle(
            "HeaderMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            alignment=TA_RIGHT,
            textColor=TEXT,
        ),
        "headerCompany": ParagraphStyle(
            "HeaderCompany",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=TEXT,
        ),
        "sectionTitle": ParagraphStyle(
            "SectionTitle",
            parent=base["Heading4"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=DELPI_BLUE,
            spaceAfter=0,
        ),
        "bodyCompact": ParagraphStyle(
            "BodyCompact",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=TEXT,
        ),
        "cardTitle": ParagraphStyle(
            "CardTitle",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=10,
            textColor=DELPI_BLUE,
        ),
        "cardValue": ParagraphStyle(
            "CardValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TEXT,
        ),
        "tableHeader": ParagraphStyle(
            "TableHeader",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=6.8,
            leading=8,
            alignment=TA_CENTER,
            textColor=DELPI_BLUE,
        ),
        "tableCell": ParagraphStyle(
            "TableCell",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=TEXT,
        ),
        "tableCellCenter": ParagraphStyle(
            "TableCellCenter",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=TEXT,
        ),
        "tableCellNcm": ParagraphStyle(
            "TableCellNcm",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=TEXT,
            splitLongWords=0,
        ),
        "tableCellMoney": ParagraphStyle(
            "TableCellMoney",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            alignment=TA_RIGHT,
            textColor=TEXT,
        ),
        "tableCellMoneyBold": ParagraphStyle(
            "TableCellMoneyBold",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=10,
            alignment=TA_RIGHT,
            textColor=TEXT,
        ),
        "conditionLabel": ParagraphStyle(
            "ConditionLabel",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=TEXT_MUTED,
        ),
        "conditionValue": ParagraphStyle(
            "ConditionValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=TEXT,
        ),
        "conditionNote": ParagraphStyle(
            "ConditionNote",
            parent=base["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=TEXT_MUTED,
        ),
        "observations": ParagraphStyle(
            "Observations",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=TEXT,
        ),
        "signatureName": ParagraphStyle(
            "SignatureName",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            alignment=TA_LEFT,
            textColor=TEXT,
        ),
        "signatureMeta": ParagraphStyle(
            "SignatureMeta",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.5,
            alignment=TA_LEFT,
            textColor=TEXT_MUTED,
        ),
        "closingSalutation": ParagraphStyle(
            "ClosingSalutation",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            alignment=TA_LEFT,
            textColor=TEXT,
        ),
    }


def _format_icms_display(value: str) -> str:
    if not value or value == "—":
        return "—"
    if "incluso" in value.lower():
        return value.replace("—", "-").upper()
    if value.endswith("%"):
        return f"{value} - INCLUSO"
    return value


def _format_embalagem_display(value: str) -> str:
    if not value or value == "—":
        return "—"
    lowered = value.lower()
    if "padrao" in lowered or "padrão" in lowered or "inclusa" in lowered or "delpi" in lowered:
        return "INCLUSA"
    return value


def _format_frete_display(value: str) -> str:
    if not value or value == "—":
        return "—"
    normalized = value.replace("—", "-").replace("–", "-")
    upper = normalized.upper()
    if upper.startswith("FOB"):
        return "FOB - por conta do comprador"
    if upper.startswith("CIF"):
        return "CIF - por conta do vendedor"
    return normalized


def _escape(value: str) -> str:
    return escape(value, entities={"\"": "&quot;", "'": "&apos;"})


def _escape_multiline(value: str) -> str:
    return _escape(value).replace("\n", "<br/>")


def _display(value: object, *, empty: str = "—") -> str:
    if value is None:
        return empty
    text = str(value).strip()
    return text or empty
