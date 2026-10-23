# X4.UX-R1.S9 — Supplier Creation UX Polish (CNPJ inteligente, horário local e fonte humanizada)

**Escopo:** somente `plugins/supplies` (MFE). Zero alteração de contrato, backend, RBAC, manifest ou escrita ERP.
**Status:** `ACCEPT_WITH_RESIDUAL` (código/testes verdes; validação visual em browser `TEST_NOT_RUN`).

## 1. Baseline

| Item | Valor |
|---|---|
| BASE HEAD | `1c7a96ce33` |
| ORIGIN MAIN (início) | `1c7a96ce33` |
| Escopo autorizado | três ajustes de UX no cadastro assistido + campo `tax_id` do formulário |

## 2. Evidências dos três problemas (antes)

1. **CNPJ assistido sem máscara** — `<input>` cru em `CreationAssistedFlow.tsx`: aceitava letras/símbolos como valor efetivo e não formatava `23622391000181` → `23.622.391/0001-81`.
2. **Hora ambígua** — `formatRetrievedAt` usava `toLocaleString("pt-BR")` sem `timeZone`: a hora exibida dependia do fuso da máquina do usuário, não do horário de Brasília.
3. **Fonte técnica exposta** — `CreationSuggestionsPanel` renderizava `provider_id` cru (`brasilapi-cnpj-v1`) como texto de interface.
4. **tax_id do formulário principal** — `digitsOnly` preservava o draft canônico, mas não havia apresentação CNPJ/CPF conforme `person_type` (e não aplicar máscara fixa indistinta era requisito).

## 3. Causa raiz

- Apresentação e valor efetivo estavam acoplados ao texto cru do input; inexistia camada de máscara de exibição no MFE.
- `toLocaleString` sem `timeZone` delega o fuso ao ambiente de execução — semântica de exibição indefinida.
- Não havia mapa de apresentação para provedores; o identificador técnico vazou para a UI.

## 4. Reuso verificado antes de implementar

| Necessidade | Busca | Decisão |
|---|---|---|
| Máscara CNPJ/CPF | `plugins/commercial/.../portfolioBillingTableMappers.ts` tem `formatCnpj` **local ao domínio comercial**; `@delpi/plugin-ui` (`displayFormat`, campos) **não** expõe máscara de documento | Util novo `features/suppliers/taxIdMask.ts` no bounded context de suprimentos (2 consumidores reais: fluxo assistido + formulário), sem criar pacote amplo |
| Input mascarado no kit | `SuppliesTextField`/`TextField`/`NativeTextField` não aceitam `inputMode`, `ref` nem controle de caret; `onChange(value)` não entrega `selectionStart` | `SupplierTaxIdField` replica **apenas o shell visual** com as mesmas classes BEM do kit (`textFieldBemClasses(UI_PREFIX)` + `FieldLabel`) e controla o caret — kit não tem variante mascarada |
| Datas/fuso | `plugin-ui/src/utils/periodPreset.ts` usa `America/Sao_Paulo` para calendário — convenção confirmada | `Intl.DateTimeFormat` com `timeZone` explícito em `content.ts` (formatação de timestamp de consulta, não preset de período) |
| Nome de provedor | nenhum catálogo de apresentação encontrado no Portal/kit | `providerDisplayName` centralizado em `creation/content.ts` com fallback honesto |
| Normalização | `stateMachine.normalizeCnpjDigits` já é o owner da identidade (dígitos) | preservado — `digitsOnly` novo é só apresentação/edição; `searchTaxIdChanged`/`isCnpjFormatValid` continuam normalizando pela stateMachine |

## 5. Mudanças realizadas

### A — CNPJ inteligente (cadastro assistido)

`CreationAssistedFlow.tsx`: o input passa a exibir `formatCnpjDigits` progressivo; `handleCnpjChange` normaliza para dígitos (`digitsOnly(...,14)`), reformata e agenda o caret via `cnpjInputRef` + `caretPosAfterDigits`/`digitsBeforePos` (edição no meio e remoção de separadores preservam posição coerente). `inputMode="numeric"`, `aria-invalid` no incompleto/inválido, consulta permanece manual e exige `isCnpjFormatValid` (14 dígitos + verificadores). `searchTaxIdChanged` segue comparando dígitos: mudança só de máscara **não** invalida o preview; mudança de dígitos invalida na hora (abort + sequência).

### A′ — CNPJ/CPF no formulário principal

`SupplierFormFields.tsx`: novo `SupplierTaxIdField` para `spec.key === "tax_id"` — apresentação `formatTaxIdForPerson` (J → CNPJ, F → CPF, indefinido/outros → dígitos puros sem máscara ambígua; CPF com >11 dígitos mostra dígitos para não esconder conteúdo do payload). **O `onChange` entrega somente dígitos** — draft e payload `POST /suppliers` permanecem canônicos (prova: `suppliers.test.ts` `body.tax_id === "00000000000191"` segue verde). `SupplierCreatePage` passa `personType={draft.person_type}`; edição protegida E14 inalterada. `shims/plugin-ui.d.ts` declara `FieldLabel` (export real do kit, já resolvido via alias de teste).

### B — Data/hora em America/Sao_Paulo

`formatRetrievedAt` → `Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", ... })` → `dd/mm/aaaa às hh:mm (horário de Brasília)`. O `retrieved_at` do backend é instante ISO-8601 com offset (`…Z` no provedor vigente) — nunca é mutado, nunca é subtraído manualmente, e timestamp inválido retorna o valor original.

### C — Fonte humanizada

