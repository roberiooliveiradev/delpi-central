"""Amostras de NF-e modelo 55 para testes. Não são documentos fiscais reais."""

from __future__ import annotations

_WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9)


def nfe_access_key(
    *,
    uf: str = "35",
    yymm: str = "2610",
    cnpj: str = "47132675000158",
    model: str = "55",
    series: str = "001",
    number: str = "000085645",
    emission_type: str = "1",
    code: str = "62594974",
) -> str:
    body = f"{uf}{yymm}{cnpj}{model}{series}{number}{emission_type}{code}"
    if len(body) != 43 or not body.isdigit():
        raise ValueError("corpo da chave de teste inválido")
    total = sum(int(digit) * _WEIGHTS[index % 8] for index, digit in enumerate(reversed(body)))
    remainder = total % 11
    check_digit = 0 if remainder < 2 else 11 - remainder
    return body + str(check_digit)


def nfe_xml(
    access_key: str,
    *,
    dh_emi: str = "2026-10-02T10:00:00-03:00",
    model: str = "55",
    series: str = "1",
    number: str | None = None,
    cnpj: str | None = None,
    protocol_key: str | None = None,
    include_protocol: bool = True,
    include_id: bool = True,
    wrapped: bool = True,
) -> bytes:
    document_number = number if number is not None else str(int(access_key[25:34]))
    issuer = cnpj if cnpj is not None else access_key[6:20]
    identifier = f' Id="NFe{access_key}"' if include_id else ""
    protocol = protocol_key if protocol_key is not None else access_key
    note = (
        f"<NFe><infNFe{identifier}>"
        f"<ide><mod>{model}</mod><serie>{series}</serie><nNF>{document_number}</nNF>"
        f"<dhEmi>{dh_emi}</dhEmi></ide>"
        f"<emit><CNPJ>{issuer}</CNPJ></emit>"
        f"</infNFe></NFe>"
    )
    protection = ""
    if include_protocol:
        protection = f"<protNFe><infProt><chNFe>{protocol}</chNFe></infProt></protNFe>"
    if wrapped:
        body = f'<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">{note}{protection}</nfeProc>'
    else:
        body = note
    return f'<?xml version="1.0" encoding="UTF-8"?>{body}'.encode()
