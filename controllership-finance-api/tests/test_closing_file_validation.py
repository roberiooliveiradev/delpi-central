"""Validação defensiva de arquivos — três camadas (doc 103 §D, D-U2=A).

Assinatura + estrutura + MIME/extensão convergentes. XLSX não é qualquer
ZIP; XLS exige CFB; PDF truncado é rejeitado; CSV não basta por extensão;
ZIP renomeado, poliglota e conteúdo truncado são casos negativos tipados.
"""

from __future__ import annotations

import io
import zipfile

import pytest

from controllership_finance_app.domain.closing_checklist import errors as de
from controllership_finance_app.domain.closing_documents.file_validation import (
    MAX_FILE_BYTES,
    sanitize_original_name,
    validate_upload_content,
)


def _pdf() -> bytes:
    return b"%PDF-1.4\nbody " + b"x" * 2048 + b"\n%%EOF\n"


def _png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 32 + b"IEND\xaeB`\x82"


def _jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"


def _webp() -> bytes:
    return b"RIFF" + b"\x24\x00\x00\x00" + b"WEBP" + b"\x00" * 32


def _xls() -> bytes:
    return b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 512


def _xlsx() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("xl/workbook.xml", "<workbook/>")
        zf.writestr("xl/worksheets/sheet1.xml", "<worksheet/>")
    return buf.getvalue()


def _csv() -> bytes:
    return "data;valor\n2026-05-31;1000,00\n".encode("utf-8")


@pytest.mark.parametrize(
    "name,mime,payload,expected_mime",
    [
        ("extrato.pdf", "application/pdf", _pdf(), "application/pdf"),
        ("foto.jpg", "image/jpeg", _jpeg(), "image/jpeg"),
        ("foto.jpeg", "image/jpeg", _jpeg(), "image/jpeg"),
        ("recibo.png", "image/png", _png(), "image/png"),
        ("img.webp", "image/webp", _webp(), "image/webp"),
        ("planilha.xls", "application/vnd.ms-excel", _xls(),
         "application/vnd.ms-excel"),
        ("planilha.xlsx",
         "application/vnd.openxmlformats-officedocument"
         ".spreadsheetml.sheet",
         _xlsx(),
         "application/vnd.openxmlformats-officedocument"
         ".spreadsheetml.sheet"),
        ("dados.csv", "text/csv", _csv(), "text/csv"),
    ],
)
def test_valid_files_accepted(name, mime, payload, expected_mime):
    ext, canonical = validate_upload_content(
        original_name=name, declared_mime=mime, content=payload
    )
    assert canonical == expected_mime


def test_empty_file_rejected():
    with pytest.raises(de.EmptyFile):
        validate_upload_content(
            original_name="a.pdf", declared_mime="application/pdf", content=b""
        )


def test_oversize_rejected():
    with pytest.raises(de.FileTooLarge):
        validate_upload_content(
            original_name="a.pdf",
            declared_mime="application/pdf",
            content=b"x" * (MAX_FILE_BYTES + 1),
        )


def test_disallowed_extension_rejected():
    for name in ("extrato.ofx", "dados.qif", "nota.txt", "app.exe", "doc.docx"):
        with pytest.raises(de.UnsupportedMediaType):
            validate_upload_content(
                original_name=name,
                declared_mime="application/octet-stream",
                content=b"qualquer conteudo de texto",
            )


def test_zip_renamed_to_xlsx_rejected():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("payload.bin", b"\x00" * 64)
    with pytest.raises(de.InvalidFileContent):
        validate_upload_content(
            original_name="planilha.xlsx",
            declared_mime=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            content=buf.getvalue(),
        )


def test_truncated_pdf_rejected():
    with pytest.raises(de.InvalidFileContent):
        validate_upload_content(
            original_name="extrato.pdf",
            declared_mime="application/pdf",
            content=b"%PDF-1.4\n" + b"x" * 2048,  # sem %%EOF
        )


def test_extension_content_mismatch_rejected():
    with pytest.raises(de.ContentTypeMismatch):
        validate_upload_content(
            original_name="foto.png",
            declared_mime="image/png",
            content=_pdf(),
        )


def test_csv_carrying_binary_signature_rejected():
    with pytest.raises(de.ContentTypeMismatch):
        validate_upload_content(
            original_name="dados.csv",
            declared_mime="text/csv",
            content=_xlsx(),
        )


def test_csv_with_nul_rejected():
    with pytest.raises((de.ContentTypeMismatch, de.InvalidFileContent)):
        validate_upload_content(
            original_name="dados.csv",
            declared_mime="text/csv",
            content=b"a,b\x00\x00\x00binary",
        )


def test_declared_mime_divergence_rejected():
    with pytest.raises(de.ContentTypeMismatch):
        validate_upload_content(
            original_name="extrato.pdf",
            declared_mime="image/png",
            content=_pdf(),
        )


def test_truncated_xlsx_rejected():
    with pytest.raises(de.InvalidFileContent):
        validate_upload_content(
            original_name="planilha.xlsx",
            declared_mime=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            content=_xlsx()[:20],
        )


def test_zip_bomb_manifest_rejected():
    """ZIP com tamanho descompactado declarado abusivo não passa por
    planilha — a guarda de metadados bloqueia sem descomprimir."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "<Types/>")
        zf.writestr("xl/workbook.xml", "<workbook/>")
        for i in range(40):
            zf.writestr(f"big{i}.xml", b"y" * (8 * 1024 * 1024))
    with pytest.raises(de.InvalidFileContent):
        validate_upload_content(
            original_name="planilha.xlsx",
            declared_mime="application/zip",
            content=buf.getvalue(),
        )


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("../../etc/passwd", "passwd"),
        ("..\\windows\\system.ini", "system.ini"),
        ("relatório junho.pdf", "relat_rio_junho.pdf"),
        ("a/b/c/../d.pdf", "d.pdf"),
        ("nome\x00oculto.pdf", "nome_oculto.pdf"),
    ],
)
def test_sanitize_original_name(raw, expected):
    assert sanitize_original_name(raw) == expected
