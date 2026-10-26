# X4.PROD-C1 — Supplier Production REST Cutover

**Status:** `ACCEPT_WITH_RESIDUAL` — separação de ambientes implementada e
homologação completa (POST 53 + PUT 51) **aprovada em DELPI_TST01**; o cutover
produtivo ficou **bloqueado no gate G8** porque a REST produtiva
(`http://192.168.1.231:8061/restall`) **não expõe a rota de fornecedores**
(404 em todas as variantes) e **rejeita as credenciais técnicas** (401).
Escrita produtiva permanece OFF — fail-closed por pin de destino.

## 1. Topologia

```text
LOCAL (dev)                          HOMOLOGAÇÃO               PRODUÇÃO
api-delpi (AMBIENTE=2)   →  REST 192.168.1.233:8701/rest   →   DELPI_TST01
api-delpi (AMBIENTE=1)   →  REST 192.168.1.231:8061/restall →   DELPI   [G8 BLOQUEADO]
Listagem (E13)         →  api-delpi SQL Server              →   DELPI (inalterado)
```

`PARAMETROS_MINHADELPI` é multi-ambiente (`AMBIENTE` 1/2): **1 = conjunto
produtivo** (convenção já documentada no compose), **2 = homologação**.
Cada runtime fixa `INTRANET_PARAMS_AMBIENTE` — nenhuma seleção por request.

## 2. Fonte de configuração (inventário P0)

| Item | Achado |
|---|---|
| Resolver | `resolve_protheus_rest_config(raw)` — lê `USR_PROTHEUS`, `PSW_PROTHEUS`, `URL_REST`, `PATH_AUTH`, `PATH_SUPPLIERS`; trata inversão de labels por semântica de path; falha controlada em par ambíguo |
| Conexão | `IntranetDelpiDev.dbo.PARAMETROS_MINHADELPI` via `INTRANET_DB_*` (fallback TOTVS_DB_*/DB_*); produção usa o **mesmo** servidor/tabela |
| `environment_key` | `ambiente:{N}@{host:porta}` do `URL_REST` — registrado no tracking |
| Cache de params | Sem cache aparente por request — a leitura ocorre por operação |
| Gates | `PROTHEUS_SUPPLIER_CREATE_ENABLED`/`UPDATE_ENABLED` — OFF em produção; o ensaio ligou-os apenas no processo do script |
| Limite físico | `CONTEUDO varchar(30)` — `http://192.168.1.231:8061/restall` (35c) não cabe; forma resolvida = **origem na URL_REST + `/restall` nos paths** |

## 3. Matriz de destinos

| Runtime | REST URL | Destino | Fonte |
|---|---|---|---|
| Local | `192.168.1.233:8701` (`ambiente:2`) | DELPI_TST01 | `PROVEN` — ensaio real |
| Homologação | `192.168.1.233:8701` (`ambiente:2`) | DELPI_TST01 | `PROVEN` |
| Produção | `192.168.1.231:8061` (`ambiente:1`) | DELPI | `TO_INVENTORY` — upstream sem rota/credencial |

## 4. Implementação (S1) — guarda fail-closed

`PROTHEUS_REST_EXPECTED_BASE_URL` (env por runtime) + `assert_protheus_write_target(config, expected)` chamado nos use cases de create/update **após** resolver o config e **antes** de token/tracking/upstream:

- sem pino declarado → `PROTHEUS_REST_TARGET_UNVERIFIED` (503) — `INCONCLUSIVE → NO WRITE`;
- URL resolvida ≠ pino → `PROTHEUS_REST_TARGET_MISMATCH` (503) — `STOP — WRITE_DISABLED`;
- nenhum fallback silencioso entre ambientes; nada exposto ao frontend.

Wiring: `docker-compose.yml` + `.env.dev.example` (ambiente=2, pino TST) +
`.env.prod.example` (ambiente=1, pino `http://192.168.1.231:8061`).

## 5. Ensaio local completo (T1–T3) — DELPI_TST01

