# app/models/cliente_model.py
from pydantic import BaseModel

class Cliente(BaseModel):
    codigo: str
    nome: str
    uf: str
    cnpj: str
