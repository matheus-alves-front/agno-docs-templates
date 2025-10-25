import re
from typing import Callable, Tuple

CPF_RE = re.compile(r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$")
CNPJ_RE = re.compile(r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$")
DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
UF_RE = re.compile(r"^[A-Za-z]{2}$")
CEP_RE = re.compile(r"^\d{5}-?\d{3}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")


def is_cpf(value: str) -> bool:
    return bool(CPF_RE.match((value or "").strip()))


def is_cnpj(value: str) -> bool:
    return bool(CNPJ_RE.match((value or "").strip()))


def is_date_br(value: str) -> bool:
    return bool(DATE_RE.match((value or "").strip()))


def is_uf(value: str) -> bool:
    return bool(UF_RE.match((value or "").strip()))


def is_cep(value: str) -> bool:
    return bool(CEP_RE.match((value or "").strip()))


def is_email(value: str) -> bool:
    return bool(EMAIL_RE.match((value or "").strip()))


def is_phone(value: str) -> bool:
    return bool(PHONE_RE.match((value or "").strip()))


def guess_validator(field_name: str) -> Tuple[Callable[[str], bool], str | None, str | None]:
    field = (field_name or "").upper()
    if "CPF" in field:
        return is_cpf, "CPF no formato 999.999.999-99", "cpf"
    if "CNPJ" in field:
        return is_cnpj, "CNPJ no formato 99.999.999/9999-99", "cnpj"
    if "DATA" in field or "NASC" in field:
        return is_date_br, "Data no formato dd/mm/aaaa", "data"
    if field.endswith("UF") or field == "UF":
        return is_uf, "UF com 2 letras (ex.: SP)", "uf"
    if "CEP" in field:
        return is_cep, "CEP no formato 99999-999", "cep"
    if "EMAIL" in field:
        return is_email, "e-mail válido", "email"
    if "TELEFONE" in field or "CELULAR" in field or "WHATS" in field:
        return is_phone, "telefone (+5511999999999)", "telefone"
    return (lambda _value: True), None, None
