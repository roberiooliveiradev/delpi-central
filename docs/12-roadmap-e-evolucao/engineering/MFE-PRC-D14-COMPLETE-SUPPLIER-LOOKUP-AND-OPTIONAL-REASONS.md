# D14 — Busca colapsável V2 e justificativas opcionais individuais (SB1 e SA5)

**Data PO:** 2026-11-08. **Status:** IMPLEMENTED_DEV / PROD_SUSPENDED. **Task:** `ENG-PRC-D14-FIX-TABLE-AND-CONTEXTUAL-REASONS` (fechamento de `ENG-PRC-D14-FULL-UX-AND-CONTRACT`).
**Documentos de origem:** MFE-PRC-WIREFRAME-FORNECEDORES-V2-APPROVED.md, MFE-PRC-D13-DIRECT-EDIT-AUTOMATIC-DIFF-AND-SA5-OPERATIONS.md, MFE-PRC-D12-ROUTES-API-DELPI-IMPLEMENTATION-BLUEPRINT.md, MFE-PRC-REF-012-INDIVIDUAL-FIELDS-AND-SUPPLIER-LINK-OPERATIONS.md.
**Owners:** Portal Engenharia MFE (UX), Engineering API (intake/draft/domain/verify/audit), api-delpi (read-only SB1/SA2/SA5), Core (RBAC), Engineering owner (regras técnicas); TOTVS é a fonte oficial. Não criar novo owner ou boundary.

## 1. Gap comprovado por capturas e leitura de código

- O MFE atual mantém a pesquisa PrcSupplierCellLookup sempre aberta na coluna "Fornecedor", concatenando codigo/loja/razao e repetindo Loja e Razão social nas demais colunas. Isso NÃO implementa o wireframe aprovado V2 (lupa → busca colapsável por linha → seleção oficial → células separadas).
- Em UPDATE, justificativas são inputs permanentes, required e maxLength 500 sob cada campo SB1; existe UMA supplierReason geral compartilhada com todas operações SA5.
- validateStep no MFE e validate_supplier_link_changes no domínio atualmente exigem reason; verificar também validate_update_changes, DTOs, revisions e EVA. PO agora aprova razões opcionais por atributo, multiline e 250 caracteres.
- A captura CREATE mostra sugestão visual de autocomplete no campo. Não assumir que popup do Chrome equivale ao resultado SA2 oficial; testar role option, request e seleção.
- D13 corrige reported P0 de verificação SA5-only, mas baseline oficial de ADD/REMOVE não foi comprovado persistido no server; preservar fail-closed e não declarar aceite se faltar.

## 2. Contrato visual obrigatório — tabela V2 em CREATE e UPDATE

Colunas separadas, nessa ordem:
1) Busca: SOMENTE botão icon search/lupa com aria-label e aria-expanded;
2) Código (A2_COD), somente leitura, zeros preservados;
3) Loja (A2_LOJA), somente leitura;
4) Razão social (A2_NOME), somente leitura;
5) Nome fantasia (A2_NREDUZ), somente se disponível oficialmente; senão traço honesto/ocultar em responsivo;
6) Part Number (A5_CODPRF), editável na própria linha, opcional;
7) Catálogo (A5_CODPRCA), editável na própria linha, opcional;
8) Ações: icon trash-2/undo-2, sem botão textual largo.

NUNCA escrever "CODIGO / LOJA — RAZAO" dentro da célula Busca. Não duplicar código/loja/nome. Em CREATE, Adicionar fornecedor (+) cria linha de identificação pendente e oferece lupa; em UPDATE, mostrar vínculos oficiais SA5 pré-carregados, permitindo editar atributos individualmente, e Adicionar cria uma operação ADD com seleção SA2. Alterar fornecedor de vínculo existente é operação de identidade, não pode substituir chave silenciosamente.

