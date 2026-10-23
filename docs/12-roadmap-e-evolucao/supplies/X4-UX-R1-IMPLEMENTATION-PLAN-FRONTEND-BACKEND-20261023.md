# X4.UX-R1 — Plano de implementação ponta a ponta (2026-10-23)

> **STATUS: PLANNED / PLAN APPROVED FOR DOCUMENTATION; EXECUTION GATED.** Planejamento frontend → BFF → external-data-api → api-delpi, baseado nas decisões PO de 23/10 e em inspeção pontual do HEAD. **Não autoriza implementação, alteração de RBAC, provider, migrations, cutover ou escrita Protheus.** Cada fatia requer inventário/gate específico, RQ/AC congelados e GO explícito. E10/WF-15 segue com gate próprio ainda `INCONCLUSIVE` na última evidência; X4 evolui E13/E14 existentes, não promove nova página.

## 1. Goal / fronteiras

Um único formulário `SupplierCreatePage` sob `/apps/supplies/suppliers/new`, com **três entradas**: **CNPJ direto**, **razão social → candidatos → escolha humana de CNPJ → lookup automático**, e **manual sem consulta externa**. Os caminhos assistidos convergem para um **preview de sugestões sem persistência**, identificação da origem/data por campo, edição/complementação de regras internas, revisão e POST de criação **somente se o gate Protheus e autorização próprios estiverem abertos**.

Na lista E13 (`/apps/supplies/suppliers`), mostrar apenas **diferenças acionáveis** por fornecedor, com status, contagem, freshness e atalho para seção `#enrichment` na ficha E14. `SOURCE_MISSING` quando Protheus tem dado mas fonte não fornece é informativo, **não** diferença/pendência. Não apagar propostas, corromper auditoria, forçar REJECT ou alterar enum canônico S1/S2 sem contrato/ADR.

Ownership invariant: `plugins/supplies` UX; `supplies-api` Flask AuthZ server-side, composição, drafts S2, read-model e pré-cadastro; `external-data-api` busca externa normalizada + proveniência + rate limits; `api-delpi` consulta e regras Protheus, duplicate-check no owner, writes somente quando habilitados; Core effective permissions + unidade/recurso; Keycloak SSO/S2S. Proibido MFE → api-delpi/BrasilAPI direto, import cross-context de domain/application, espelho de SA2 em Postgres, novos CRUD permissions.

## 2. Baseline inspecionado — PROVEN versus TO_INVENTORY

| Surface / route | Evidência do código consultado | Estado / implicação |
|---|---|---|
| MFE `SupplierCreatePage.tsx` | `SupplierCreateDraft` manual, `createSupplier` e confirmação outcome; `SUPPLIER_FIELD_REGISTRY` 23 campos, catálogos | **PROVEN**, preservar; não recriar página |
| MFE `SuppliersPage`/`SupplierDetailPage` | Inventário X4.P0; detalhe com `EnrichmentSection` | **PROVEN** segundo evidência X4; atalho E13 é alvo |
| BFF `GET /suppliers` | `suppliers_routes.py`, proxy paginado `/supplies/suppliers` da api-delpi | **PROVEN**, não presumir summary de enriquecimento |
| BFF `GET /suppliers/{code}/{store}` | `suppliers_routes.py`, Protheus read | **PROVEN** |
| BFF `POST /suppliers` | `suppliers_routes.py`, `sanitize_post_body` → api-delpi gated write; ACK ≠ persistence proven | **PROVEN** como rota, **write gate OFF** em runtime anterior |
| BFF `GET /suppliers/catalogs/<kind>` e `GET /suppliers/postal-codes/<cep>` | Código atual inspecionado | **PROVEN**; preservar assistência de CEP e catálogos |
| BFF 7 rotas S2 `/suppliers/{code}/{store}/enrichment-reviews...` | `supplier_enrichment_routes.py`, actor ownership e revisão persistida | **PROVEN** apenas para cadastro existente; não reutilizar S2 em pré-cadastro |
| External Data `GET /v1/cnpj/{cnpj}` | `external-data-api/.../cnpj_routes.py`, S2S `supplies-api`, BrasilAPI normalizada | **PROVEN**, fonte a reutilizar |
| External discovery por nome | Sem rota comprovada nesta inspeção; provider não homologado | **TO_INVENTORY / TARGET**, não nomear fornecedor vencedor |
| Summary list E13 | Não comprovado endpoint de contagem de diferenças; cuidado com N+1 e latest review do ator | **TO_INVENTORY / TARGET** |
| Duplicidade no Protheus por CNPJ | `GET /suppliers?query` existe, mas sem comprovação de unicidade semântica e empresa/filial | **TO_INVENTORY** owner `api-delpi` |
| RBAC/unit scope da criação/prévia | `@require_policy(can_use_operations)` no BFF; verificar escopo efetivo + unidade/ownership do novo fluxo | **TO_INVENTORY** antes do freeze |
| Provedor de nome, licença, LGPD/ROPA | Não homologado; ROPA externa formal pendente | **TO_INVENTORY / BLOCKER de nome** |

