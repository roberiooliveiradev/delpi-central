# X4.UX-R1.S8.D1 — Deploy federado + runtime gate da conferência de cadastros por CNPJ

**Data:** 2026-10-23
**Autoridade:** autorização explícita do Product Owner («PORTAL SUPRIMENTOS — X4.UX-R1.S8.D1»)
**Escopo:** somente `supplies-api` + `plugins/supplies` (MFE). api-delpi, external-data-api, Core, Keycloak — **não redeployados**.

## Baseline

- **BASE HEAD:** `a172180890` (commit S8) → rebase sobre `origin/main` `c87dad7f00`.
- **SOURCE S8 SHA:** `a17218089073922178d84fd84ac990dc598dd1c4` — ancestralidade S1/S2/R1/R2/S7 confirmada no HEAD.
- **PRODUCTION CHECKOUT:** `srv-api` (`operador@192.168.1.237`), `~/projetos/delpi-central` → pull ff-only até `9281aa9f0955` (contém S8; commits supervenientes eram docs/outros produtos — zero mudança em `supplies-api`, `plugins/supplies`, `api-delpi`).

## Gate de segurança (pré-deploy)

| Condição | Evidência |
|---|---|
| ERP write gate OFF | `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` — `infra/.env` e env do container |
| Rollback definido | imagens anteriores `infra-supplies-api:84d02964a88f`, `infra-supplies:6b3130be529f`; SHA prod anterior `6c5bae9568` |
| Migrations no range | nenhuma (range docs-only no escopo) |
| Nova permission | nenhuma — mesma `can_use_operations` |
| Containers | todos healthy/up antes do deploy |

## Deploy sequencial (script oficial `infra/scripts/up-prod-sequential.sh`)

| Serviço | Imagem antes → depois | Container |
|---|---|---|
| `delpi-supplies-api` | `84d02964a88f` → `acc772fa65fa` | Up/healthy |
| `delpi-supplies` | `6b3130be529f` → `37dee5f0450d` | Up |
| api-delpi | `c04762910d62` (inalterado) | SKIPPED — sem mudança S8 |
| external-data-api | inalterado | SKIPPED |
| gateway/core/keycloak | inalterados | SKIPPED |

Rollback **não executado** (não necessário). Reversão conjunta (BFF+MFE) documentada: o endpoint novo é aditivo; se o BFF for revertido com o frontend S8, a lista ficaria sem fonte — reverter os dois juntos.

## Runtime gate — supplies-api (read-only)

Dentro do container, token usuário real via Keycloak interno (`delpi` realm, client `delpi-central`):

| Caso | Resultado |
|---|---|
| Sem token | **401** |
| `tax_id` inválido (`123`) | **422** |
| `page` não inteiro | **422** |
| CNPJ real existente, `page=1&page_size=10` | **200**, `total=1`, `items=1`, chaves `[blocked,state,supplier_code,supplier_name,supplier_store]`, `002012/01` |
| `page=99` além do total | **200** `items=[]` (página vazia honesta) |
| Via gateway `/apps/supplies-api/...` | 401 sem token; **200** com token, `total=1` |
| BrasilAPI durante paginação | **0** ocorrências nos logs do supplies-api |
| Escrita supplier (POST/PUT api-delpi) | **0** nos logs; `write_enabled=false` |

`POST /suppliers/creation-preview` via gateway: `200 POSSIBLE_MATCH`, `total=1`, `matches=1`, 8 sugestões com proveniência, `write_enabled=false` — contrato S8 **aditivo confirmado**.

## MFE federado

- `remoteEntry.js` → `__federation_expose_App-CHykQmuO.js` → `./App-CwatapS_.js` (cadeia verificada; asset público **200**, 268 502 bytes — mesmo hash do build local).
- Marcadores S8 no bundle real: `existing-suppliers`, `duplicate_check`, `creation-preview`, `CompactPagination`, «Conferir cadastro», «Este CNPJ já possui», «continuar o preenchimento», `noopener`.
- Proibidos ausentes: `api-delpi`, `brasilapi.com.br`, `Service-Authorization`, `s2s_`, `client_secret` — **BFF-only**.

## Regressão

- E13 list `200` (5 itens) · E14 detail `002012/01` `200` · E14 `enrichment-reviews` `200`.
- 0 containers unhealthy/restarting; ~107 containers preservados.

## Dados reais por cenário (§9)

| Cenário | Resultado |
|---|---|
| CNPJ com um registro | PASS (total=1, uma linha) |
| CNPJ sem registro | coberto por teste unitário (zero registros → `total=0`) |
| Duas lojas / códigos diferentes / >10 registros | **TEST_NOT_RUN** em produção (não havia documento autorizado conhecido nesses volumes); coberto por testes `TestExistingSuppliers` |
| Consulta indisponível → INCONCLUSIVE | preservado (teste unitário + contrato `total:null`) |

## Visual / acessibilidade

- **V1–V8 (desktop/mobile/temas/teclado/F5): `INCONCLUSIVE`** — sem browser autenticado nesta sessão.
- Não foi declarado PASS por inspeção de bundle.

## Auditoria (RQ-07) — residual

Contrato de auditoria de visualização permanece `TO_INVENTORY` (owner: Core/segurança). Nenhum evento/log improvisado criado; nenhum CNPJ bruto ou payload externo em logs comuns.

## AC coverage

AC-01–17, AC-20 `PASS` · AC-18/19 `INCONCLUSIVE` (sem browser).

## Pós-condição

Produção serve o fluxo: consulta CNPJ → aviso informativo não bloqueante → lista completa paginada (total real) → «Conferir cadastro» abre E14 em nova aba → rascunho preservado. Sem bloqueio por CNPJ repetido, sem permission nova, sem escrita ERP, sem alteração na api-delpi.


## Revisão GPT — aceite arquitetural D1 (2026-10-23)

**Veredito: `ACCEPT_WITH_RESIDUAL` para deploy e runtime HTTP** com base nas evidências registradas no GitHub e no relatório Cursor (`SOURCE S8 a172180890`, relatório de deploy `1c7a96ce33`). A revisão documental não equivale à repetição independente dos comandos SSH, testes ou validação em browser.

**PROVEN por evidência reportada:** imagens BFF/MFE atualizadas, health, endpoint paginado respondendo `200 total=1`, preview aditivo com `total`, bundle federado S8, regressão E13/E14, flags ERP OFF e nenhuma escrita identificada na janela de smoke. Logs com zero POST/PUT não constituem prova exaustiva fora da janela observada.

**Limites:** paginação com dois ou mais registros/mais de dez e navegação nova aba/retorno do draft **não foram exercitados em produção via navegador**. Portanto AC-18/19 e V1–V8 `INCONCLUSIVE`, cenários multi-registro de runtime `TEST_NOT_RUN`. A pós-condição "lista completa paginada → E14 → rascunho preservado" é **capacidade comprovada por código/contrato e bundle**, e não fluxo visual já validado. `GATE-FEATURE S8 = INCONCLUSIVE` até evidência interativa ou aceite formal de residual pelo PO.

**Auditoria de visualização:** `TO_INVENTORY`, sem contrato aprovado; não introduzir eventos ou armazenamento por inferência. Próxima fatia restrita a validação autenticada de UX (sem novo deploy nem escrita Protheus), com capturas e provas de multi-loja quando houver dados autorizados. R1.S3 permanece bloqueado; R1.S4–S6 não autorizados.
