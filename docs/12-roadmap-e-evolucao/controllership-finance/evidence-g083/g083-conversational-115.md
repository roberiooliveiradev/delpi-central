# G083 — Homologação conversacional 115 perguntas

**Status: TEST_NOT_RUN.** O canal oficial da CLARA (host ChatGPT com MCP autenticado) não está acessível neste ambiente de execução; nenhuma resposta foi simulada, mockada ou produzida por endpoint alternativo — conforme §6.2/§6.4.

## Dependência externa exata

Homologação das 105 golden + 10 negativas exige sessão ChatGPT com o conector CLARA produtivo autenticado (`delpi-controllership-finance-api` MCP, OAuth Keycloak do usuário). A camada MCP (`knowledge`/`read`/`analyze`) está operacional; a camada de resposta em linguagem natural vive exclusivamente no host externo.

## Protocolo executável (doc 152 §14.6)

Para cada uma das 115 perguntas registrar: identificador, pergunta exata, competência/filial/filtros, resposta integral, tools chamadas, fontes usadas, afirmações operacionais, confronto com autoridade, resultado PASS/FAIL/INCONCLUSIVE, evidência, correção. Perguntas: `controllership-finance-api/tests/clara_golden_set_r01_r15.py` (`GOLDEN_SET` 105, `NEGATIVE_SET` 10) — expectativa de recuperação documentada no golden test PG (101 PASS + 4 MISS esperados).

## Pré-condições já cumpridas neste gate

Corpus produtivo republicado com zero afirmação superada nos padrões conhecidos; retrieval e contexto verificados por teste e smoke.
