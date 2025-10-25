import re

CPF_RE   = re.compile(r"^\d{3}\.?\d{3}\.?\d{3}-?\d{2}$")
CNPJ_RE  = re.compile(r"^\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}$")
DATE_RE  = re.compile(r"^\d{2}/\d{2}/\d{4}$")
UF_RE    = re.compile(r"^[A-Za-z]{2}$")
CEP_RE   = re.compile(r"^\d{5}-?\d{3}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?\d{10,15}$")

def is_cpf(v: str) -> bool: return bool(CPF_RE.match((v or "").strip()))
def is_cnpj(v: str) -> bool: return bool(CNPJ_RE.match((v or "").strip()))
def is_date_br(v: str) -> bool: return bool(DATE_RE.match((v or "").strip()))
def is_uf(v: str) -> bool: return bool(UF_RE.match((v or "").strip()))
def is_cep(v: str) -> bool: return bool(CEP_RE.match((v or "").strip()))
def is_email(v: str) -> bool: return bool(EMAIL_RE.match((v or "").strip()))
def is_phone(v: str) -> bool: return bool(PHONE_RE.match((v or "").strip()))

def guess_validator(field_name: str):
    f = (field_name or "").upper()
    if "CPF" in f: return is_cpf, "CPF no formato 999.999.999-99"
    if "CNPJ" in f: return is_cnpj, "CNPJ no formato 99.999.999/9999-99"
    if "DATA" in f or "NASC" in f: return is_date_br, "Data no formato dd/mm/aaaa"
    if f.endswith("UF") or f == "UF": return is_uf, "UF com 2 letras (ex.: SP)"
    if "CEP" in f: return is_cep, "CEP no formato 99999-999"
    if "EMAIL" in f: return is_email, "e-mail válido"
    if "TELEFONE" in f or "CELULAR" in f or "WHATS" in f: return is_phone, "telefone (+5511999999999)"
    return (lambda _v: True), None