Script versionado `api-delpi/scripts/protheus_supplier_c1_full_assay.py`
(mesmo protocolo E2/E5: guard de ambiente → use cases canônicos com
gate+pin+codusr+tracking → REST GET → SQL read-back → safety DELPI).
Ator `3bfdd634…` → `codusr=000311` (Core local semeado para o ensaio).

### T2 — POST completo: `PASS`

| Critério | Resultado |
|---|---|
| Fornecedor criado | `003884/01` (CNPJ teste `98887766030041`, mod-11 válido) |
| POST_FIELDS | **53/53 enviados — 53 `PERSISTED`** (SQL field-by-field) |
| REST read-after-write | `A2_NOME` conferido via `get_supplier` |
| Código/loja | Retornados pelo upstream (SYSTEM_GENERATED) |
| Tracking | `7fd9a896` → `CONFIRMED` (200) |
| DELPI | `delpi_residue_count = 0` |

### T3 — PUT completo: `PASS` (com fixups de valores válidos)

51 campos editáveis — primeiro PUT com 50 campos (`risk_code` adiado por
lookup exausto):

| Classe | Campos | Resultado |
|---|---|---|
| PERSISTED direto | 42 | Mudança before≠sent=persisted provada REST+SQL |
| Coerência fixada (`UNCHANGED_REQUIRED`) | `person_type` (J — documento CNPJ), `state`, `country_code`, `bacen_country_code` (Brasil — coerência com município SC), `linked_customer_code` (imutável upstream por design E6/E7) | Mantidos — não é fake PASS |
| Divergentes na 1ª tentativa → **resolvidos** | `state_registration` (`987654321` inválido → IE real `251.854.221` **PERSISTED** — upstream valida DV estadual), `payment_method_code` (`90` inexistente → `01` **PERSISTED**), `linked_customer_store` (`02` ignorado, `03` 400 → par `000001/05` **PERSISTED**) | Valores inválidos corretamente rejeitados; campos editáveis com valores válidos |
| Adiado → resolvido | `risk_code` (`003`→`001` **PERSISTED**) | PERSISTED |

- `untouched_fields_preserved` = TRUE (amostra BAIRRO/CNAE/RISCO/TRANSP/RECPIS
  estável após PUT parcial; parcial aplicou só `A2_NREDUZ`).
- `identity_preserved` = TRUE (`A2_LOJA`/`A2_CGC` estáveis; `A2_COD` fora do
  read-back — registro sempre localizado pela chave 003884/01).
- Tracking: create CONFIRMED; updates CONFIRMED ×6; REJECTED ×2 (400 — os
  valores inválidos); RECONCILIATION_REQUIRED ×2 (MATA020 400 sinalizados).

## 6. Cutover produtivo (S1-destino) — **BLOQUEADO (G8)**

Evidências read-only contra `http://192.168.1.231:8061/restall`:

| Prova | Resultado |
|---|---|
| `GET /restall/` | 200 — serviço vivo |
| `GET /rest/` | 404 — apenas `restall` existe na 8061 |
| `POST /restall/api/oauth2/v1/token` | 400/401 — rota existe; **credenciais `api.delpi` rejeitadas (401)** |
| `GET/POST /restall/delpi/api/v1/suppliers` | **404** — rota não publicada (TST devolve 401/501 no mesmo teste) |
| Variantes (`/api/v1/…`, `/delpi/suppliers`, …) | 404 — API de fornecedores ausente da `restall` |

**Decisão:** `URL_REST@AMBIENTE=1` **permanece** `192.168.1.233:8701` —
virar agora quebraria o GET de detalhe E14 (que resolve REST via amb=1) e
não habilitaria nada (auth 401). O cutover exige, do owner TOTVS (Gabriel):
(a) publicação da API `delpi/api/v1/suppliers` na `restall` produtiva;
(b) credencial técnica válida para o token produtivo. Depois: `URL_REST@1 =
http://192.168.1.231:8061` + `PATH_*` prefixados `/restall` + smoke read-only.

## 7. Deploy efetivo (D1 parcial — somente código)

- `api-delpi` rebuildado em `srv-api` (`up-prod-sequential.sh --build api-delpi`),
  container `Up (healthy)`, `/health` 200.
