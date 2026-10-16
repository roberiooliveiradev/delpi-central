# TÉO Context Bridge V1

> **Status:** implementado. Canal canônico = server-side Workspace Context
> (MFE → Core `/me/workspace-context` → TÉO `get_workspace_context`).
> Site tool WebMCP permanece como **fallback** da mesma origem.

## O que é

Quando o usuário trabalha em um Processo → Melhoria → Revisão no Portal
Transforma+, o TÉO (especialista no ChatGPT) pode receber o **contexto
identificador** daquela tela sem o usuário digitar IDs:

```text
Portal Transforma+                     Core                    TÉO MCP
─────────────────                     ────                    ─────────
route + hash ──► resolver canônico ──► PUT /me/workspace-context
       │                                    │                    │
       │                                    ▼                    ▼
       │                            workspace_context_v1   get_workspace_context
       │                            (efêmero, TTL, por         │
       │                             usuário, multi-tab)      ▼
       └─► fallback: site tool WebMCP               get_process_context
                                                              │
                                                              ▼
                                                       Transformômetro API
                                                       (leitura autoritativa)
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

## Canal canônico — Workspace Context server-side

O hook `useWorkspaceContextPublisher` (montado no `App`) publica
`workspace_context_v1` no Core (`PUT /core-api/me/workspace-context`) em
eventos semânticos: mudança de rota/hash/seleção e foco/visibilidade —
dedupe por assinatura evita flood. No `pagehide`/unmount a aba remove seu
contexto (`DELETE`, keepalive). Falha de publicação nunca quebra o Portal.

O Core resolve por usuário autenticado com TTL e desempate multi-tab
(`client_instance_id` por aba; `focused` como evidência de foreground):
`active` | `absent` | `stale` | `ambiguous`. `active` = "workspace aberto",
não "aba focada" — o usuário conversando com o TÉO em outra janela mantém
o contexto ACTIVE.

O TÉO lê via `get_workspace_context` (MCP) / `gpt_get_workspace_context`
(GPT Actions) — mesma capability. Referência explícita do usuário sempre
prevalece sobre o contexto ambiente; `ambiguous` ⇒ uma pergunta
discriminativa; nunca busca silenciosa por "processo mais provável".

## Site tool (WebMCP) — fallback

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
- É projeção do mesmo resolver canônico (`resolveTeoPortalContext`) —
  útil nos ambientes WebMCP; não é mais o canal primário.

## Sem fluxo manual

O fluxo legado de copiar/colar contexto foi removido: não existe ação
TÉO no `PortalTopBar`, handler de clipboard nem payload manual. Os dois
canais automáticos (Workspace Context server-side + site tool WebMCP)
são suficientes. Em ambiente onde nenhum deles alcança o TÉO, o usuário
informa o código do processo na conversa (ex.: `PROC-0080`) — dado já
visível na tela.

Não existe contrato oficial para abrir o ChatGPT/TÉO por URL com contexto
injetado — nenhuma URL é inventada.


## Aceite funcional do contexto automatico — 2026-10-16

**Resultado:** `ACCEPT` para a navegacao contextual observada no fluxo testado;
cenarios de isolamento, expiracao prolongada e navegacao entre dois processos
distintos permanecem `TEST_NOT_RUN`. Este aceite nao equivale a uma
homologacao E2E universal.

**Owners:** Portal (navegacao/publicacao), Core (Workspace Context), 
Transformometro (dados canonicos), TEO (consumidor governado).
**Fonte da evidencia:** respostas ao vivo das capabilities
`get_workspace_context` e `get_process_context` durante uma sessao
autenticada em 16/10/2026. Sao leituras de runtime observadas na conversa,
nao arquivos de log, screenshots nem testes automatizados de navegador.
**Implementacao de referencia:** [remocao do clipboard
`8626e87482`](https://github.com/roberiooliveiradev/delpi-central/commit/8626e874822bb1b4cf3523f559c9b8cc3993a54c)
e [ajuste documental
`5a458cc50d`](https://github.com/roberiooliveiradev/delpi-central/commit/5a458cc50db0199d56633cbf01336a4c835d94fe).

Referencias usadas na verificacao (apenas identificadores de navegacao):

- Processo `PROC-0080`: `b6c2db01-662a-4fbb-8102-11d331d00e03`
- Instancia GLPI #1197: `d518444b-fc6f-45de-8679-99a47d057279`
- Revisao TO-BE Dashboard Suprimentos v1.0:
  `08df3a4c-fe2d-4f35-ba08-efa114a56bd2`

| Cenario observado | Evidencia de runtime | Estado |
| --- | --- | --- |
| 1. Home -> processo | `home`, sem referencias -> `route_id=processo`, `process_id=PROC-0080 (UUID acima)`, `area=visao-geral` | `PASS` |
| 2. Visao Geral -> Resultados | `area=resultados`; `canonical_path` termina em `#resultados`; processo preservado | `PASS` |
| 3. Resolucao da instancia | `instance_id=d518444b-...`; `get_process_context` confirmou GLPI #1197 vinculada ao processo | `PASS` |
| 4. Selecao da revisao | `route_id=revisao`, `revision_id=08df3a4c-...`, `area=vigencia`; processo e instancia preservados | `PASS` |
| 5. Leitura autoritativa | `get_process_context(process_id, instance_id, revision_id)` retornou revisao TO-BE correta, ativa e aprovada | `PASS` |
| 6. Saida para Dashboard | `route_id=dashboard`, `canonical_path=/apps/transformometro/dashboard`, `process_id=null`, `instance_id=null`, `revision_id=null` | `PASS` |

