# Process Workspace — contrato de navegação (URL = autoridade)

A URL representa integralmente a seleção material do usuário:
processo → melhoria → revisão → seção. Refresh, link compartilhado e
back/forward restauram exatamente o contexto exibido — sem state paralelo.

## Formatos

```text
/apps/transformometro/processes/:processId#<section>
/apps/transformometro/processes/:processId/instances/:instanceId#<section>
/apps/transformometro/processes/:processId/instances/:instanceId/revisions/:revisionId#<section>
```

`<section>` é o token de hash (sem `#`).

## O que a URL NÃO representa

`revisao_referencia_id` (AS-IS), baseline, ids de medição/recurso,
autorização e verdade de domínio. A referência AS-IS é resolvida pelo
backend via `revisao_referencia_id`.

## Painel efetivo por hash (level-wins)

`resolveWorkspacePanelView({ view, hash })` decide qual painel renderiza
em rotas de instância/revisão:

- hash vazio ou token que é seção **do próprio nível** → painel do nível
  (instância: dados/mapeamento/diagrama/contexto/revisoes;
  revisão: vigencia/matriz/mapeamento/diagrama/medicao/investimentos/
  recursos/evidencias);
- token que é seção **exclusiva do processo** (resultados, melhorias,
  documentacao, tarefas, sala, historico, visao-geral e aliases legados
  `#dados`…`#timeline` conforme `PROCESSO_HASH_TO_PRIMARY`) → painel de
  processo com a seleção da rota.

Tokens ambíguos (`#mapeamento`, `#diagrama`, `#dados`) pertencem ao nível
da rota — comportamento legado preservado.

## Seleção → URL

Escolhas explícitas em Resultados navegam (`pushState`, via
`navigateSelection`):

| Ação | URL resultante |
|---|---|
| escolher melhoria `I` | `/processes/P/instances/I#<seção>` |
| escolher cenário `R` | `/processes/P/instances/I/revisions/R#<seção>` |
| limpar cenário | `/processes/P/instances/I#<seção>` |
| trocar melhoria | `/processes/P#<seção>` (revisão nunca atravessa instância) |
| trocar seção | mesmo path, só o hash muda |

## Regras

- Rota explícita sempre vence sobre qualquer estado transitório.
- Nunca `P/I2/R1` (cross-instance mix) — trocar de melhoria derruba a
  revisão da rota.
- `P#resultados` com várias melhorias → "Selecione uma melhoria" (sem
  fallback silencioso).
- `P/I/R` com `R` fora do escopo de `I` → estado de seleção, nunca
  correção silenciosa.
- Auto-resolução do view-model (ex.: única melhoria) é **preview**, não
  seleção — não é escrita na URL.
- Helpers canônicos: `buildProcessWorkspacePath` (path+seção),
  `resolveWorkspacePanelView` (painel efetivo). Sem concatenação manual.
