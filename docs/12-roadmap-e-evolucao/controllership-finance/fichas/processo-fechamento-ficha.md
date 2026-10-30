# PROC-0072 — Ficha do processo de fechamento mensal

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4 (GATE E —
conhecimento operacional consolidado; autoridade canônica = doc 118).

## Identificação

- Processo: **PROC-0072 — Gestão do Fechamento Mensal da
  Controladoria** — `APPROVED_RULE` (doc 118 base canônica).
- Produto: Central de Fechamento — Portal Controladoria & Finanças.
- Competência: `YYYY-MM` — dimensão de dado; consulta não exige
  abertura formal.
- Filial: `01` (Matriz) e `02` — dimensão de dado, **não** fronteira
  de permission (ver §Segurança).

## Modelo operacional (doc 118 §2)

Etapas funcionais: **P1** cockpit da competência · **P2** checklist
documental e evidências · **P3** estoque, cutoff e conciliação ·
**P4** classificações e pendências · **P5** pacote, finalização e
envio à DRE · **P6** administração.

Conceitos que a CLARA distingue:

- **Competência consultada × competência aberta**: consultar um mês
  não o abre — meses sem abertura formal mostram explicação + ação
  autorizada (Help `monthlyClosing`).
- **Dados × documentos**: dados = consultas governadas aos relatórios;
  documentos = evidências anexadas/enviadas (doc 91/113/115 — trilha
  de entrega à DRE, vigência e validação documental).
- **Critério de pendência**: pendência = item sem evidência validada
  ou sem critério de conclusão atendido — estado lido das pendências
  governadas, nunca deduzido.

## Capacidades do Portal × o que a CLARA pode fazer

| Capacidade | Superfície | CLARA |
|---|---|---|
| Consultar competência/relatórios | views `closing/*` | `read`/`analyze` com identidade delegada |
| Comparar relatórios | — (sem tela genérica) | `analyze(report_comparison)` |
| Pendências/tarefas | `closing/pendencies`, `closing/my-tasks` | `read`/`analyze` conforme contrato |
| Documentos e envio à DRE | `closing/documents`, pacotes P5 | `read`/orientação; upload = ação humana autorizada |
| Explicar regras e relatórios | Help + estas fichas | `knowledge` com citação |
| Executar/atualizar | execute/delete governados | somente contratos existentes, effective permission, aval por risco (doc 124) |
| Tela de comparação, export comparativo | **não existe** | não prometer |
| Ação no TOTVS | fora do Portal | **nunca** — a CLARA orienta onde conferir |

**Princípio**: conhecer ≠ consultar ≠ executar. A CLARA **explica**
qualquer funcionalidade com fonte governada; **consulta** só o que tem
contrato + autorização + implementação; **executa** só contratos
governados com permissão efetiva e confirmação por risco.

## Fluxo Controladoria → DRE (docs 91/113/115)

Documentos entram como evidência na competência (P2) → pacote (P5) →
envio à DRE → validação documental pela DRE → download autorizado
(`controllership-finance.access.dre` somente para documentos
disponibilizados — sem dados internos). Responsabilidades:
Controladoria produz evidência e valida fechamento; DRE recebe,
confere e homologa o pacote.

## Permissões e segurança

- `controllership-finance.access` — consultas internas autorizadas.
- `controllership-finance.manage` — administração compatível.
- `controllership-finance.access.dre` — somente documentos DRE
  disponibilizados.
- Sem permission por relatório/filial/comparação — `PROVEN` (doc 126).
- Effective permission do Core é autoridade — JWT nunca decide;
  fail-closed por sujeito em toda leitura/análise.
- Branch (`filial`) = filtro de dado, não fronteira RBAC.

## O que permanece humano/ERP (doc 118 §13)

- Emissão oficial de relatórios (MATR910/460/320/989, FINR190).
- Recálculos e virada (MATA320/300/330/280), reabertura de estoque.
- Classificação Direto/Ind/Adm (E10a), decisão sobre NF a
  desconsiderar (E11a/E11b), aceite/homologação (G6).

## Governança

- Evidências: docs 91/112/113/115/116/117/118/119/120/121/124/126.
- Vocabulary canônico (doc 118 §10): P7, H02, E/S, sacramentação,
  poder3, loc99, TES vs CFOP, MOD, OP, EDAPP, competência.
- Resposta factual exige `FACT | POSSIBLE_DIVERGENCE | RECOMMENDATION |
  INSUFFICIENT_EVIDENCE` — nunca causa inventada, nunca "zero" para
  dado ausente, nunca TARGET afirmado como comportamento em produção.
