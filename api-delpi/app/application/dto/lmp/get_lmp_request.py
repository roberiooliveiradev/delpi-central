# app/application/dto/lmp/get_lmp_request.py
from dataclasses import dataclass


@dataclass
class GetLMPRequest:
    sale_number: str