**Authority:** `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md` → `.cursor` global/especializadas → ADR/contratos → implementação HEAD → testes → docs/plan. A inspeção pontual acima **não substitui** rebaseline e full producer/consumer inventory de P0.

## 3. Rotas — existente, proposta, não criar

Rotas relativas ao owner. **URLs candidatas não são congeladas**, verificar precedência de match com `/suppliers/<code>/<store>`, DTO/errors e gateway antes de criar.

| Owner | Método/rota | Estado | Consumer; função; segurança |
|---|---|---|---|
| MFE | `/apps/supplies/suppliers/new` | EXISTING | Três entradas na mesma página e mesmo draft; opção manual independente |
| MFE | `/apps/supplies/suppliers` | EXISTING | Listagem E13 enriquecida com status/counter server-driven |
| MFE | `/apps/supplies/suppliers/:code/:store#enrichment` | EXISTING | Revisão E14, deep link; evitar rota nova |
| supplies-api | `GET /suppliers`, `GET /suppliers/{code}/{store}`, `POST /suppliers` | EXISTING | List, detail e POST gated; não misturar preview com criação |
| supplies-api | `POST /suppliers/creation-preview` | TARGET (candidate) | CNPJ → normalizar, conferir identidade + duplicidade autorizada, buscar `external-data-api` S2S, mapear allowlist de 23 campos, proveniência, sem persistência |
| supplies-api | `GET /suppliers/external-search?query=&state=&page=` | TARGET (candidate) | Nome → resultados paginados e limitados, Core AuthZ; somente depois de provider homologado |
| external-data-api | `GET /v1/cnpj/{cnpj}` | EXISTING | Lookup exato S2S; já minimizado, rate limited |
| external-data-api | `GET /v1/companies/search?query=&state=&page=` | TARGET (candidate) | Discovery provider com licença/limites/proveniência; contrato transversal, sem acesso ao domínio fornecedor |
| supplies-api | Extensão `GET /suppliers` **ou** `GET /suppliers/enrichment-summaries` | TARGET (alternative) | Read-model paginado, autoritativo por ator/unidade, counters acionáveis e last checked; decidir UMA opção no freeze |
| supplies-api | 7 rotas S2 por fornecedor | EXISTING | Review/decisions/bulk/prepare-update após existir SA2; não executar na criação |
| api-delpi | Endpoint canônico de busca exata de duplicidade CNPJ (**a inventariar**) | TO_INVENTORY | Não presumir que busca textual seja checagem de duplicidade suficiente; regras de filial e matching no owner |

### DTO candidate — `creation-preview` (TARGET)

Request `{ "tax_id": "14 digits" }` validado no BFF. Resposta mínima sugerida:
```json
{
  "tax_id": "masked-or-authorized-tax-id",
  "person_type": "J",
  "duplicate_check": {"status": "CLEAR|POSSIBLE_MATCH|INCONCLUSIVE", "matches": []},
  "suggestions": [
    {"field_key": "supplier_name", "suggested_value": "...", "source": {"provider_id": "brasilapi-cnpj-v1", "retrieved_at": "ISO-8601"}, "status": "SUGGESTED", "applicable": true}
  ],
  "unavailable_fields": ["payment_condition_code"],
  "write_enabled": false
}
```
**Exemplo estrutural, não contrato atual.** Evitar retornar `tax_id` bruto sem justificativa e autorização; nenhuma fonte externa decide código/loja/condições de pagamento/conta contábil. O BFF deve impedir que `person_type` e `tax_id` sejam alterados de modo incoerente; não inferir a classificação para outros tipos. Candidatos nome: `{ name, trade_name?, tax_id_masked_or_authorized, city?, state?, source, retrieved_at }` + pagination; uso do CNPJ integral em seleção necessita contrato seguro e não expor identificador desnecessariamente.

