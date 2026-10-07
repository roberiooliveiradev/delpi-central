# BPMN Modeler (Meu Modelador de Processos)

MFE do bounded context `bpmn-modeler`: modelagem de processos BPMN 2.0 com
edição visual (bpmn-js), validação estrutural/semântica no backend, revisões
imutáveis e layout automático via ELK em Web Worker.

## Superfícies

| Superfície | Caminho |
|---|---|
| Biblioteca de modelos | `/apps/bpmn-modeler` |
| Editor de modelo | `/apps/bpmn-modeler/models/{id}` |
| Revisão (somente leitura) | `/apps/bpmn-modeler/models/{id}/revisions/{n}` |
| API | `/apps/bpmn-modeler-api` (OpenAPI em `/openapi.json`) |

## Ajuda (feature-help-sync)

Conteúdo canônico de ajuda em `src/content/helpTooltips.ts`.
Qualquer mudança user-facing deve atualizar essas chaves no mesmo entregável.

## Arquitetura interna

- `src/editor/` — **única** fronteira com vendor BPMN (bpmn-js, bpmn-moddle,
  properties panel). Nenhum import vendor fora deste diretório.
- `src/layout/` — perfil ELK, grafo, worker e proposta de BPMN-DI
  (transiente; Accept → dirty → autosave persiste; Cancel → zero write).
- `src/state/` — máquina de save (`SaveMachine`), autosave do working copy
  (`AutosaveController` — debounce, single-flight, read-back verify) e
  capabilities. Autosave nunca cria revisão — checkpoint é explícito.
- `src/data/api/` — cliente HTTP do `bpmn-modeler-api`.

## Desenvolvimento

```bash
npm ci
npx tsc -b        # typecheck
npx vitest run    # testes unitários
npx eslint .      # lint
npm run build     # bundle MFE (remoteEntry.js + worker chunk)
npm run test:e2e  # Playwright — requer stack real (ver e2e/)
```

## E2E

`e2e/` contém a suíte Playwright das jornadas congeladas (P7 §25). Requer
stack real (gateway + portal + API + DB + Keycloak + RBAC) e identidades
de teste via `BPMN_E2E_TOKEN_{VIEWER,EDITOR,MANAGER}` e `BPMN_E2E_BASE_URL`.
