# Gate 053 — Auditoria vídeo: relatórios × rotinas TOTVS (2026-11-02)

## Acessibilidade do vídeo

- Arquivo presente: `Downloads/fechamento/Acompanhamento...mp4` (126 MB, íntegro em disco).
- Revisão visual: **TEST_NOT_RUN** — o executor não tem capacidade de
  reprodução/análise de vídeo. Nenhuma afirmação abaixo deriva da
  gravação — deriva dos artefatos, fichas e código no HEAD.
- `NOT_OBSERVED_IN_VIDEO` para todas as rotinas: não afirmar ausência
  de R04/MATR860 — apenas que não foi verificável nesta execução.

## Matriz R01–R15 — evidência documental + código (não-vídeo)

| ID | Rotina candidata | Artefato confirmado | Categoria* | Implementação | Ação TARGET |
|---|---|---|---|---|---|
| R03 | MATR460 | arquivo P7 | A REPORT_OUTPUT | parcial/cadastro | COMPLETE_EXISTING |
| R05 | MATR320 | Entradas e saidas.pdf | A | implementado | homologar |
| R06 | MATR910 | cpv 09 26 matriz.xlsb | C — separar cálculo de consulta | Kardex/CPV endpoint | REUSE+COMPLETE |
| R07 | MATR910 | Invent.xlsb | A (`D3_DOC=INVENT` candidato) | parcial | COMPLETE por contrato |
| R08 | MATR989 | Material em processo.xlsb | A | implementado | homologar |
| R09 | DLP204 | Fat x MOD.xlsb | A | OPERATIONAL_IMPLEMENTATION_COMPLETE | fechado |
| R10/R11 | EDAPP | exportações | A | implementado | homologar |
| R12 | MATA320/300/330 | — | B ERP_OPERATION | estado consultável | KEEP_IN_TOTVS + STATUS_ONLY |
| R15 | MATA330/280 | — | B + E PROCESS_STATUS | corte/virada estado | STATUS_ONLY |
| R13 | — | bancos externos | D DOCUMENT_EVIDENCE | fluxo P2/P5 | DOCUMENT_FLOW |
| R14 | — | importação externa | D | fluxo P2/P5 | DOCUMENT_FLOW |
| R04 | MATR860 candidata | NENHUM artefato | F INCONCLUSIVE | nenhum | DECISION_REQUIRED |

*Categorias classificatórias G053 — não são permissões/tipos aprovados.

## R04 — bloco de evidência

- MATR860 no vídeo: `NOT_OBSERVED_IN_VIDEO` (revisão visual pendente).
- Artefato oficial: NENHUM no pacote — sem layout, colunas ou grão.
- Fonte candidata SD3 (`D3_OP`/movimentos): `TO_INVENTORY`, não provada.
- R08 compartilha SD3 mas não é equivalente (semântica diferente).
- Owner funcional: não confirmado.
- Ação: `DECISION_REQUIRED` — artefato oficial R04 + owner antes de
  qualquer implementação. `SEARCH_MISS != ABSENCE`.

## Separação operação × informação (premissa aprovada)

Operacional continua no TOTVS (cálculo custos, fechamento, virada):
R12/R15 = `B ERP_OPERATION` / `E PROCESS_STATUS` — Portal apenas
consulta estado, nunca executa comandos ERP. Saídas informacionais (A)
são candidatas ao Portal por fonte/contrato comprovados.

## Bloqueios/owners

- R04: artefato oficial + owner funcional — Controladoria.
- Revisão visual do vídeo: executor humano com reprodução — qualquer
  classificação acima fica sujeita à revisão do vídeo.

## Veredito

`INCONCLUSIVE` para a meta principal (auditoria do vídeo) — sem
capacidade de reprodução no executor; classificação documental
entregue como baseline a confirmar pela observação visual.
