# Realtime — cobertura WebSocket (Transformômetro)

## Definição de «100%»

Todo fluxo mutável invalida as UIs relevantes **sem F5**, para usuários remotos e outras abas do mesmo usuário. Painéis keep-alive **inativos** não mantêm socket; ao reativar, fazem reload completo.

## Contrato canônico

| Camada | Módulo |
|--------|--------|
| Fan-out + enrich | `tm_app/application/services/transformometro_realtime_notify.py` |
| Client id (anti-eco) | Header `X-Transformometro-Client-Id` → `actorClientId` no evento |
| Ignore próprio evento | MFE: `collaborativeEntityUpdate.ts` (por **clientId**) |
| Keep-alive | `useWorkspaceKeepAliveReload` + `subscribeWorkspaceTreeRefresh` |
| Cross-tab local | `BroadcastChannel('transformometro-workspace')` |

## Matriz fluxo × salas × UI

| Fluxo | Salas WS | UI que reage |
|-------|----------|--------------|
| Processo CRUD / diagrama / WBS / arquivos | `processo:{id}`, `catalog:processo`, `catalog:dashboard` | Detail + árvore + listas |
| Instância / escopo | `processo_instancia`, `processo`, catalogs | Melhoria + processo |
| Revisão / vigência / overlay | `revisao`, `processo`, `processo_instancia` | Cadastro + melhoria + processo |
| Medição / investimento / vínculo | `medicao`/`investimento`/`vinculo` + revisão + processo/instância | Cadastro + matriz + comparativo |
| Matriz impacto×esforço | `revisao` (+ scope) | Matriz revisão / melhoria / processo |
| Recurso custo | `recurso_custo`, `recurso`, **revisões vinculadas**, processo/instância, dashboard | Recurso + revisão aberta + dashboard |
| Filial / setor / recurso | entity + catalog | Listas + detail |
| Import JSON / pacote | `catalog:processo\|filial\|setor\|recurso\|dashboard` | Listas + detalhes (via catalog watch) |
| Dashboard recalc | `catalog:dashboard` | Dashboard |

## Checklist manual

1. Salvar medição/investimento → priorização/comparativo sem F5.
2. Alterar custo de recurso com revisão vinculada aberta → rateio/cadastro atualiza.
3. Import JSON com processo aberto → detail/árvore atualizam.
4. Duas abas na mesma revisão → aba B reflete save da aba A.
5. Voltar à revisão keep-alive → medição/investimentos refetcham.

## Gate CI

- `tests/test_transformometro_realtime.py` — fan-out, section keys, enrich.
- `tests/test_realtime_mutation_notify_inventory.py` — rotas mutáveis chamam notify.
- MFE: `collaborativeEntityUpdate.test.ts`, `workspaceTreeRefresh.test.ts`.
