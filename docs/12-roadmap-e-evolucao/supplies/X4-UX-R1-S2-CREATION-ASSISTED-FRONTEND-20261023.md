# X4.UX-R1.S2 — Frontend de cadastro assistido (manual + CNPJ)

**Data:** 2026-10-23 · **Status:** `DONE (evidência de testes/build; smoke federado não executado)`

## 1. Baseline

- HEAD base: `1cdfa4a85a` (S1 presente e confirmado).
- `git status` limpo no início; `git fetch origin` executado.
- Escopo: **somente `plugins/supplies`** + esta documentação. Nenhuma mudança backend, permissão, migration, manifest ou rota nova.

## 2. Contrato consumido (S1, sem alteração)

`POST /apps/supplies-api/suppliers/creation-preview` — body `{ "tax_id": "<14 dígitos>" }`.

Resposta tipada em `creation/types.ts`: `tax_id_masked`, `person_type`, `duplicate_check{status, matches[]}`, `suggestions[]{field_key, suggested_value, source{provider_id, retrieved_at}, applicable}`, `unavailable_fields[]`, `write_enabled`.

O MFE fala **apenas** com o BFF — nunca `api-delpi`, `external-data-api` ou BrasilAPI (teste estrutural garante).

## 3. UX — três modalidades, um formulário

Seletor no topo da `SupplierCreatePage` (fieldset radiogroup, navegável por teclado):

| Modalidade | Comportamento |
|---|---|
| **Consultar por CNPJ** | input CNPJ + «Consultar» → preview → painel de sugestões + banner de duplicidade |
| **Buscar por razão social** | exibida como **indisponível** — R1.S3 `BLOCKED` (provider nominal não homologado); nenhuma pesquisa/mock/endpoint falso |
| **Preencher manualmente** | fluxo original intacto, funciona sem qualquer serviço externo |

Troca de modo com dados digitados pede confirmação (`window.confirm`) antes de descartar o estado assistido — o **draft nunca é apagado** pela troca.

## 4. Regras de aplicação de sugestões

Estado por campo (UX-only, `SuggestionEntryStatus`): `SUGGESTED` → `CONFIRMED` (aplicado) | `MANUALLY_CHANGED` (editado depois) | `UNAVAILABLE` (campo sem dado na fonte).

- Campo vazio: aplicável só por clique explícito.
- Campo preenchido diferente: aplicação exige confirmação de sobrescrita.
- `applicable=false` (ex.: `supplier_short_name`): nunca aplicável — hint «confira antes de usar».
- Campo ausente no provider: nada é apagado/zerado.
- Edição posterior do campo reconcilia o estado via `applyDraftPatchToEntries` dentro do `patchDraft` canônico.
- «Aplicar todas» afeta somente elegíveis com campo vazio.

## 5. Duplicidade — apresentação honesta

- `CLEAR` → «Nenhum cadastro encontrado com este CNPJ no escopo consultado» (sem garantia universal).
- `POSSIBLE_MATCH` → alerta warning + lista de matches (código, loja, nome, link para ficha E14).
- `INCONCLUSIVE` → «verificação não concluída», nunca tratado como liberado.

## 6. Estados e erros

Loading dedicado; erros tipados do envelope `ApiRequestError`: 401/403 (permissão), 404 (CNPJ não encontrado na fonte), 422 (documento inválido), **429 com `Retry-After`** (botão «tentar novamente» respeita o tempo — sem retry automático), 502/503/504 e falha de rede com fallback manual sempre visível. Respostas obsoletas descartadas por `AbortController` + sequência de requisição (`requestSeq`).

## 7. Segurança / side-effects

- Prévia é read-only: o módulo `creation/` não importa `createSupplier` nem chama `POST /suppliers` (teste estrutural).
- CNPJ não vira identidade/autorização; JWT e AuthZ seguem backend-first.
- Nenhum secret/token novo; `httpClient` canônico reutilizado.
- `write_enabled` exibido honestamente; gate ERP permanece OFF — revisão final e `POST /suppliers` inalterados.

## 8. Arquivos

Novos: `creation/{api,types,stateMachine,content}.ts`, `CreationAssistedFlow.tsx`, `CreationSuggestionsPanel.tsx`, `stateMachine.test.ts`, `creation.structural.test.ts`.
Alterados: `SupplierCreatePage.tsx` (integração), `index.css` (estilos escopados `.dashboard-supplies-portal`), `helpTooltips.ts`, `userManualContent.ts`, `glossaryContent.ts` (help sync).

## 9. Evidências

- `vitest run`: **319/319** (41 arquivos) — inclui 16 unitários novos + 5 estruturais.
- `tsc -b`: limpo. `vite build`: OK.
- `eslint`: 13 erros/21 warnings **todos pré-existentes** fora do escopo (nenhum em `creation/`, `SupplierCreatePage`, help/CSS).
- **FEDERATED SMOKE: `TEST_NOT_RUN`** — sem ambiente federado autorizado nesta fatia; responsividade/a11y revisadas por estrutura (fieldset radiogroup, `aria-invalid`, `aria-busy`, hints `role="note"`, labels associadas), não por evidência de navegador.

## 10. Limitações / gaps

- Sem evidência visual em navegador (desktop/mobile, claro/escuro) — pendente de R1.S7 acceptance.
- Busca nominal permanece `BLOCKED` (R1.S3): a UI a apresenta como futura.
- Preview não substitui validação autoritativa na criação — estado pode mudar entre consulta e confirmação.

## 11. Próximo gate

R1.S3 (provider nominal) permanece bloqueado; S4/S5/S6 não autorizados automaticamente. Aceite federado do S2 depende de R1.S7.