Busca por linha COLAPSADA por padrão:
- Lupa abre área de busca contextual desta linha; foco no input, aria-controls/expanded.
- Input busca código, razão social e fantasia; resultados reais SA2 com razão social principal e código/loja/fantasia secundários.
- Debounce e loading imediatos, abort/epoch para requests velhas; empty apenas após resposta, error/retry honesto, 401/403, sem limitar a lista já carregada.
- Selecionar preenche atomicamente codigo+loja+razao, fecha pesquisa e preserva PN/Catálogo na mesma linha quando aplicável; escolher identidade diferente requer regras explícitas sem mutação silenciosa.
- Escape, botão fechar, clique externo: fecha sem apagar seleção nem criar diff; unmount sem portal órfão.
- Usar AnchoredPanelPortal oficial do plugin-ui para sugestões fora do overflow de tabela; preservar E2E D7–D10 e acesso teclado ArrowUp/Down/Enter/Escape; desabilitar autocomplete nativo do browser apenas neste input quando tecnicamente compatível.
- Identidade supplierCode/store, sem duplicações, sem texto livre como fornecedor oficial.
- 0/1/N fornecedores, IDs estáveis por linha (nunca index como key), foco e erros por linha.
- Desktop tabela alinhada; tablet scroll só no card; mobile cards de fornecedor com mesmos atributos e busca colapsável; zoom 200%; dropdown sem clipping.

Wireframe textual:
FORNECEDORES                                    [+ Adicionar fornecedor]
BUSCA | CÓDIGO | LOJA | RAZÃO SOCIAL | FANTASIA | PART NUMBER | CATÁLOGO | AÇÕES
[⌕]   | 000002 | 01   | TE CONNECTIVITY... | TYCO | [880643-1] | [CAT-1] | [lixeira]
       PN: [Adicionar justificativa]   Catálogo: [Adicionar justificativa]
[linha de busca expandida quando clicar lupa]
[⌕ Buscar por código, razão social ou nome fantasia ...]
[Resultado oficial SA2: Razão social / Código · Loja · Fantasia]

## 3. Justificativa opcional por CAMPO em CREATE e UPDATE

A regra vale para todos os campos SB1 editáveis: Descrição, Grupo, Tipo, Unidade, Armazém padrão, Conta contábil, Produto de terceiros, Referência do cliente.
A regra vale SEPARADAMENTE para cada atributo da amarração SA5: Part Number e Catálogo. Se os dois mudarem na mesma linha, devem existir DUAS justificativas independentes (nunca uma justificativa geral da linha).
Além disso, cada operação ADD de vínculo e cada solicitação de REMOVE tem sua própria justificativa opcional, separada das justificativas por atributo. Se o owner exigir reason para REMOVE por política de risco ainda pendente, manter operação de remoção bloqueada até signoff, sem impor regra aos demais campos.

Padrão único:
- Botão discreto icon message-square-plus "Adicionar justificativa (opcional)" perto do campo.
- Apenas ao clicar, expandir textarea multiline de 3 linhas, via plugin-ui/façade, com 0/250 e maxLength 250; recolher mantém texto; remover limpa somente este campo; botão muda para "Editar justificativa".
- Por padrão não exibir inputs permanentes de justificativa. Não exigir justificativa para avançar/submeter campo alterado, salvo política técnica aprovada específica.
- No UPDATE reason não cria mudança sozinho; na volta ao baseline diff e reason ficam fora do payload. No CREATE reason é opcional, e metadados devem seguir contrato formal, sem injetar into propriedades desconhecidas.
- Para SA5 manter estado por stable row key + atributo; PN reason nunca copia para Catálogo, outro fornecedor ou operação ADD/REMOVE.
- Strings omitidas, null ou vazias significam nenhuma razão; strings presentes até 250; 251+ rejeitado 422 backend, sem truncamento silencioso no servidor.
- Auditoria não é opcional: ator, tempo, before/after, tipo op, origem, revisão e provenance são obrigatórios conforme contrato mesmo sem motivo.

## 4. Contratos, API e domínio — mudar toda a cadeia

Front: remover supplierReason global e required reasons. Estado reasonsPorCampoSB1 + reasonsPorChaveSA5PorAtributo + reasonsPorOpAddRemove.
Contrato backend aditivo/versionado: changes[] cada path com reason opcional; supplierLinkChanges[] operação add/update/remove com reason da operação opcional e razões de atributo independentes. Shape candidato (validar com owner e compat): fieldReasons {partNumber: reason, catalogNumber: reason} + reason (op). Não criar DTO paralelo ao que REST/EVA já usa. Preservar legacy payload/compatibilidade e idempotência.
Domain/Application: relaxar obrigatoriedade de reason nos use cases autorizados; validar 250 por motivo e por atributo, sem afetar required fields do produto, owner AuthZ, CAS, approval, state/verify.
PG: persistir razões por atributo/operacao na estrutura governada; se JSONB atual suportar, não adicionar migration desnecessária. Recuperar no draft/detalhe/histórico/revisão/evidência.
REST/EVA: paridade via mesmos use cases, exatamente seis tools existentes, sem tokens em prompt/artefatos. Api-delpi sem writes.
P0: garantir SA5-only entra no conjunto obrigatório verify; ADD exige ausência no baseline oficial persistido e presença posterior; REMOVE exige presença anterior e ausência posterior em read completo, owner signoff; fail-closed mismatched/unverifiable/ambiguous/incomplete. NÃO mudar authority nem habilitar remoção sem regra técnica aprovada.