Todas as chamadas de `get_workspace_context` na sequencia observada
retornaram `status=active`. A validacao posterior no dominio nao promoveu
a dica de navegacao a autorizacao: o TEO leu os dados por capability
tipada, preservando `Workspace Context != Domain Truth != AuthZ`.

**Classificacao de evidencias:** respostas efetivamente obtidas das duas
capabilities = `PROVEN` para esses casos; relatos anteriores do Devin
sobre 489 testes e deploy = `INFORMED` neste registro, sem reexecuta-los
nesta rodada. Nao houve escrita de dados de negocio.

**Cobertura residual (nao provada por esta sessao):**

- Troca direta de um processo A para outro processo B distinto:
  `TEST_NOT_RUN`.
- Duas abas com selecoes concorrentes/ambiguidade: `TEST_NOT_RUN`.
- Logout, troca de identidade e isolamento entre usuarios: `TEST_NOT_RUN`.
- Expiracao por TTL e renovacao apos longa inatividade:
  `TEST_NOT_RUN` (estado `stale` observado em consulta anterior,
  mas renovacao E2E nao testada aqui).
- Testes negativos de autorizacao com outro usuario:
  `TEST_NOT_RUN`.
- Automacao E2E de navegador e comprovacao independente de SHA em
  producao nesta rodada: `TEST_NOT_RUN`.

**Decisao do Chat 00:** `ACCEPT` para o fluxo de navegacao
Home -> Processo -> Resultados/Instancia -> Revisao -> Dashboard.
Sem nova implementacao ou alteracao de contrato por este aceite; manter
residuais como trabalho de Integration & Acceptance (07). Nao declarar
`PASS` para cenarios nao executados.


## Arquivos

- `src/integrations/teo/teoPortalContext.ts` — modelo `TeoPortalContext`
  + resolver puro (`resolveTeoPortalContext`);
- `src/integrations/teo/teoWorkspaceSelection.ts` — loja mínima da
  seleção corrente do workspace (publicada por `ProcessResultsSection`);
- `src/integrations/teo/teoContextBridge.ts` — adapter WebMCP
  (`document.modelContext`, fallback `navigator.modelContext` legado);
- `src/integrations/teo/workspaceContextPublisher.ts` — payload
  `workspace_context_v1` + PUT/DELETE no Core;
- `src/integrations/teo/useWorkspaceContextPublisher.ts` — hook que
  publica em eventos semânticos e despublica no unmount.

## Limites conhecidos

- O contexto só localiza: autorização e fatos de domínio continuam
  `get_process_context(process_id, instance_id, revision_id)`.
- O store do Core é efêmero (TTL) — contexto expirado resolve `stale`,
  nunca usado silenciosamente.
- Navegação reversa (TÉO → "Abrir no Portal") é FUTURE — `canonical_path`
  já está no contrato para isso.