### Erros obrigatórios no freeze

`400/422` formato inválido, `401` sem auth, `403` capability/unidade, `404` CNPJ não localizado, `409` duplicidade/concorrência quando aplicável, `429` limite + Retry-After, `502` schema/provider inválido, `503/504` indisponibilidade. Resultado de duplicate-check `INCONCLUSIVE` não deve ser tratado como `CLEAR`. Buscar nomes exige limites mínimos de query, paginação, ordenação e mitigação de enumeração/scraping.

## 4. Fluxos / UX e políticas de dados

**Manual:** entrar em Novo fornecedor → selecionar manual → mesmo formulário atual com campos/catálogos/ajuda e revisão; não exigir fonte externa. Mantém pessoa física/outros quando contrato permitir; buscas externas PJ/CNPJ não bloqueiam uso manual.

**CNPJ:** validar 14 dígitos e dígitos verificadores segundo regra de domínio → acionar creation-preview (sem criar) → duplicate-check → sugerir dados mapeáveis com proveniência por campo → usuário confirma/ajusta → completa campos internos → revisão final → POST somente gate ON e autorização explícita. Quando provider falha, oferecer continuar manualmente sem marcar sugestão como validada.

**Razão social:** busca nominal explícita → lista de homônimos e filiais com UF/cidade/CNPJ autorizado, source e timestamp → usuário escolhe uma empresa → orquestra automaticamente o mesmo creation-preview pelo CNPJ selecionado → mesmo formulário. Nada de selecionar primeiro resultado silenciosamente. Provider não homologado → modo desabilitado/indisponível com explicação; não inventar busca via `GET /suppliers` Protheus como se fosse busca EXTERNA.

**E13 conferência:** na lista, mostrar `NOT_CHECKED | NEEDS_REVIEW | IN_REVIEW | REVIEWED | STALE/EXPIRED` como **rótulos candidatos**, não enum persistido; timestamps e source. Definir regras precisas sobre revisão por ator versus status compartilhado (ownership): não expor revisão de outro usuário; `view-all` nunca amplia unidade. Contar `actionable_pending` como propostas ainda não decididas **que exigem ação** (comparação relevante + eligibility admissível + estado da revisão). `SOURCE_MISSING` com dado interno, `MATCH`, `PROTECTED`, `NOT_COMPARABLE`, `UNSUPPORTED` são informativos, não pendências. `CURRENT_MISSING` pode ser complemento elegível. Determinar regra para `PENDING_VALIDATION`: não contar como pronta para ACCEPT sem validação; evitar falsos positivos. Preservar trilha S2 e distinguir `PENDING` técnico de pendência UX. Sem consultas BrasilAPI durante renderização/paginação da lista.

**Proveniência:** por campo mostrar `source.provider_id`, `retrieved_at`, `SUGGESTED | CONFIRMED | MANUALLY_CHANGED | UNAVAILABLE`; valor interno Protheus não perde autoridade por ausência externa. Nunca exibir QSA/CPF/contatos excluídos, raw third-party response ou secrets. Evidência de preview/consentimento somente se contrato LGPD/retention permitir; não persistir busca e resposta externa por padrão.

**Escrita:** flags de `api-delpi` permanecem OFF; a prévia deve funcionar independentemente de criar fornecedor. `POST /suppliers` **não é caminho de consulta**. Quando futuro write ON for autorizado, tratar ACK != confirmed e reconciliar GET/operation status, sem retry cego de POST indeterminado.

## 5. Grafo de execução — menores fatias e gates