## 5. Sequência fixa de execução (Devin)

A. Ler AGENTS.md, HEAD/git status e docs D14/V2/D13/D12/REF-012; inventariar todas as validações reason e propriedades do plugin-ui.
B. Definir contrato único e compatível para reasons por atributo (owner, consumidor, errors/AuthZ/versioning/idempotency/audit).
C. Backend-first: domínio, DTO, casos de uso REST/EVA, persistência e testes (reason omitido/250/251, PN e catálogo independentes, SA5 add/remove governado).
D. Refatorar CREATE e UPDATE: tabela V2 de 8 colunas, ícones oficiais, lupa com painel colapsável, busca oficial SA2, mobile; remover concatenacão e textos duplicados; eliminar justificativa geral.
E. Refatorar todos campos SB1 e PN/Catálogo/ADD/REMOVE para botão individual de justificativa expandida com textarea e contador 250; razão opcional; diff D13 mantém-se.
F. Executar typecheck/build/Vitest/pytest, PG real, API authenticated, Playwright desktop/tablet/mobile com cenários concretos (não vacuamente listbox visível), a11y, zoom200, screenshots antes/depois.
G. Rebuild/recreate containers DEV engineering e engineering-api e api-delpi somente se tocada, verificar health, remoteEntry e bundle hash, login SSO + query SA2 real, integração e regresso CREATE/UPDATE.
H. Atualizar D14, V2, D13, REF-012, blueprint D12, plano consolidado, outcomes com SHA; commit/push main conforme AGENTS; preservar diffs concorrentes. NENHUM deploy produção.

## 6. Acceptance matrix BLOQUEANTE

B01 CREATE lupa colapsável e nenhuma busca permanente — PASS somente com screenshot e Playwright autenticado.
B02 UPDATE lupa colapsável em vínculos SA5 e novas linhas — PASS browser.
B03 Colunas Código/Loja/Razão/Fantasia/PN/Catálogo separadas, sem concatenação — PASS browser.
B04 Busca por código/razão parcial/fantasia SA2 real e seleciona preenchendo identidade — PASS browser, request/option não vazio.
B05 Keyboard/popover/viewport/mobile/tablet/zoom200 sem corte e sem autocomplete Chrome concorrente — PASS browser.
B06 PN e Catálogo editáveis na linha, identidade e diffs estáveis, duplicados/empty/abort seguros — PASS.
J01 Todos 8 campos SB1 possuem justificativa individual multiline colapsável, opcional 250 — PASS.
J02 Cada PN e cada Catálogo tem razão própria não compartilhada — PASS.
J03 Cada ADD e REMOVE tem reason própria, REMOVE só após owner; sem supplierReason geral — PASS/PENDING_OWNER.
J04 0 e 250 caracteres aceitos, 251 rejeitado no backend 422; descartar não gera fake diff — PASS.
J05 CREATE/UPDATE/draft/details/review/audit/REST/EVA reason persistida e mapeada corretamente — PASS.
S01 SA5-only fail-closed, incompletude/mismatch/ambiguidade nunca publica — PASS.
S02 Baseline server-side authoritative para ADD e REMOVE, e regra owner REMOVE — PASS/PENDING_OWNER.
T01 Typecheck/build/Vitest/pytest/PG real/Playwright desktop tablet mobile screenshots — PASS (reportar TEST_NOT_RUN honestamente).
D01 DEV containers atualizados, bundle fingerprint, Gateway JWT e docs GitHub — PASS.
P01 Produção intocada — PASS.

D14 não é aceito por implementação parcial de UI ou backend. Se houver operação dependente de owner, entregar o restante, marcar PARTIAL e bloquear somente o que não foi autorizado.

## 7. Formato de evidências