- `PROTHEUS_REST_EXPECTED_BASE_URL=http://192.168.1.231:8061` no `.env` prod
  → se os params resolverem URL divergente, qualquer write falha fechado.
- Gates produtivos: `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`,
  `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` — confirmados no container.
- Resolução produtiva atual: `env_key=ambiente:1@192.168.1.233:8701`
  (inalterada — intencional).
- Local: `.env` dev → `INTRANET_PARAMS_AMBIENTE=2` + pino TST;
  container recriado; resolução `ambiente:2@192.168.1.233:8701` verificada.

## 8. Gates

| Gate | Estado |
|---|---|
| G1 local→TST01 | `PASS` (env_key amb=2@233:8701; ensaio real) |
| G2 POST completo | `PASS` (53/53) |
| G3 PUT completo | `PASS` (51/51 provados) |
| G4 reconciliação campo-a-campo | `PASS` |
| G5 identidade preservada | `PASS` |
| G6 tracking | `PASS` (CONFIRMED; rejeições 400 registradas) |
| G7 testes automatizados | `PASS` (492 escopo supplier; 1 falha DAVI pré-existente fora do escopo) |
| G8 config produtiva validada | **`FAIL`** — upstream sem rota/credencial |
| G9 AuthZ/segurança | `PASS` (nenhuma alteração) |
| G10 rollback | `PASS` (params reversíveis; código revertível via git) |
| G11 contratos | `PASS` (nenhum contrato alterado) |
| G12 zero escrita em DELPI | `PASS` (safety check = 0) |

**Predeploy gate global: `FAIL` → cutover produtivo não executado.**

## 9. Flags efetivas

| Flag | Local | Produção |
|---|---|---|
| `PROTHEUS_SUPPLIER_CREATE_ENABLED` | false no serviço (ensaio usou env de processo) | false |
| `PROTHEUS_SUPPLIER_UPDATE_ENABLED` | false no serviço | false |
| `PROTHEUS_REST_EXPECTED_BASE_URL` | `http://192.168.1.233:8701/rest` | `http://192.168.1.231:8061` |
| `INTRANET_PARAMS_AMBIENTE` | 2 | 1 |

## 10. Rollback

- Params: `PATH_AUTH@2`/`URL_REST@1` reversíveis via UPDATE na tabela.
- Código: `git revert` do commit C1 + rebuild `api-delpi`.
- Registro de teste `003884/01` permanece em DELPI_TST01 (mesma política dos
  resíduos `ZZ HOMOLOG E2*`) — cleanup fora do escopo.
- Reversão não desfaz fornecedores já criados; jamais usar DELETE em SA2.

## 11. Residuais

- `linked_customer_code` permanece imutável upstream (handoff E7).
- `linked_customer_store`: sensível à loja — `02` ignorada, `03` 400, `05`
  persistiu (capacidade confirmada; seletividade upstream registrada).
- `state_registration`: exige IE com DV válido do UF (rejeição correta).
- Handoff TOTVS pendente: publicar `delpi/api/v1/suppliers` na `restall`
  produtiva + credencial válida → só então `URL_REST@1` + smoke read-only.
- `E10_VISUAL`/full-stack BFF: ensaio executado nos use cases canônicos (não
  via BFF) — limitação registrada; rota/AuthZ inalteradas por E2–E7.

## 12. Arquivos alterados

- `api-delpi/app/config.py` — `PROTHEUS_REST_EXPECTED_BASE_URL`
- `api-delpi/app/application/services/integrations/protheus_path_resolver.py` — `assert_protheus_write_target`
- `api-delpi/app/application/use_cases/integrations/{create,update}_protheus_rest_supplier_use_case.py` — chamada do guard
- `api-delpi/tests/test_protheus_supplier_{create,update}_use_case.py`, `test_protheus_write_tracker.py`, `test_supplier_change_provenance.py` — fixtures + 2 testes do guard
- `api-delpi/scripts/protheus_supplier_c1_full_assay.py` — **novo** ensaio
- `infra/docker-compose.yml`, `infra/.env.dev.example`, `infra/.env.prod.example`
- `docs/12-roadmap-e-evolucao/supplies/IMPLEMENTATION-PLAN.md`