| Etapa | Owner | Entrega | Precondição e aceitação | STOP |
|---|---|---|---|---|
| **R1.P0 Inventory/Freeze** | Architecture + Product + owners | HEAD/.cursor, producer-consumer contracts, provider/licença/LGPD, wireframe 3 opções, RQ/AC, route collision/flags, domain status e prioridades | Documentos canônicos + RQ/AC fechados, GO explícito por próxima fatia | `EXECUTION_DRIFT` ou `INCONCLUSIVE` se regra/owner/fonte sem prova |
| **R1.S1 BFF creation preview** | supplies-api + api-delpi (somente se duplicidade exigir) | `creation-preview` sem estado persistente, mapping de campos allowlisted, duplicate-check fail-closed, provenance/erros; reutilizar external-data-api CNPJ | Core effective AuthZ, S2S, positive+sibling+negative, timeout/429/403/duplicidade, testes; zero POST ERP | Sem duplicate-check confiável, parar/sinalizar bloqueio de criação |
| **R1.S2 MFE creation (manual+CNPJ)** | plugins/supplies | Selector 3 opções com nominal disabled se provider ainda pending; CNPJ preview+origem por campo, confirmação, draft/URL/F5, manual intacto, Help | BFF S1 aceito, kit-first, desktop/mobile, dark/light, teclado, build/test/federated smoke | Não exibir botão que implique escrita quando gate OFF |
| **R1.S3 External name discovery** | external-data-api | Provedor homologado de nomes, S2S allowlist, rate limit/cache apenas se autorizado, normalização/minimização, paginação, fonte, erros | Direito de uso + LGPD/DPO + testes e contrato aprovado; zero chamadas diretas MFE | Se provider não adequado, continuar sem nominal e registrar blocker |
| **R1.S4 BFF name search + MFE nominal** | supplies-api + plugins/supplies | Busca por nome via BFF, candidatos e seleção explícita → criação-preview pelo CNPJ automática, mesmo draft, fallback manual | S3 PASS, review RQ/AC, segurança, testes positivos/homônimos/rate limit | Sem CNPJ validável/duplicidade segura, não sugerir cadastro |
| **R1.S5 BFF summary E13** | supplies-api (DB own) | Read-model eficiente por lista/ator/unidade: contagem acionável, freshness/status e deep-link; sem scan externo/N+1 | Gate domain classification e teste query/perf, consentimento/ownership; não alterar decisões originais | Sem semântica unívoca de status, voltar a freeze |
| **R1.S6 MFE list conferência** | plugins/supplies | Coluna/filtro contagem/status/atalho para E14, manter paginação/busca, não criar página nova | S5 PASS, kit-first/help, URL/F5, positive+sibling+negative, desktop/mobile/tema/a11y, federated smoke | Summary indisponível → parcial sem bloquear listagem |
| **R1.S7 Runtime gate/acceptance** | Deploy/Infra + PO | public bundle/source SHA, smoke federado E13/E14/criação 3 opções quando provider autorizado, rollback e documentação | Dados seguros; 401/403/429/503; no ERP writes; screenshots; revisão final GPT | Smoke ausente = INCONCLUSIVE, não PASS |

**Sequência flexível por subgrafo:** S1→S2 (CNPJ/manual) pode avançar sem S3/S4 (nome); S5→S6 (conferência) independe do provider nominal. `S7` deve ser executado por fatia material publicada, não esperar indefinidamente todas as frentes. Não executar múltiplas páginas simultaneamente sem gate/GO. O grafo é `PLANNED`, não autorização para iniciar S1.

## 6. RQ/AC baseline para freeze

| RQ | Acceptance mínimo | Evidência requerida |
|---|---|---|
| RQ-R1-01 | Cadastro manual sem necessidade de serviço externo | Teste manual + provider indisponível |
| RQ-R1-02 | Consulta CNPJ válida, erros tipados e sem POST ERP | Teste BFF/S2S + test UI |
| RQ-R1-03 | Sugestões mapeadas somente a campos do POST homologados | Contract+mapper unit test e exclusões |
| RQ-R1-04 | Fonte, timestamp e estado por campo; edição/aceite explícito | UI test/visual |
| RQ-R1-05 | Duplicate-check não dá `CLEAR` por ausência de evidência | Positive, sibling, negative e regra canônica |
| RQ-R1-06 | Pesquisa por razão social traz candidatos, sem escolher automaticamente | Provider+BFF+UI tests |
| RQ-R1-07 | Seleção nome → CNPJ → consulta detalhada automática | Integration test incluindo homônimos |
| RQ-R1-08 | Erros 401/403/404/409/422/429/502/503 e fallback manual | Contract tests/visual |
| RQ-R1-09 | Resumo E13 não faz N+1 nem consultas externas por linha | Query/performance + trace |
| RQ-R1-10 | `SOURCE_MISSING` interno não entra em contagem acionável | Unit/integration + fixtures |
| RQ-R1-11 | Histórico/ownership, unit scope e sem permissões por botão | Security positive/sibling/negative |
| RQ-R1-12 | Atalho E13→E14 `#enrichment`, URL/F5, filtros | MFE integration/federated |
| RQ-R1-13 | Nenhum cadastro/edit ERP sem gate; ACK ≠ persisted | Negative tests e smoke seguro |
| RQ-R1-14 | UX acessível, mobile, claro/escuro e Help sincronizada | Visual keyboard/focus/screenshot |
| RQ-R1-15 | ROPA/provider/licença e retenção/limites verificadas | Revisão institutional documentada, sem afirmar aprovação ausente |

