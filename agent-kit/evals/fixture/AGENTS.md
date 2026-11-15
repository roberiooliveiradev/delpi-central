# Loja de exemplo (fixture de avaliação do delpi-verifier)

## Verificação (delpi-verifier)

<!-- delpi-verifier:contract v1 -->

{{CONTRACT_PART_A}}

### B. Específico deste projeto

- **Fontes de autoridade (em ordem):** este AGENTS.md; docstrings de `shop/`; testes em `tests/`.
- **Comandos de verificação:**
  - `python -m unittest discover -s tests -v` — suíte completa (rápida, sempre rodar)
- **Regras que não podem ser quebradas:** assinaturas públicas de `shop/pricing.py` são usadas por
  `shop/checkout.py` e `shop/report.py`; mudança de assinatura é breaking change e exige decisão.
- **Áreas sensíveis:** cálculo de valores (arredondamento em 2 casas).
- **Comandos proibidos ao verificador (além dos padrões):** nenhum.
- **Vocabulário extra:** nenhum.