## 13. Revisão GPT — C1 (2026-10-23)

**Veredito dividido:** `LOCAL_HOMOLOGATION = ACCEPT_WITH_RESIDUAL` conforme evidências reportadas de POST 53/53 e cobertura PUT 51/51 na `DELPI_TST01`; `PRODUCTION_CUTOVER = EXECUTION_DRIFT / BLOCKED` devido a G8 FAIL (rota suppliers 404 e autenticação 401). O GPT revisou o relatório no GitHub; **não reexecutou** REST, SQL, SSH, testes ou deploy. Campos classificados como `UNCHANGED_REQUIRED` não são prova de mudança de valor independente, mesmo quando incluídos na cobertura total 51/51.

**Desvio de execução:** apesar da regra expressa `G8 FAIL => NO DEPLOY`, a execução publicou **somente** a `api-delpi` com a guarda de alvo esperado, sem executar a troca do `URL_REST@1`. Essa publicação parcial precisa ser classificada como **exceção/desvio do gate de deploy**, não PASS do predeploy. O relatório indica containers saudáveis e flags globais CREATE/UPDATE OFF, mas isso não apaga o desvio. Não concluir cutover concluído nem ativação autorizada.

**Segurança:** manter `PROTHEUS_SUPPLIER_CREATE_ENABLED=false` e `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` até verificar com owner TOTVS a publicação da rota no endpoint `192.168.1.231:8061/restall`, credenciais autorizadas, paridade de contrato, destino efetivo `DELPI` e plano operacional de release. O pino produtivo atualmente diverge do parâmetro `URL_REST@1`, resultando em fail-closed no caminho de escrita; isso é estado transitório, não destino produtivo ativo. `GET E14` ainda depende do destino antigo conforme o documento.

**Próxima ação:** handoff objetivo ao Gabriel com URL, paths, respostas HTTP sanitizadas e pergunta sobre instância/serviço de publicação e credencial correta. Após correção upstream, nova pré-verificação read-only G8 e decisão de cutover; não repetir cadastro fictício em produção. Revisar também se o procedimento local homologou o BFF/AuthZ end-to-end: o relatório explicita ensaio por use cases, não fluxo de UI/BFF.


## 14. Estado de espera / handoff entre chats (2026-10-23)

**Decisão PO: aguardar a resposta do Gabriel/TOTVS.** A consolidação canônica com links, SHAs, endpoints, configurações efetivas, evidências, guard, rollback, drifts, tarefas proibidas e checklist de retomada está em [X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md](./X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md). Não tratar esse handoff como GO para mudança de `URL_REST@1` nem para CREATE/UPDATE produtivos. Reancorar HEAD e authorities ao iniciar um novo chat.


## 15. Atualização de comunicação TOTVS — 2026-10-26

Resposta de Gabriel Araújo de **23/10/2026, 16:29**, apresentada pelo PO: **nenhuma mudança foi publicada ainda**; aguarda aprovação. O owner informa reaproveitamento do endpoint REST existente e da configuração; o PO esclareceu que autenticação e configuração também **não serão alteradas**. Gabriel solicita uma janela de manutenção de **30 minutos** para criar campo de controle de alteração do usuário; Michael deverá indicar disponibilidade. Possível alteração posterior da senha pelo configurador não constitui mudança executada.

**Estados atuais de decisão:** `GABRIEL_REPLIED`; `RELEASE_PREPARATION_PENDING`; `MAINTENANCE_WINDOW_PENDING`; `PROD_UPSTREAM_NOT_DEPLOYED`; `G8=FAIL_LAST_OBSERVED`; `PRODUCTION_CUTOVER=BLOCKED`. Os resultados 404/401 de 23/10 são evidência histórica ainda sem reteste; não inferir resolução somente da promessa de reutilização do endpoint. O PO informou que **vai enviar** a resposta ao Gabriel, mas **o envio ainda não foi comprovado**; não registrar como realizado.

