# DELPI News — Etapa 1 (execução)

**Referência histórica de análise:** `5ba8c24275eda0458fdc21fa0c4191f6407c0964`  
**HEAD de `main` ao concluir a Etapa 1 (antes do commit desta entrega):** `b1d089a558556d8563bcc9f5ba8047ab67301808`  
**Branch de trabalho:** `main` (conforme `AGENTS.md`).

## Ledger de requisitos

| ID | Requisito | Estado |
|---|---|---|
| RQ-01 | Reancorar git/regras/docs antes de implementar | ATENDIDO |
| RQ-02 | Inventariar capacidades existentes com decisão de reuso | ATENDIDO |
| RQ-03 | Definir ownership admin × público × API × TV | ATENDIDO |
| RQ-04 | Contratos conceituais fontes RSS + notícias normalizadas (sem ops prematuras) | ATENDIDO |
| RQ-05 | Prova visual navegável da apresentação futura | ATENDIDO |
| RQ-06 | Não implementar Android/APK/device mgmt | FORA_DO_ESCOPO_COM_JUSTIFICATIVA (suspenso) |
| RQ-07 | Não ampliar `external-data-api` para RSS | ATENDIDO (decisão NEW BC) |
| RQ-08 | Preservar alterações de outras tarefas | ATENDIDO (working tree limpa em `main`) |

## Aceite observável

1. Documentação em `docs/12-roadmap-e-evolucao/delpi-news/` descreve arquitetura, inventário e contratos.
2. Rota pública `/p/delpi-news/board/aberto` registra no `public-hub` e renderiza board kiosk com fixture.
3. Testes do app `delpi-news` verdes (positive + sibling + negative).
4. Sem API OpenAPI nova, sem Android, sem mudança de mandato do `external-data-api`.

## Evidência de validação

| Prova | Resultado |
|---|---|
| Vitest `src/apps/delpi-news` (Docker node:22, monorepo plugins montado) | **6/6 PASS** (`loadBoard` + `NewsBoardView`) |
| `tsc` estrito só do app `delpi-news` (+ `shell/types`) | **PASS** (`DELPI_NEWS_TSC_OK`) |
| `npm run build` completo do hub no mesmo sandbox Docker | **INCONCLUSIVE** — falhas em pacotes irmãos (`tv-dashboard-presentation`, `plugin-ui`, …) por resolução de deps via symlink; **zero** erro em `src/apps/delpi-news/*` |
| Ambiente host WSL | `node_modules` do hub owned by root → Vitest local bloqueado (`EACCES` em `.vite-temp`); validação via Docker |

Rebuild do container `delpi-public-hub` em runtime: `infra/scripts/up-*-sequential.sh` (fase MFE/`public-hub`) quando for visualizar em `/p/delpi-news/board/aberto`.

## Próximas etapas (não desta entrega)

- E2: scaffold `delpi-news-api` + schema + scheduler de coleta
- E3: admin MFE + RBAC
- E4: trocar fixture do hub por `GET /public/boards/{token}`
- E5: opcional slide external no TV Dashboard
