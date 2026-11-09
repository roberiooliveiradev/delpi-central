# R13 — Extratos e aplicações

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.


## Identificação

- Código/nome: **R13 — Extratos bancários e aplicações** (evidências
  financeiras externas do pacote de fechamento).
- Finalidade: compor o pacote documental enviado à Contabilidade
  externa (público operacionalmente chamado “DRE”) — extratos,
  aplicações (XP, BB) e comprovantes.
- Processo: PROC-0072 — `PROVEN` no checklist de entregáveis
  (doc 85 §12; doc 118 §6; doc 156).
- Owner funcional: Controladoria interna (coleta); Contabilidade
  externa (consumo documental — doc 156).
- Owner técnico: nenhum — **fonte fora do Protheus**.
- Implementação: **`SOURCE_UNAVAILABLE` — `BLOQUEADO`**; entrega via
  upload documental P2 (`TARGET`).
- Homologação: G1 `PASS`; demais `PENDING`.

## Fonte e dados

- Fonte: **externa** (bancos, corretoras XP/BB) — não há tabela
  Protheus; regra de coleta = contrato de entrada externo, não SQL.
- Trilha de evidência: anexo/upload na competência (P2 documental) —
  `TARGET`.
- Capability CLARA: **nenhuma** de dados; a CLARA explica o papel do
  item no pacote e orienta o fluxo de documentos.

## Regras de negócio

- Nenhuma regra de seleção registrável — `TO_INVENTORY`
  (doc 85 §12 `BLOQUEADO`).

## Interpretação

- A CLARA **não consulta** extratos — orienta sobre entrega,
  pendências e validação documental (fluxo P2/113).
- Qualquer pergunta sobre valores de extrato exige o documento anexado
  ou a fonte externa — `INSUFFICIENT_EVIDENCE` honesto.

## Operação

- Documentos recebidos pela Controladoria interna → envio à
  Contabilidade externa (doc 91/113/115/156 — gestão documental, não
  dado consultável).
- Comparações: `NOT_COMPARABLE` — evidência externa sem medida numérica.

## Governança

- Evidências: doc 85 §12; doc 118 §6; checklist `Arquivos de envio`.
- Pendências: contrato de entrada (upload P2 `TARGET`).
- Limitações: não inventar conteúdo de extrato; não expor dados
  sensíveis no corpus.
- Referências: doc 85 §12; doc 118 §6; doc 91; doc 115.

## Perguntas contraditórias — contexto vigente (Gate 079)

- **"O R13 é comparável numericamente com outros relatórios?"** —
  **Não.** `NOT_COMPARABLE`: a evidência é documento bancário externo
  sem medida numérica no ERP — não há tabela Protheus nem valor
  computável para comparação.