TASK_ID: ENG-PRC-D14-FIX-TABLE-AND-CONTEXTUAL-REASONS
BASE_SHA: f1f4767b3015f07310ddc61769fe282528416086
FINAL_SHA: 7c13fd75f0c20c2ac29c05155f6806612a2eb917
FOREIGN_DIFF_PRESERVED: delia-api/*, engineering-api/.../drawing/understanding.py, plugins/tv-dashboard-presentation/*, tv-dashboard-api/*

B01_CREATE_COLLAPSIBLE_SEARCH: PASS — lupa exclusiva; busca fechada por padrão; Playwright autenticado desktop/tablet/mobile
B02_UPDATE_COLLAPSIBLE_SEARCH: PASS — vínculo oficial com lupa desabilitada (identidade SA5 preservada); nova linha com lupa
B03_DISTINCT_COLUMNS: PASS — Busca|Código|Loja|Razão|Fantasia|PN|Catálogo|Ações sem concatenação
B04_REAL_SA2_CODE_LEGAL_TRADE: PASS — seleção SA2 preenche colunas; busca por razão social remota (ex.: BRITAGEM TRES RIOS)
B05_OVERLAY_A11Y_MOBILE: PASS — AnchoredPanelPortal; aria-expanded/controls; cards ≤768px
J01_SB1_8_OPTIONAL_REASON: PASS — gatilho só com alteração/preenchimento; textarea ≤250 colapsado
J02_PN_CATALOG_INDEPENDENT: PASS — PN e Catálogo com toggles/razões independentes (E2E + Vitest)
J03_ADD_REMOVE_REASONS: PASS (REMOVE UI) / PENDING_OWNER (publicação REMOVE no ERP)
J04_250_CLIENT_BACKEND_422: PASS — maxLength 250 cliente; pytest 250 ok / 251 → 422
J05_CREATE_UPDATE_DRAFT_EVA_AUDIT: PASS — canal `reasons` no create fora do technicalDraft; update via fieldReasons
S01_SA5_ONLY_VERIFY: PASS — herdado D13 (fail-closed preservado)
S02_SERVER_BASELINE_ADD_REMOVE: PARTIAL — ADD baseline ok; REMOVE aguarda signoff owner
TYPECHECK: PASS (`npm run typecheck` engineering)
BUILD: PASS (`npm run build` + docker rebuild `delpi-engineering`)
VITEST: PASS — `prcIntakePayload.test.ts` 13/13
PYTEST: PASS — `test_product_registration.py -k d14` 5/5
PLAYWRIGHT_DESKTOP_TABLET_MOBILE: PASS — 6/6 (`prc-suppliers.spec.ts`)
SCREENSHOTS: `docs/12-roadmap-e-evolucao/engineering/assets/d14-fix/` (+ espelho gitignored em `plugins/engineering/e2e/artifacts/`)
DEV_CONTAINERS: `delpi-engineering` recreate + `delpi-engineering-api` restart (local DEV)
BUNDLE_FINGERPRINT: `__federation_expose_App-QrdhYuIl.js` + `style-7OfO7Qlv.css` (gateway `/apps/engineering/assets/remoteEntry.js`)
DOCS: este arquivo + wireframe V2 atualizado
PROD_DEPLOY: NOT_PERFORMED
ACCEPTANCE: PASS (DEV) / PARTIAL (REMOVE owner)
BLOCKERS: remoção SA5 oficial ainda depende de regra técnica do owner
EXECUTION_DRIFT: nenhum material
ARCHITECTURE_DECISION_REQUIRED: nenhum

### Screenshots canônicos (desktop)

| Estado | Arquivo |
|---|---|
| Busca colapsada (só lupa) | `assets/d14-fix/prc-suppliers-search-collapsed-lupa-only-desktop.png` |
| Busca expandida | `assets/d14-fix/prc-suppliers-search-open-new-row-desktop.png` |
| Seleção SA2 → colunas | `assets/d14-fix/prc-suppliers-supplier-selected-columns-desktop.png` |
| PN alterado → Justificar compacto | `assets/d14-fix/prc-suppliers-pn-changed-reason-toggle-desktop.png` |
| Editor ≤250 aberto | `assets/d14-fix/prc-suppliers-reason-editor-open-close-desktop.png` |
| UPDATE baseline sem gatilho | `assets/d14-fix/prc-update-update-baseline-desktop.png` |
| UPDATE PN alterado | `assets/d14-fix/prc-update-update-pn-changed-desktop.png` |
| UPDATE PN+Catálogo | `assets/d14-fix/prc-update-update-both-changed-desktop.png` |
| UPDATE PN revertido | `assets/d14-fix/prc-update-update-pn-reverted-desktop.png` |
| UPDATE revisão | `assets/d14-fix/prc-update-update-review-desktop.png` |
