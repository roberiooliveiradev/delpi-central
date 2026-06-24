# Evidências — reconciliação estoque Suprimentos

**Gerado em:** 2026-06-24T18:36:34.868076Z  
**Período:** 2026-05-01 a 2026-05-31

Referência: [playbook-correcao-estoque-supplies-inventario.md](../playbook-correcao-estoque-supplies-inventario.md)

## Resumo por filial

| Filial | API estimada | SQL estimada | SB9 em end_date | SB9 ≤ end_date | SB2 atual | Ref. EM ESTOQUE | Ref. TOTAL GERAL |
|--------|-------------|-------------|-----------------|----------------|-----------|-----------------|------------------|
| 01 Matriz | R$ 281.491,39 | R$ 281.491,39 | — | R$ 3.474.907,58 | R$ 3.554.743,73 | R$ 3.598.312,40 | R$ 3.862.102,97 |
| 02 UES | R$ 4.911.291,59 | R$ 4.911.291,59 | — | R$ 9.635.115,44 | R$ 10.162.314,04 | R$ 9.737.043,62 | R$ 10.048.509,51 |

## Breakdown SQL (estimativa API)

### Filial 01 — Matriz

- Base SB9 (`closing_base_date`): **20260228** → R$ 3.474.907,58
- Ponte SD3: R$ -1.756.147,25
- Período SD3: R$ -1.437.268,93
- **Total estimado:** R$ 281.491,39

- Sem fechamento SB9 na data exata end_date — estimativa SB9+SD3 é esperada; validar closing_base_date e ponte SD3.
- Estimativa API < 50% do EM ESTOQUE oficial — gap estrutural (ponte/período SD3 ou base SB9 antiga).

### Filial 02 — UES

- Base SB9 (`closing_base_date`): **20260228** → R$ 9.635.115,44
- Ponte SD3: R$ -3.090.429,49
- Período SD3: R$ -1.633.394,37
- **Total estimado:** R$ 4.911.291,59

- Sem fechamento SB9 na data exata end_date — estimativa SB9+SD3 é esperada; validar closing_base_date e ponte SD3.

## Conclusões W0

- **Não há registros SB9010 com `B9_DATA = end_date`** — o Registro de Inventário não está refletido como fechamento SB9 nessa data no banco consultado.
- Filial **01**: último fechamento SB9 usado pela API é **20260228**; ponte SD3 R$ -1.756.147,25 + período R$ -1.437.268,93 → estimativa R$ 281.491,39 vs EM ESTOQUE ref. R$ 3.598.312,40.
- Filial **01**: **SB2 atual** (R$ 3.554.743,73) está próximo do EM ESTOQUE do print — saldo corrente é melhor referência que SB9+SD3 neste cenário.
- Filial **02**: último fechamento SB9 usado pela API é **20260228**; ponte SD3 R$ -3.090.429,49 + período R$ -1.633.394,37 → estimativa R$ 4.911.291,59 vs EM ESTOQUE ref. R$ 9.737.043,62.
- Filial **02**: **SB2 atual** (R$ 10.162.314,04) está próximo do EM ESTOQUE do print — saldo corrente é melhor referência que SB9+SD3 neste cenário.
- **API e SQL de reconciliação coincidem** — o gap é de regra/dados TOTVS, não bug de implementação.

## Próximo passo (playbook)

SB9010 sem fechamento após fev/2026 — estimativa SD3 não confiável para maio. Escalar Controladoria (fechamentos SB9 mar–mai) antes de W2; avaliar fallback SB2 ou MAX(B9_DATA)<=end_date quando inventário oficial existir sem SB9 na data.

## Checklist W0

- [ ] Confirmar fechamento SB9 na `end_date` por filial
- [ ] Comparar SB9 end_date com EM ESTOQUE do Registro
- [ ] Comparar API com SQL (deve coincidir)
- [ ] Registrar decisão D1–D4 com Suprimentos