**Próxima ação:** após o envio, agendar manutenção com Michael e Gabriel; aprovar escopo técnico do campo e rollback; aguardar publicação TOTVS; reexecutar G8 **read-only** e validar destino real `DELPI`. Manter parâmetros e flags de escrita sem mudança até prova de runtime e autorização específica. A atualização **não é GO para POST/PUT produtivo ou mudança de configuração**. Para handoff operacional, consultar [X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md](./X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md).

## 16. R3 — Readiness autorizada pelo PO (2026-10-26)

`PO_AUTHORIZED_FULL_MINHA_DELPI_READINESS`: preparar produção completa
(amb=1 → `192.168.1.231:8061` + `/restall` nos paths + flags ON), sem
aguardar a publicação do Gabriel — 401/404 upstream = `UPSTREAM_PENDING`.

### Resultado: `EXECUTION_DRIFT` (contrato real incompatível)

- `CONTEUDO varchar(30)` verificado no schema real; params amb=1 ≡ amb=2.
- Layout requerido (pin compara `base_url` exato = origem):
  `URL_REST@1=http://192.168.1.231:8061` (25c ✓),
  `PATH_AUTH@1=/restall/api/oauth2/v1/token` (28c ✓),
  `PATH_SUPPLIERS@1=/restall/delpi/api/v1/suppliers` (**31c ✗**).
- Nenhum split base/path válido; prefixo `/restall` é obrigatório
  (`POST /restall/...token` → 400 vivo; `POST /...token` na raiz → 404).
- **Nada aplicado**: flip parcial quebraria E14; flags OFF (condição de
  segurança não demonstrável); nenhum POST/PUT real executado.
- Resoluções possíveis: DDL `varchar(50)` (DBA/owner), param `BASE_PATH`
  no resolver (api-delpi), ou raiz upstream curta (`/rest` caberia exato).
- `.env.prod.example` alinhado: pin documenta a origem sem `/restall`.

Estado: `CONFIG_READY=PREPARED`, `CREATE/UPDATE=OFF(prepared)`,
`DEPLOY=n/a (sem mudança)`, `UPSTREAM=PENDING`, `END_TO_END=INCONCLUSIVE`.


## 17. R4 — BASE_PATH aplicado e habilitação CREATE/UPDATE (2026-10-26)

Execução da opção `BASE_PATH` (decisão arquitetural do PO em R4), commit `cd50b85610`:

- **Resolver**: `OPTIONAL_PARAM_KEYS=("BASE_PATH",)`; loader passa a selecionar
  chaves opcionais; prefixo composto em memória **após** a resolução semântica
  de labels; dedup segment-aware; fail-closed em valor inválido; `base_url`
  preservado como origem pura (pin exato inalterado).
- **Params amb=1 (transação atômica)**: `URL_REST=http://192.168.1.231:8061`,
  `INSERT BASE_PATH=/restall`, PATH_AUTH/PATH_SUPPLIERS idênticos; amb=2
  intocado (`URL_REST` TST, sem `BASE_PATH`).
- **Runtime provado**: `auth_url=…/restall/api/oauth2/v1/token`,
  `suppliers_base_url=…/restall/delpi/api/v1/suppliers/`,
  `assert_protheus_write_target=PASS`.
- **Flags**: `PROTHEUS_SUPPLIER_CREATE_ENABLED=true`,
  `PROTHEUS_SUPPLIER_UPDATE_ENABLED=true` (`.env` + env do container;
  backup `infra/.env.bak.x4-r4-20261026`).
- **Deploy**: `up-prod-sequential.sh --build api-delpi` @ `cd50b8561`,
  container `Up (healthy)`; `delpi-supplies-api` saudável; logs limpos
  (único erro = 401 de auth upstream esperado).
- **Testes**: 610/610 focados (protheus/supplier/integration) + 10 casos
  novos de BASE_PATH.
- **Upstream**: token route responde **401** (rota viva, credencial/rota de
  suppliers não publicada) → `UPSTREAM_PENDING`; `END_TO_END=INCONCLUSIVE`.
- **Nenhum POST/PUT real executado**; primeira escrita exige autorização
  operacional distinta.
- **Rollback**: UPDATE reversível de `URL_REST@1` + `DELETE BASE_PATH@1`;
  flags via restore do `.env` + redeploy; código via `git revert`.
