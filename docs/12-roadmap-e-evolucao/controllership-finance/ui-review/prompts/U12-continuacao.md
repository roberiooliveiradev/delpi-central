# Prompt para o Cursor — UI review, U12 (continuação W2 → W8)

```text
PROMPT CURSOR — UI REVIEW · U12 · CONTINUAÇÃO W2 → W8

CONTEXTO
A U12 parou em W2: o marcador global do verificador (agent-kit) tratou a sessão do executor como
verificador e bloqueou as escritas. O owner limpou o marcador. Retomar do working tree parcial
(hints da paginação, filtersAriaLabel, renderCfRecordCard, catálogo de campos W3,
CfFilterBarShell, rótulo de filial), sem refazer W0/W1.
Antes de editar: git status e git diff --stat; conferir que o parcial ainda compila e passa nos
testes do MFE. Se o marcador voltar a bloquear, PARAR e reportar (não contornar o guard).

REVISÃO DO CLAUDE SOBRE W1 (0cbe6c3d65) — corrigir junto com W2/W6
R1 · Ordenar ocorrências por «status» não ordena. `_occurrence_sort_key` lê row["status"], mas a
   situação da ocorrência (pendente/resolvida) vem do store de status (`_statuses_map`), não da
   linha. Ordenar pelo valor do mapa (o mesmo de `_status_from_map`), com teste que prova a ordem.
R2 · A lista branca precisa cobrir as colunas que a tela mostra. Ocorrências: faltam rule (Regra)
   e field (Campo); Protheus e XML: ordenar pelo valor tipado do campo (número para dinheiro e
   alíquota, data para data, texto para o resto) ou registrar como exceção com motivo.
   Notas casadas, Sem par, CT-e, Lançadas fora do período e TES: a lista branca segue as colunas
   definidas em W6. Teste de contrato: toda coluna `sortable` do MFE com paginação no servidor
   existe na lista branca do recurso na BFF.

EXECUTAR
W2 → W8 de prompts/U12-cursor.md e track.md §10, com as mesmas regras, critérios de aceite e
report. Um commit por etapa (W2 por página ou grupo pequeno), push a cada etapa.
```
