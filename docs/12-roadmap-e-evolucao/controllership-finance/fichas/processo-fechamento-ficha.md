# PROC-0072 — Ficha do processo de fechamento mensal

Versão da ficha: 1.1 · 09/11/2026 · doc 127 Etapa 4 (GATE E) +
glossário de destinatários aprovado pelo PO (doc 156).

Autoridade canônica do processo: doc 118. Vocabulário de
responsabilidades e destinatários: doc 156 (`APPROVED_RULE`,
commit `be75e5048cbaf600bfc131424d7aa0f965767565`).

## Identificação

- Processo: **PROC-0072 — Gestão do Fechamento Mensal da
  Controladoria** — `APPROVED_RULE` (doc 118 base canônica).
- Responsável pelo fechamento mensal da DELPI: **Controladoria
  interna** — prepara, analisa, confere e encaminha as evidências.
- Produto: Central de Fechamento — Portal Controladoria & Finanças.
- Competência: `YYYY-MM` — dimensão de dado; consulta não exige
  abertura formal.
- Filial: `01` (Matriz) e `02` — dimensão de dado, **não** fronteira
  de permission (ver §Segurança).

## Glossário funcional (doc 156 — não misturar dimensões)

| Termo | Definição operacional | Não confundir com |
|---|---|---|
| **Controladoria interna** | Prepara, analisa, confere e encaminha as evidências do fechamento. | Destinatário documental |
| **Financeiro** | Origem dos relatórios financeiros do Módulo 06; envio **consolidado filiais 01+02**. | Destinatário ou permission |
| **Estoque/Custos** | Origem dos relatórios do Módulo 04; P7/resumo **individual por filial 01 e 02**. | Permission code |
| **Contabilidade externa** | Destinatária dos documentos para tratamento contábil. | Controladoria interna |
| **Fiscal** | Destinatário exclusivo de entregas fiscais específicas. | Natureza fiscal do documento |
| **DRE** | Demonstração do Resultado do Exercício; no Portal, também apelido do público externo consumidor dos documentos. | Departamento formal obrigatório, módulo ERP ou `recipient_area` |
| **`recipient_area=CONTABIL`** | Classificação documental dos 14 itens atuais do rascunho V2. | Identidade da pessoa ou acesso irrestrito |
| **`controllership-finance.access.dre`** | Permissão de acesso à experiência documental DRE. | Área destinatária; **não** autoriza qualquer documento |

Regras de distinção que a CLARA deve preservar:

1. Quem **prepara** = Controladoria interna; quem **recebe** = Contabilidade externa (público operacionalmente chamado “DRE”).
2. Financeiro ≠ Controladoria: Financeiro é origem dos relatórios financeiros; Controladoria é a responsável funcional do fechamento.
3. Contabilidade externa ≠ Fiscal: `FISCAL` só para entregas fiscais específicas confirmadas; natureza fiscal do documento **não** implica `recipient_area=FISCAL`.
4. Os 14 itens atuais usam `recipient_area=CONTABIL` porque o destinatário funcional aprovado é a Contabilidade externa — não porque a permissão DRE conceda acesso.
5. Relatórios financeiros de envio são consolidados (01+02); o P7 deve ser entregue **por filial**, não consolidado.

## Modelo operacional (doc 118 §2)

Etapas funcionais: **P1** cockpit da competência · **P2** checklist
documental e evidências · **P3** estoque, cutoff e conciliação ·
**P4** classificações e pendências · **P5** pacote, finalização e
envio à Contabilidade externa (público DRE) · **P6** administração.

Conceitos que a CLARA distingue:

- **Competência consultada × competência aberta**: consultar um mês
  não o abre — meses sem abertura formal mostram explicação + ação
  autorizada (Help `monthlyClosing`).
- **Dados × documentos**: dados = consultas governadas aos relatórios;
  documentos = evidências anexadas/enviadas (doc 91/113/115/156 —
  trilha de entrega à Contabilidade externa, vigência e validação).
- **Critério de pendência**: pendência = item sem evidência validada
  ou sem critério de conclusão atendido — estado lido das pendências
  governadas, nunca deduzido.
- **Área organizacional × origem de relatório × destinatário ×
  permissão**: dimensões distintas (doc 156) — nunca equiparar.

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

## Fluxo Controladoria → Contabilidade externa (docs 91/113/115/156)

Documentos entram como evidência na competência (P2) → pacote (P5) com
`recipient_area=CONTABIL` → envio à Contabilidade externa (público
operacionalmente chamado “DRE”) → validação documental pelo
destinatário → download autorizado. Responsabilidades: Controladoria
interna prepara/valida e encaminha; Contabilidade externa recebe e
trata. `FISCAL` permanece reservado a entregas fiscais específicas.

Acesso efetivo **não** nasce só do cadastro da área: exige
`controllership-finance.access.dre` + vínculo `RECIPIENT` válido na
área/pacote + versão `SUBMITTED` contendo a evidência — fail-closed.
A permissão DRE **não** permite consultar qualquer documento.

## Permissões e segurança

- `controllership-finance.access` — consultas internas autorizadas.
- `controllership-finance.manage` — administração compatível.
- `controllership-finance.access.dre` — capability da experiência
  documental DRE; **não** é `recipient_area` e **não** concede acesso
  irrestrito.
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

- Evidências: docs 91/112/113/115/116/117/118/119/120/121/124/126/156.
- Vocabulary canônico (doc 118 §10): P7, H02, E/S, sacramentação,
  poder3, loc99, TES vs CFOP, MOD, OP, EDAPP, competência.
- Glossário de destinatários: doc 156 (PO 2026-11-09).
- Resposta factual exige `FACT | POSSIBLE_DIVERGENCE | RECOMMENDATION |
  INSUFFICIENT_EVIDENCE` — nunca causa inventada, nunca "zero" para
  dado ausente, nunca TARGET afirmado como comportamento em produção.