`providerDisplayName("brasilapi-cnpj-v1")` → «BrasilAPI — dados públicos de terceiros» (sem reivindicar base oficial/homologadora). Desconhecido → mostra o próprio id (fallback honesto). `provider_id` permanece no contrato e fica acessível via `title` do elemento de fonte.

### Help sync

`helpTooltips.ts`, `userManualContent.ts`, `glossaryContent.ts`: copy ajustada para máscara automática, horário de Brasília e comportamento dígitos-only do `tax_id`.

## 6. Contratos preservados

- `POST /suppliers/creation-preview` e `GET /suppliers/existing-suppliers`: **zero mudança** — `provider_id`, `retrieved_at`, `duplicate_check.total` intactos.
- `POST /suppliers` (create) e `PUT` protegido: payload continua com `tax_id` em dígitos.
- Sem permission nova, sem rota nova, sem deploy, **PROTHEUS_WRITE_GATE = OFF** intocado.

## 7. Testes

| Suíte | Resultado |
|---|---|
| `taxIdMask.test.ts` (novo, 15) — máscara progressiva, colagem formatada/crua, símbolos, CPF, person-type, caret helpers | `PASS` |
| `creation/content.test.ts` (novo, 7) — UTC→SP, offset explícito, virada de data, fuso fixo, fallback inválido, mapa de provedor + fallback | `PASS` |
| `creation.structural.test.ts` (+4 S9) — inputMode/caret/máscara no fluxo, `SupplierTaxIdField` + personType + digits-only, `America/Sao_Paulo`/`Intl`, `providerDisplayName` + `provider_id` preservado | `PASS` |
| `stateMachine.test.ts` (27) — regressão identidade/invalidação/verificadores | `PASS` |
| `suppliers.test.ts` (64) — payload `tax_id` dígitos, máscara LGPD CPF, seções | `PASS` |
| MFE completo | **363 testes, 43 arquivos — PASS** |
| `tsc -b` | `PASS` |
| `vite build` | `PASS` (bundle `App-KA33PBbe.js`) |
| ESLint escopo alterado | `PASS` (0 erros; warnings/erros pré-existentes fora do escopo não tocados) |
| Browser interativo (digitação/caret/colagem/mobile) | `TEST_NOT_RUN` — sem browser autenticado |

## 8. RQ/AC

| AC | Resultado |
|---|---|
| AC-01 14 dígitos → máscara automática | `PASS` (unit + estrutural) |
| AC-02 colagem formatada/crua igual | `PASS` (unit) |
| AC-03 letras/símbolos normalizados | `PASS` (unit) |
| AC-04 caret coerente em edição | `PASS` (helpers unitários); interativo `TEST_NOT_RUN` |
| AC-05 inválido não consulta | `PASS` (`isCnpjFormatValid` + botão desabilitado) |
| AC-06 dígitos mudam → preview invalidado; máscara não | `PASS` (stateMachine + estrutural) |
| AC-07 CPF/CNPJ por tipo, draft/payload intactos | `PASS` (unit + payload canônico preservado) |
| AC-08 exibição America/Sao_Paulo, timestamp imutável | `PASS` (unit; contrato inalterado) |
| AC-09 fonte amigável, proveniência preservada | `PASS` (unit + `title` com `provider_id`) |
| AC-10 labels/teclado/foco/mensagens | `PASS` estrutural (`label`, `inputMode`, `aria-invalid`, `role="alert"`); interativo `TEST_NOT_RUN` |
| AC-11 regressão S8 (paginação/E14/draft) | `PASS` (16 estruturais S8/S9 + suite completa) |
| AC-12 testes/typecheck/build/help | `PASS` |

## 9. Limites de verificação e residuais

- Comportamento físico de caret em browser real (jsdom não executa composição de input) → `TEST_NOT_RUN`; helpers cobertos por unitários e markup segue o shell canônico do kit.
- `formatTaxIdForPerson` em `person_type` vazio mantém dígitos puros — decisão deliberada para não adivinhar máscara ambígua (requisito).
- Visual do novo formato `dd/mm/aaaa às hh:mm (horário de Brasília)` e do nome de fonte pendente de aceite visual.
- Deploy **não autorizado** nesta etapa — depende de aceite arquitetural posterior.

## 10. SHA final

`71ffc32ce8997ae202051afa255309c09e9d86f3` (`origin/main`, fast-forward).


## 11. Revisão GPT — aceite em código (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para implementação em código.** Revisado no GitHub HEAD `6df86f5a32`: `taxIdMask.ts`, `SupplierTaxIdField`, `CreationAssistedFlow`, `content.ts` e documentação. A máscara mantém o valor canônico numérico e o comportamento de invalidação por mudança real de dígitos; `formatRetrievedAt` utiliza explicitamente `America/Sao_Paulo`; a fonte `brasilapi-cnpj-v1` tem apresentação amigável sem alteração do `provider_id`. O commit documental posterior a `71ffc32ce8` não altera a implementação.

**Evidências reportadas pelo Cursor, não reexecutadas pelo GPT:** 363 testes MFE, typecheck e build PASS, ESLint escopado PASS. **Residual obrigatório:** teste no navegador autenticado de digitação incremental, colagem, edição intermediária/Backspace e caret, CPF/CNPJ por tipo, hora comparada ao instante ISO com offset e texto/proveniência exibidos. `BROWSER = TEST_NOT_RUN`; `DEPLOY = NOT_AUTHORIZED / NOT_EXECUTED` nesta entrega. **Não promover GATE-FEATURE S9 a PASS sem runtime.** Nenhuma alteração backend, permissão ou escrita ERP autorizada. Próximo passo exige GO separado para `S9.D1` (deploy MFE e smoke federado read-only).
