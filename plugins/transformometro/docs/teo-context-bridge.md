# TÉO Context Bridge V1

> **Status:** implementado (frontend-only). Aceite ChatGPT depende de
> ambiente com Site tools (ver limitações abaixo).

## O que é

Quando o usuário trabalha em um Processo → Melhoria → Revisão no Portal
Transforma+, o TÉO (especialista no ChatGPT) pode receber o **contexto
identificador** daquela tela sem o usuário digitar IDs:

```text
Portal Transforma+                ChatGPT                    TÉO MCP
─────────────────                ────────                   ─────────
route + hash ──► context bridge ─► site tool / clipboard ──► get_process_context
                                                              │
                                                              ▼
                                                       Transformômetro API
```

## Contexto ≠ autorização ≠ dado de domínio

O bridge informa apenas **onde o usuário está**. O payload contém somente
identificadores de navegação:

```json
{
  "version": "1",
  "product": "transformometro",
  "process_id": "… | null",
  "instance_id": "… | null",
  "revision_id": "… | null",
  "area": "resultados | null",
  "canonical_path": "/apps/transformometro/processes/…#resultados"
}
```

Nunca inclui token, cookie, permissão, cargo, e-mail ou conteúdo de
domínio. IDs sozinhos não concedem acesso — o TÉO relê o estado canônico
via `get_process_context` e o backend continua fail-closed.

`area` é um hint conversacional (ex.: `resultados`, `mapeamento`), não
policy e não restringe o TÉO.

## Mapeamento rota → contexto

| Rota | IDs | area |
|---|---|---|
| `/processes/:p` | process_id (+ seleção do workspace) | seção do workspace (8 seções) |
| `/processes/:p/instances/:i` | + instance_id | seção da melhoria |
| `…/instances/:i/revisions/:r` | + revision_id | seção da revisão |
| `…/diagram/edit` | ids do nível | `mapeamento` (processo) / `diagrama` |
| demais telas | todos `null` | `null` |

## Seleção do workspace (deep-link V1)

Desde a deep-linked selection, **a URL é a autoridade da seleção
material**: escolher melhoria/cenário em Resultados navega para
`/processes/:p/instances/:i[/revisions/:r]#<seção>` — refresh, share e
back/forward restauram P/I/R sem state paralelo.

Em rotas aninhadas, um hash que é **seção exclusiva do processo**
(resultados, melhorias, documentacao, tarefas, sala, historico,
visao-geral + aliases) abre o painel de processo com a seleção da rota
(`resolveWorkspacePanelView`, level-wins); hashes que são seção do
próprio nível continuam abrindo o painel de instância/revisão.

A loja `teoWorkspaceSelection` (publicada por `ProcessResultsSection`)
permanece apenas como **fallback de transição**: cobre os casos em que a
UI exibe uma seleção auto-resolvida pelo view-model sem escolha explícita
(ex.: única melhoria) e a URL não a materializa. Precedência inalterada:

```text
process_id  ← rota
instance_id ← rota explícita, senão seleção publicada do mesmo processo
revision_id ← rota explícita, senão seleção cuja instance_id bate
```

Aliases legados de hash (`#diagrama`, `#arquivos`, `#priorizacao`,
`#dados`, `#timeline`) normalizam para a seção canônica. Rotas PT legadas
(`/processos/…`) resolvem os mesmos IDs e `canonical_path` sai em EN.

Nada é inventado: melhoria/revisão não selecionadas saem `null`. O
contexto é derivado de `window.location` no momento da chamada — sem
cache, sem stale, zero requests de domínio extras.

## Site tool (WebMCP)

`document.modelContext.registerTool` registra:

- `get_current_transformometro_context` — read-only, sem input, retorna o
  contexto acima.

Suporte oficial (documentação OpenAI "Site tools", ago/2026):

- **ChatGPT desktop — navegador integrado**, ChatGPT Work e Codex;
  modelos GPT-5.6 Sol / GPT-6 Sol (Luna tem WebMCP desabilitado);
  indisponível em workspaces Enterprise/Edu.
- Tools em iframes **não são descobertas**. Como o plugin é
  `renderMode: federated`, ele roda no documento top-level do Portal e o
  registro funciona. Se o Portal for embutido em iframe, a site tool não
  será descoberta (limitação do navegador).
- Feature-detect: sem `modelContext` o registro é no-op e o Portal segue
  normal.

## Fallback portátil

Fora do ambiente com Site tools, a ação **TÉO** na barra superior
(visível dentro do workspace de processo) copia um payload curto:

```text
TÉO, use este contexto do Portal Transforma+:
process_id=…
instance_id=…
revision_id=…
area=resultados
path=/apps/transformometro/processes/…
```

Não existe contrato oficial para abrir o ChatGPT/TÉO por URL com contexto
injetado — nenhuma URL é inventada.

## Arquivos

- `src/integrations/teo/teoPortalContext.ts` — modelo + resolver puro +
  payload de clipboard;
- `src/integrations/teo/teoWorkspaceSelection.ts` — loja mínima da
  seleção corrente do workspace (publicada por `ProcessResultsSection`);
- `src/integrations/teo/teoContextBridge.ts` — adapter WebMCP
  (`document.modelContext`, fallback `navigator.modelContext` legado);
- `src/integrations/teo/useTeoPortalContext.ts` — hook reativo a rota,
  hash e seleção;
- `src/integrations/teo/TeoContextAction.tsx` — ação TÉO no
  `PortalTopBar`.

## Limites conhecidos

- Nenhum endpoint, permissão, tabela ou MCP tool nova foi criada;
  `get_process_context(process_id, instance_id, revision_id)` já cobre o
  handoff.
- Navegação reversa (TÉO → "Abrir no Portal") é FUTURE — `canonical_path`
  já está no contrato para isso.
