from __future__ import annotations

PIX_KEY_TYPES = frozenset({"cpf", "cnpj", "email", "phone", "random"})

PIX_KEY_TYPE_LABELS = {
    "cpf": "CPF",
    "cnpj": "CNPJ",
    "email": "E-mail",
    "phone": "Telefone",
    "random": "Chave aleatória",
}


def normalize_pix_key(key_type: str | None, key_value: str | None) -> tuple[str | None, str | None]:
    type_norm = str(key_type or "").strip().lower()
    value_norm = str(key_value or "").strip()
    if not type_norm and not value_norm:
        return None, None
    if not type_norm or not value_norm:
        raise ValueError("Informe o tipo e a chave PIX.")
    if type_norm not in PIX_KEY_TYPES:
        raise ValueError("Tipo de chave PIX inválido.")
    return type_norm, value_norm
