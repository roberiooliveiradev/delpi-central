# Fase 0 — Validação SQL (Apontamento de Produção)

> Gerado em: `2026-07-15`  
> Fonte: `SH6010` → `SH1010` → `SHB010` (sem view fabril)  
> Script: `api-delpi/scripts/sql/production_appointments_fase0_probe.py`  
> Status: **Pronto para Fase 1 (rotas api-delpi)**

Período probe: `20260615` ≤ `H6_DTAPONT` < `20260716` (últimos ~30 dias).  
Execução: `docker exec` + pyodbc no container `delpi-api-delpi` (API HTTP estava unhealthy — `postgres-plugins`; TOTVS OK).

Artefatos JSON: [fase0-results-sc.json](./fase0-results-sc.json), [fase0-results-es.json](./fase0-results-es.json).

---

## Checklist

| # | Probe | SC (`01`) | ES (`02`) | Latência (ms) |
|---|-------|-----------|-----------|---------------|
| 1 | Catálogo CTs (`SHB010`) | 84 CTs | 60 CTs | ~3–10 |
| 2 | CTs inspeção final (`%INSPE%FINAL%`) | CT-70 | CT-99 (cadastro; lista global 2) | ~5–18 |
| 3 | Amostra apontamentos + joins | 20 linhas OK | — | ~231 |
| 4 | Summary por CT (inclui inspeção) | 24 CTs; **CT-70 #1** | 28 CTs; CT-00 #1 volume | ~180–190 |
| 5 | Série temporal por dia | 23 dias | 31 dias | ~160–200 |
| 6 | Drill-down por OP | 30 OPs OK | — | ~184 |
| 7 | Filtro um CT (`CT-70`) | 702 apont. / 144,89 qtd | — | ~16 |
| 8 | SH6 sem vínculo CT | **0** | **3** | ~105–117 |
| 9 | Qtd no CT inspeção (PA/PI) | CT-70 = 144,89 / 702 | — | ~37 |

**Resultado:** go para rotas. Queries analíticas com `NOLOCK` + bind; período 30 dias por filial fica **&lt; 250 ms** — adequado para MFE; cache só se polling agressivo ou períodos longos.

---

## Achados importantes

1. **Modelo confirmado:** `H6_RECURSO` → `SH1.H1_CTRAB` → `SHB.HB_COD` funciona; amostra de 15/07 traz PA/PI em vários CTs, inclusive CT-70.
2. **CT inspeção nos totais:** na SC, CT-70 (`INSPEÇÃO FINAL`) lidera quantidade produzida no período — o plugin **não** deve excluí-lo (diferente da eficiência-fabril).
3. **Metadado inspeção:** SC = `CT-70`, ES = `CT-99` — descoberta por nome, sem hardcode.
4. **Unidade:** `H6_QTDPROD` vem em escala Protheus (valores fracionários típicos de milheiro) — UI deve exibir o número como na SH6; conversão para unidade só se regra de negócio existir depois.
5. **Cadastro sujo:** há código `CT- 53` (espaço) no catalog SC — API deve `RTRIM` em códigos/nomes.
6. **Orfãos:** ES com 3 apontamentos sem CT no período — listagem com `INNER JOIN` SH1/SHB os omite; summary pode expor `appointments_missing_ct_link` se quisermos completude (opcional Fase 1).
7. **ES / CT-00:** alto volume em `CT-00` (`MONTAGEM - REVISAR`) — incluir nos totais; filtro por CT no UI cobre quem quiser excluir manualmente.

---

## Como reproduzir

```bash
docker cp api-delpi/scripts/sql/production_appointments_fase0_probe.py \
  delpi-api-delpi:/tmp/production_appointments_fase0_probe.py

docker exec -e PROBE_BRANCH=01 -e PROBE_JSON_OUT=/tmp/pa_fase0.json \
  delpi-api-delpi python /tmp/production_appointments_fase0_probe.py

docker exec -e PROBE_BRANCH=02 -e PROBE_JSON_OUT=/tmp/pa_fase0_es.json \
  delpi-api-delpi python /tmp/production_appointments_fase0_probe.py
```

Quando a API HTTP estiver saudável, o mesmo SQL pode ser validado via `POST /data/sql` (tabelas já na whitelist: `SH6010`, `SH1010`, `SHB010`, `SB1010`).

---

## Próximo passo (Fase 1)

Implementar rotas em `/production/appointments/*` conforme [ESPECIFICACAO.md](./ESPECIFICACAO.md), SQL em `totvs/`, envelope `api_delpi_success`, RBAC filial, testes SQL + smoke meta. **Chat só no final.**