## 7. Execução GPT → Cursor → GitHub

Para **cada** fatia, Cursor deve entregar:
`TASK, GOAL, RQ/AC, AUTHORITIES, OWNER, BASE HEAD, ORIGIN MAIN, FINAL HEAD, GIT STATUS, CURRENT_STATE, FACTS PROVEN, TO_INVENTORY, EXECUTION_DRIFT, FILES INSPECTED/CHANGED, CONTRACT IMPACT, TESTS, SECURITY CHECKS, RQ/AC COVERAGE, RESIDUAL SEARCH, POSTCONDITION, UNRESOLVED, NEXT STEP, COMMIT/SHA, PUSH STATUS`.

Antes de mudar código: HEAD/status → instruções oficiais e `.cursor` aplicáveis (`development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`; `plan-construction`/execução/test-and-commit/feature-help-sync quando cabível) → contratos/producers/consumers/schema/testes HEAD → classificação → GO de escopo → menor diff → testes + evidência runtime → documentação/commit/push. Mudança de owner/contrato/plano por premissa invalidada = `EXECUTION_DRIFT` e STOP.

## 8. Security, rollout, rollback, DoD

- Core resolve **effective** `supplies.access` + escopo/unidade/recurso; JWT não é permission final. Validar pessoa, PJ/CPF conforme caminho; `view-all` não eleva unidade. Fail-closed em Core/provedor/limiter indisponível.
- Nome nominal exige anti-abuso e política explícita: tamanho mínimo query, debounce frontend não substitui limit backend, máximo de resultados/página, não divulgar CPF/QSA, provenance, retenção e custo.
- Prévia sem inserts em `supplies` ou SA2 sem contrato; se optar por auditoria de consulta, formalizar no owner e sob LGPD.
- Build não prova federated runtime; cada fatia exige bundle de produção identificado, E2E real sem escritos ERP, negativo de authz, estados/loading/partial/error/403/404, telas desktop/mobile, claro/escuro, keyboard/focus, URL/F5, Help, screenshots mínimos. Smoke impedido = `INCONCLUSIVE`.
- Rollback de MFE/BFF/external-data-api por artefato SHA/digest, com migrações reversíveis/compatíveis e caminho manual preservado; não alterar outras integrações.
- Produção não receberá provider nome nem escrita ERP sem contrato, DPO/licenciamento e GO correspondente.

## 9. Decisões / pendências antes do próximo código

1. **PROVEN:** formulário manual, rotas de lista/detalhe/criação gated, BFF e CNPJ externo existentes.
2. **TARGET:** preview específico de novo fornecedor, busca externa por nome, summary E13.
3. **TO_INVENTORY:** duplicate-check canônico, domínio/escopo de dados e status compartilhado vs por ator, provider nominal e condições jurídicas, field-mapping e retenção, identidade/filial no pré-cadastro.
4. **PENDING:** ROPA formal, X4.S2 visual completo, E10 gate da fila; nenhum deles é silenciosamente convertido em PASS.
5. **NEXT STEP:** autorizar especificamente `X4.UX-R1.P0` para inventário/freeze antes de implementação S1.

## 10. Fontes relacionadas

- [Decisões do PO / três entradas e rotas candidatas](./X4-UX-R1-CADASTRO-ASSISTIDO-CONFERENCIA-DECISOES-20261023.md)
- [Roadmap gestão de fornecedores](./FORNECEDORES-GESTAO-CADASTRAL-ROADMAP.md)
- [Plano principal E1–E29](./IMPLEMENTATION-PLAN.md)
- [X4.P0 contrato UX enriquecimento existente](./X4-P0-SUPPLIER-ENRICHMENT-UX-INVENTORY-CONTRACT-FREEZE-20261022.md)
- [X4.S2 evidência runtime](./X4-S2-FEDERATED-DEPLOY-RUNTIME-ACCEPTANCE-20261022.md)
- [X3 LGPD status](../shared-integrations/X3-LGPD-STATUS-AND-DEFERRED-REMEDIATION-20261022.md)
