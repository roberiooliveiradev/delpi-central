# HANDOFF CANÔNICO — Portal Suprimentos / X4.PROD-C1 — Resposta Gabriel e preparação do release
**Atualizado em:** 2026-10-26  
**Status:** `CONFIG_READY (R4)` — drift R3 resolvido via `BASE_PATH` (§14); amb=1 → REST produtiva, CREATE/UPDATE=ON, guard PASS. `UPSTREAM_PENDING`: token 401 até Gabriel provisionar credencial/API (janela Michael por confirmar). `END_TO_END = INCONCLUSIVE`  
**Responsável pela publicação upstream:** Gabriel Araújo / TOTVS — aplicar mudança na instância produtiva após aprovação e janela operacional. Endpoint, autenticação e configuração existentes serão reutilizados, conforme resposta do owner.  
**Decisão PO neste chat:** registrar e **aguardar a resposta do Gabriel**; não executar novos flips, POST/PUT produtivos ou ativação de flags enquanto o bloqueio estiver aberto.

> **LEIA ESTE ARQUIVO PRIMEIRO EM NOVO CHAT.** Este é um handoff operacional do C1; não substitui a hierarquia de authority, os ADRs, o código no HEAD ou o [relatório C1](./X4-PROD-C1-SUPPLIER-PRODUCTION-REST-CUTOVER.md). Reancorar HEAD, git status, regras `.cursor`, contratos e runtime antes de qualquer ação.

## 1. Objetivo original e fronteira
Objetivo: **produção cadastrar fornecedores reais na base `DELPI` por REST produtiva**, enquanto **desenvolvimento/homologação testa em `DELPI_TST01`**. A listagem produtiva continua consultando `DELPI` via SQL `api-delpi`. Fluxo: `plugins/supplies → supplies-api → api-delpi → Protheus`. O PO solicitou **POST e PUT completos apenas em homologação local antes de deploy**, sem ensaio de escrita em `DELPI`.

**Não confundir:** (a) o host/container produtivo, (b) `AMBIENTE=1` na tabela de parâmetros, (c) a base efetiva à qual a REST escreve. Antes do cutover, o runtime produtivo utiliza `AMBIENTE=1`, mas `URL_REST@1` permanece apontando à REST de **teste**; isso é estado legado/transitório intencionalmente preservado para não quebrar E14 enquanto G8 falha. A guarda adicional de escrita mantém FAIL-CLOSED.

## 2. Âncoras Git e docs
- Implementação C1 de guard: `5b21b2545d` (referência informada no execution report).
- Relatório/ensaio C1: `a11b53269f` (commit de execução reportado).
- Revisão arquitetural GPT de C1: `3ba53769d213a38eab0effc31f5df42f06ca7107`.
- Outros baselines: E2 `12a142877d` (POST em TST), E3 `8fb120f25a` (53 POST + frontend), E5 `2808ceb9ce` (PUT parcial homologado), E6 `5747665a84` (catálogos/PUT condicionado), E7 `e8a86cb338` (helps), S10 `bf3db64c8e` (hierarquia UX).
- Documento técnico detalhado com tabelas de evidências: [X4-PROD-C1-SUPPLIER-PRODUCTION-REST-CUTOVER.md](./X4-PROD-C1-SUPPLIER-PRODUCTION-REST-CUTOVER.md).
- [IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md), [README.md](./README.md).
- **SHAs históricos não definem HEAD atual.** Não sobrescrever mudanças de outras frentes.

## 3. Topologia comprovada e situação exata
| Ambiente/uso | Configuração | Evidência/estado |
|---|---|---|
| Local/dev | `INTRANET_PARAMS_AMBIENTE=2`, REST `http://192.168.1.233:8701/rest` | `PROVEN` — operações reais atingiram `DELPI_TST01` |
| SQL homologação | `DELPI_TST01` | Read-after-write independente |
| Produção — endpoint informado por Gabriel (e-mail 21/10/2026) | `http://192.168.1.231:8061/restall` | URL informada pelo owner; API de fornecedores **NÃO funcional nos probes C1** |
| Produção — parâmetros realmente resolvidos | `AMBIENTE=1` ainda resolve `192.168.1.233:8701` (TST) | Mantido para não quebrar o GET E14; **não é cutover produtivo** |
| Produção — pin seguro implantado | `PROTHEUS_REST_EXPECTED_BASE_URL=http://192.168.1.231:8061` | Diferente do parâmetro resolvido → **write fail-closed** |
| Produção — consultas/listagem E13 | SQL `DELPI` | Não alterado |
| Produção — base final desejada para POST/PUT | `DELPI` | `PENDING`, **não verificado por escrita**, destino real depende de validação owner/runtime |

**Cuidado técnico:** configuração `PARAMETROS_MINHADELPI` em `IntranetDelpiDev` é multiambiente: `AMBIENTE=1` produção, `AMBIENTE=2` homologação; `URL_REST`, `PATH_AUTH`, `PATH_SUPPLIERS`. `CONTEUDO` tem `varchar(30)`, portanto a URL de 35 caracteres `http://192.168.1.231:8061/restall` não cabe inteira. Solução prevista: **origem** em `URL_REST`, prefixo `/restall` nos paths, seguindo o resolver/contrato verificados; não truncar URL nem alterar schema por conveniência.

## 4. O que passou em homologação (executor-reported)
- Script versionado: `api-delpi/scripts/protheus_supplier_c1_full_assay.py`.
- `POST` criou o fornecedor de teste **`003884/01`**, CNPJ fictício **`98887766030041`**, em `DELPI_TST01`; `53/53` campos de inclusão reportados `PERSISTED`; código/loja retornados pelo upstream; GET/SQL reconciliados; tracking `CONFIRMED`.
- `PUT` cobriu as **51 chaves técnicas da allowlist**; 42 alterações diretas e retestes com valores válidos para IE, forma de pagamento, loja de cliente vinculado e risco; **5 campos de coerência ficaram `UNCHANGED_REQUIRED`**. Portanto `51/51` **não significa 51 mudanças independentes de valor**. Código do cliente vinculado (`A2_CLIENTE`) segue imutável no contrato PUT testado (Gabriel/TOTVS pendente).
- IE inválida, forma de pagamento inexistente e loja inválida foram corretamente rejeitadas/ignoradas até usar valores válidos; não usar essas rejeições para inferir defeito da `api-delpi`.
- Tracking: create confirmado, seis updates confirmados, duas rejeições e duas operações `RECONCILIATION_REQUIRED` reportadas; revisar o ledger antes de inferir conclusão global. Testes `api-delpi` escopo supplier **492 PASS**, 1 falha DAVI pré-existente fora do escopo, de acordo com executor.
- A cobertura ocorreu nos **use cases canônicos**, não demonstrou o caminho autenticado `MFE → BFF → API` ponta a ponta; registrar residual.
- Ensaio TST deixou registro `003884/01`; limpeza exige owner/procedimento aprovado. Sem DELETE/UPDATE SQL direto.
- O relatório registrou `delpi_residue_count=0` para registros de ensaio; **não é prova universal de zero alterações fora daquele escopo**.
- **O GPT não reexecutou** REST, SQL, SSH, tests ou Docker; evidências acima são do execution report.

## 5. Bloqueio específico G8 (probes read-only)
Em `http://192.168.1.231:8061/restall`:
- `GET /restall/` → **200** (serviço vivo).
- `GET /rest/` → **404** (base path incorreto na instância produtiva).
- Rota `/restall/delpi/api/v1/suppliers` e variantes testadas → **404** (API de fornecedores ausente / rota divergente).
- Rota de token respondeu, mas credencial técnica atualmente configurada obteve **401**.
- Resultado: **`G8 = FAIL`**, `PRODUCTION_REST_AUTH = FAIL`, `PRODUCTION_SUPPLIER_ROUTE = FAIL`, `PRODUCTION_CUTOVER = BLOCKED`.
- Evitar afirmar que 401/404 provam definitivamente que nenhum deploy upstream existe: pedir o path, a publicação e o provisionamento corretos ao owner.

### Perguntas enviadas/preparadas ao Gabriel
1. A API `delpi/api/v1/suppliers` foi publicada na instância REST `192.168.1.231:8061/restall`? Qual a rota completa válida e sua versão?
2. Qual a rota de token produtiva e como provisionar/validar credencial técnica autorizada sem compartilhar segredo por e-mail?
3. Confirmar destino produtivo `DELPI`, empresa/filial e paridade de retorno código/loja e campos POST/PUT com homologação.
4. Há divergência contratual da operação de alteração de `A2_CLIENTE`? Trata-se de handoff separado, **não confundir com bloqueio G8**.
**Atualização 2026-10-26:** resposta recebida (e-mail de Gabriel em 2026-10-23); ver seção 11. Este parágrafo registra a situação histórica anterior. Não alegar que um e-mail foi enviado automaticamente; o assistente apenas redigiu uma mensagem no chat.

## 6. Estado PROD depois da execução C1 — exceção de deploy
- `api-delpi` foi **rebuildada e publicada em `srv-api`** com a nova guarda `assert_protheus_write_target` e pin para o endpoint produtivo, apesar de `G8=FAIL`.
- O comando/deploy foi reportado como saudável: container `Up (healthy)`, `/health` 200. Não reexecutado pelo GPT.
- **Execução fora da condição estabelecida:** o brief pedia `G8 FAIL → NO DEPLOY`. Registrar **`EXECUTION_DRIFT`** do deploy parcial, sem confundir com cutover.
- `URL_REST@1` **NÃO** foi trocado; permanece TST para GET E14. A escrita permanece bloqueada também pelo **mismatch do pin**.
- `PROTHEUS_SUPPLIER_CREATE_ENABLED=false`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=false` **confirmados no relatório**; manter OFF. Nenhuma permissão nova.
- **Não tentar resolver trocando só as flags**; não fazer POST/PUT produtivo, nem escrever direto em `PARAMETROS_MINHADELPI` sem procedimento aprovado.

## 7. Condição de pausa — o que NÃO fazer enquanto se aguarda
- Não alterar `URL_REST@1` para 231:8061 antes de G8 PASS; E14 pode perder GET.
- Não ativar `CREATE` ou `UPDATE`.
- Não cadastrar fornecedor fictício em `DELPI`; não repetir testes destrutivos em produção.
- Não desabilitar o guard, omitir pin ou fazer fallback silencioso a TST.
- Não executar SQL write direto em SA2, nem alterar Protheus/MATA020 fora do owner.
- Não tratar deploy/GET 200 como prova de persistência produtiva.
- Não iniciar cutover só por existir URL informada em e-mail.

## 8. Retomada quando Gabriel responder — CHECKLIST OPERACIONAL
**Primeiro:** ler este handoff + C1, obter `git fetch`, HEAD, git status, authorities, config e runtime atual; checar se novas mudanças afetaram `api-delpi`, `supplies-api`, Core ou manifest. Não confiar em SHA histórico como HEAD.

**Fase R1 (read-only, sem escrita):**
1. Conferir a resposta escrita do owner, rota suppliers, URL base, OAuth/token, escopo e provisionamento secreto via canal seguro.
2. Fazer probes produtivos **somente GET/status/autenticação autorizada**, sem expor segredo; confirmar 2xx esperado no path correto; obter fornecedor real conhecido e correlacionar GET da REST com `DELPI.SA2010` (código/loja/empresa).
3. Verificar se POST retorna código+loja **por contrato/ambiente compatível**, sem POST em produção; confirmar autorização, tracking, proteção de identidade e compatibilidade com 53 POST/51 allowlist PUT.
4. Se G8 ainda FAIL: manter pausa, documentar nova evidência, nova pergunta ao Gabriel e **não** mudar params/gates.

**Fase R2 (configuração/cutover, só após G8 PASS e GO operacional):**
5. Revalidar tamanho de `CONTEUDO` e resolver final de paths; backup/snapshot sanitizado dos parâmetros vigentes; plan de rollback e owners da alteração.
6. Atualizar **somente parâmetros de `AMBIENTE=1`** pelo procedimento autorizado, sem afetar amb=2 nem listagem SQL `DELPI`; verificar pin/URL efetiva após restart.
7. Smoke read-only E14, BFF, Core AuthZ positiva/negativa, supplier GET, health e tracking; rollback se houver regressão. Preservar credenciais fora do repo.
8. **A ativação das flags é outro gate:** revisar risco, owner, autorização explícita e plano de primeira escrita real; preferir `CREATE` antes de `UPDATE`. Não realizar primeiro cadastro real automaticamente por este handoff.

**Critério de conclusão C1:** `G8=PASS`, `amb=1` resolve **prod 231:8061**, `amb=2` resolve **TST 233:8701**, nenhum fallback cruzado, GET E14 preservado, deploy saudável, rollback pronto e **flags de escrita conforme GO autorizado**.

## 9. Texto inicial para novo chat
> Você é o chat de Architecture/Coordination do Portal Suprimentos. Reancore no HEAD e nas authorities. Leia `docs/12-roadmap-e-evolucao/supplies/X4-PROD-C1-HANDOFF-AGUARDANDO-GABRIEL-20261023.md` e `X4-PROD-C1-SUPPLIER-PRODUCTION-REST-CUTOVER.md`. Estamos **PAUSADOS aguardando Gabriel/TOTVS**: homologação `DELPI_TST01` POST 53/53 e PUT allowlist 51/51 (5 unchanged-required) reportada; G8 produção FAIL (suppliers 404/token 401 na REST 231:8061/restall); prod `URL_REST@1` ainda aponta TST para GET E14; guard pin 231:8061 cria mismatch e bloqueia write; flags CREATE/UPDATE OFF. Houve deploy parcial `api-delpi` apesar de G8 FAIL, classificado `EXECUTION_DRIFT`. **Não executar cutover/escrita até resposta do Gabriel, G8 read-only PASS e autorização operacional.** Quando eu trouxer a resposta, faça inventário e prepare o próximo menor passo.

## 10. Estado formal resumido
```text
X4.PROD-C1.LOCAL_ASSAY       = ACCEPT_WITH_RESIDUAL (executor-reported)
X4.PROD-C1.G8               = FAIL
X4.PROD-C1.PRODUCTION       = EXECUTION_DRIFT / BLOCKED
X4.PROD-C1.DEPLOY_PARTIAL   = EXECUTION_DRIFT (api-delpi guard only)
X4.PROD-C1.GABRIEL_REPLY    = PENDING
PROD_REST_URL_ACTUAL        = ambiente:1 -> TST REST 233:8701
PROD_REST_URL_TARGET        = ambiente:1 -> PROD REST 231:8061/restall
LOCAL_REST_URL_ACTUAL       = ambiente:2 -> TST REST 233:8701
PROD_CREATE_GATE           = OFF
PROD_UPDATE_GATE           = OFF
NEXT_STEP                  = WAIT_FOR_GABRIEL -> G8_READ_ONLY_RECHECK
```


## 11. Retomada — resposta de Gabriel recebida (2026-10-26)

**Fonte:** e-mail apresentado pelo PO, enviado por Gabriel Araújo em **23/10/2026 às 16:29**, assunto «Re: API Fornecedor X MinhaDelpi». Estado comunicado pelo owner, não evidência de execução técnica.

- Gabriel **não aplicou alterações em produção**: aguarda aval da equipe.
- Segundo o alinhamento confirmado pelo PO, **endpoint, autenticação e configuração existentes permanecem os mesmos**; não solicitar nova rota, não pressupor alteração de caminho de token ou troca de credencial para este release. A mensagem do Gabriel declara explicitamente o reaproveitamento da configuração e a ausência de necessidade de novo endpoint REST.
- Gabriel perguntou se os testes podem ser considerados concluídos: o PO pode confirmar **a homologação POST/PUT em DELPI_TST01 no escopo documentado**, sem declarar os gates de runtime produtivo aprovados.
- Gabriel solicita **janela de manutenção de 30 minutos**, disponibilidade a coordenar com Michael, para criar campo de controle de alteração do usuário e realizar publicação.
- Michael poderá alterar posteriormente a senha do usuário pelo configurador; **não significa que a senha tenha sido alterada**.
- **E-mail de resposta do PO:** intenção de envio informada em 26/10/2026; **ENVIO NÃO CONFIRMADO** neste registro. Não afirmar aceite recebido pelo Gabriel, janela agendada ou deploy executado.

### Estado operacional e decisão

`GABRIEL_REPLY=RECEIVED`; `TST_HOMOLOGATION=ACCEPT_WITH_RESIDUAL` (ensaios reportados); `PRODUCTION_UPSTREAM_CHANGE=PENDING`; `MAINTENANCE_WINDOW=PENDING_MICHAEL`; `G8=FAIL_LAST_OBSERVED / RECHECK_PENDING`; `PRODUCTION_CUTOVER=BLOCKED`; `CREATE/UPDATE=OFF` (último estado reportado, revalidar no runtime).

**Atenção à divergência histórica:** o diagnóstico C1 de 23/10 observou suppliers 404 e token 401 na REST produtiva. O esclarecimento de que a configuração será mantida **não apaga** tais evidências nem prova que a rota já esteja operante. Não alterar `URL_REST@1`, `PATH_AUTH`, `PATH_SUPPLIERS` ou secrets com base exclusivamente no e-mail. O campo novo deve ter nome, semântica e impacto no contrato confirmados no procedimento do owner antes da publicação.

### Próximos passos limitados

1. PO envia confirmação de conclusão da homologação em `DELPI_TST01`, alinhamento de reutilização do endpoint/config/auth e pedido de definição da janela com Michael; registrar o envio **somente após evidência**.
2. Michael confirma janela, Gabriel especifica campo de controle de alteração, plano de mudança/rollback e realiza publicação upstream sob aprovação operacional.
3. Depois da publicação: reancorar HEAD/config/runtime e reexecutar **G8 read-only** (rota válida, token com credencial autorizada já provisionada, GET fornecedor existente, destino `DELPI`, saúde/E14) sem POST/PUT em produção.
4. Se G8 PASS, solicitar **GO separado** para cutover da configuração `AMBIENTE=1` apenas se a verificação demonstrar necessidade real; preservar `AMBIENTE=2`, GET E14, pin de escrita e rollback.
5. **Habilitação de CREATE/UPDATE e primeira escrita real requerem autorização operacional distinta**, não decorrente deste e-mail.

Os registros históricos acima permanecem intactos como evidência do diagnóstico anterior; esta seção é a atualização cronologicamente posterior e prevalece para o estado de comunicação.


## 12. Confirmação enviada e janelas propostas — 2026-10-26

**Evidência apresentada pelo PO:** captura da conversa Outlook com resposta enviada em **26/10/2026 às 07:38** a Gabriel Araújo (Michael em cópia). O PO confirmou conclusão da homologação em DELPI_TST01, reutilização de endpoint/autenticação/configuração existentes, concordância em preparar a publicação sob janela de 30 minutos; pediu a especificação do campo de controle de alteração.

**Resposta de Michael (captura apresentada em 26/10):** janelas **12h–13h** ou **qualquer horário após 17h30**. **São disponibilidades, não agendamento confirmado nem implantação executada.** Falta selecionar horário com Gabriel/Michael e obter GO de operação.

**Decisão operacional solicitada pelo PO:** deixar a integração produtiva pronta e, caso a configuração efetiva de AMBIENTE=1 ainda aponte a REST de teste, trocar **condicionalmente** para produção. Isso **não dispensa** validar primeiro G8 read-only após publicação upstream. Até G8 PASS, manter URL_REST@1 intacta por risco de quebrar GET E14; manter AMBIENTE=2 isolado, gates CREATE/UPDATE OFF, pin fail-closed e rollback pronto. A alteração efetiva dos parâmetros deve ser executada apenas no momento controlado com owner e janela/GO confirmados; não inferir que já ocorreu a partir deste registro.

**Estado atualizado:** `PO_EMAIL_SENT=PROVEN_BY_SCREENSHOT`; `MICHAEL_WINDOWS=OFFERED`; `WINDOW_CONFIRMED=PENDING`; `GABRIEL_DEPLOY=PENDING`; `G8=FAIL_LAST_OBSERVED`; `CONFIG_CUTOVER=PENDING_CONDITIONAL`; `CREATE/UPDATE=OFF_LAST_REPORTED`.


## 13. X4.PROD-C1.R3 — Readiness autorizada pelo PO (2026-10-26)

**Decisão PO:** `PO_AUTHORIZED_FULL_MINHA_DELPI_READINESS` — apontar amb=1 para a REST produtiva, habilitar CREATE/UPDATE e deixar a Minha DELPI pronta, aceitando 401/404 upstream como `UPSTREAM_PENDING` enquanto Gabriel publica.

### Evidências novas (read-only, executadas)

- Container `delpi-api-delpi`: `INTRANET_PARAMS_AMBIENTE=1`, `PROTHEUS_REST_EXPECTED_BASE_URL=http://192.168.1.231:8061`, `CREATE/UPDATE=false` (estado preservado).
- Schema real: `CONTEUDO varchar(30)` **confirmado** (INFORMATION_SCHEMA); tabela tem apenas `ID, AMBIENTE, PARAMETRO(varchar 20), CONTEUDO`.
- Params atuais: amb=1 ≡ amb=2 → `URL_REST=http://192.168.1.233:8701/rest` (30c), `PATH_AUTH=/api/oauth2/v1/token` (20c), `PATH_SUPPLIERS=/delpi/api/v1/suppliers` (23c).
- Probes produtivos: `GET /restall/` → 200; `POST /restall/api/oauth2/v1/token` → **400** (rota viva — auth existe); `POST /api/oauth2/v1/token` → 404 (raiz **não** serve); suppliers → 404 (`UPSTREAM_PENDING` — API não publicada).
- Guard/resolver: 47/47 testes focados verdes no container deployado.

### EXECUTION_DRIFT material — varchar(30)

`URL_REST` só pode ser a origem (`http://192.168.1.231:8061`, 25c — exigido pelo pin exato), logo `/restall` deve entrar nos paths:

| Param | Valor requerido | Len | Cabe? |
|---|---|---|---|
| `URL_REST@1` | `http://192.168.1.231:8061` | 25 | ✓ |
| `PATH_AUTH@1` | `/restall/api/oauth2/v1/token` | 28 | ✓ |
| `PATH_SUPPLIERS@1` | `/restall/delpi/api/v1/suppliers` | **31** | **✗ (1 char a mais)** |

Não existe split válido (join `base/path` insere `/`; raiz do 8061 não serve rotas — provado). Flip parcial de amb=1 quebraria o GET E14. **Troca é atômica: nada foi alterado; amb=1 segue TST; flags seguem OFF.**

### Opções de desbloqueio (decisão owner/arquiteto)

1. **DDL**: `CONTEUDO varchar(30 → 50)` em `IntranetDelpiDev.dbo.PARAMETROS_MINHADELPI` (compatível p/ leitura; exige DBA/owner — tabela compartilhada com a Intranet).
2. **Resolver**: param opcional `BASE_PATH` (ex.: `/restall`) prefixando `PATH_AUTH`/`PATH_SUPPLIERS` — evolução de contrato em `protheus_path_resolver` (api-delpi, backward-compatible).
3. **Upstream (Gabriel)**: publicar sob raiz mais curta. Se existir alias `/rest` (ex.: `http://192.168.1.231:8061/rest` = **30c exatos**), **nenhuma** linha de path muda — mesma estrutura do TST; só `URL_REST@1` troca host.

### Preparado (não executado)

```sql
-- EXECUTAR SOMENTE APÓS DESBLOQUEIO varchar(30):
-- amb=1 → URL_REST=http://192.168.1.231:8061
--         PATH_AUTH=/restall/api/oauth2/v1/token
--         PATH_SUPPLIERS=/restall/delpi/api/v1/suppliers  -- 31c NÃO CABE hoje
-- Flags (.env api-delpi): PROTHEUS_SUPPLIER_CREATE_ENABLED=true
--                         PROTHEUS_SUPPLIER_UPDATE_ENABLED=true
```

**Flags permanecem OFF**: condição de segurança (destino resolvido = REST produtiva, sem fallback TST) não demonstrável enquanto amb=1 resolve TST. `.env.prod.example` corrigido: pin agora documenta origem pura `http://192.168.1.231:8061` (sem `/restall`).

```text
X4.PROD-C1.R3.CONFIG_READY    = PREPARED_NOT_APPLIED (varchar drift)
X4.PROD-C1.R3.CREATE_ENABLED  = OFF (prepared)
X4.PROD-C1.R3.UPDATE_ENABLED  = OFF (prepared)
X4.PROD-C1.R3.UPSTREAM        = UPSTREAM_PENDING (suppliers 404; token vivo)
X4.PROD-C1.R3.END_TO_END      = INCONCLUSIVE
NEXT_STEP                     = DECISAO varchar(30) → depois G8 recheck
```


## 14. X4.PROD-C1.R4 — BASE_PATH aplicado, cutover de parâmetros e flags ON (2026-10-26)

**Decisão arquitetural executada:** opção 2 do §13 — parâmetro opcional `BASE_PATH` no resolver (`api-delpi`), commit `cd50b85610`. `varchar(30)` contornado **sem** DDL: `BASE_PATH=/restall` (8c) prefixa os paths efetivos em memória; `URL_REST` permanece a origem pura (pin do guard segue exato).

### Resolver (backward-compatible)

- `OPTIONAL_PARAM_KEYS=("BASE_PATH",)` — loader faz SELECT das chaves opcionais junto às obrigatórias; ausente/vazio = comportamento idêntico ao legado.
- Prefixo aplicado **após** a resolução semântica de labels (auth/suppliers), com dedup segment-aware (`/restall` não confunde com `/rest`), normalização de barras e fail-closed em valores inválidos (`..`, `//`, scheme, whitespace).
- `config.base_url` não incorpora o prefixo → `assert_protheus_write_target` compara origem exata, sem mudança de contrato do guard.
- Testes: 10 novos casos no resolver + regressão **610/610** verdes (suíte protheus/supplier/integration).

### Configuração efetiva (transação atômica, 2026-10-26)

| Param | amb=1 antes | amb=1 depois | amb=2 (intocado) |
|---|---|---|---|
| `URL_REST` | `http://192.168.1.233:8701/rest` | `http://192.168.1.231:8061` | `http://192.168.1.233:8701/rest` |
| `BASE_PATH` | — | `/restall` (INSERT) | — |
| `PATH_AUTH` | `/api/oauth2/v1/token` | idem | idem |
| `PATH_SUPPLIERS` | `/delpi/api/v1/suppliers` | idem | idem |

**Resolução runtime comprovada** (in-container, read-only):
`base_url=http://192.168.1.231:8061` · `auth_url=…/restall/api/oauth2/v1/token` · `suppliers_base_url=…/restall/delpi/api/v1/suppliers/` · `label_mismatch=false` · **`assert_protheus_write_target: PASS`** (pin `PROTHEUS_REST_EXPECTED_BASE_URL` idêntico à origem).

### Flags efetivas

`PROTHEUS_SUPPLIER_CREATE_ENABLED=true`, `PROTHEUS_SUPPLIER_UPDATE_ENABLED=true` no `.env` (backup `infra/.env.bak.x4-r4-20261026`), confirmadas no env do container `delpi-api-delpi` após deploy `--build api-delpi` (SHA `cd50b8561`, `Up (healthy)`).

### Estado upstream e aceite

- `configuration=ok`; probe de status → **HTTP 401** em `/restall/api/oauth2/v1/token` → `authentication=failed`, `connection=unavailable` = **`UPSTREAM_PENDING`** (rota viva; credencial ainda não provisionada/publicação do Gabriel pendente — janela Michael por confirmar).
- E13 (lista de fornecedores = SQL `DELPI`): inalterado e saudável. E14 (detalhe REST): indisponibilidade específica aceita pelo PO enquanto `UPSTREAM_PENDING`.
- BFF `supplies-api` `Up (healthy)`; api-delpi servindo 2xx; único erro nos logs = o 401 de auth esperado.
- **Nenhum POST/PUT real executado.** Se a API for publicada pelo Gabriel, a primeira escrita exige autorização operacional distinta + reconciliação.

### Rollback

- Params: `UPDATE amb=1 URL_REST → http://192.168.1.233:8701/rest` + `DELETE BASE_PATH@amb=1` (snapshot pré-flip no corpo desta seção e R3).
- Flags: restaurar `infra/.env` a partir de `infra/.env.bak.x4-r4-20261026` + redeploy `api-delpi`.
- Código: `git revert cd50b85610` + deploy canônico.

```text
X4.PROD-C1.R4.CONFIG_READY    = PASS
X4.PROD-C1.R4.CREATE_ENABLED  = PASS
X4.PROD-C1.R4.UPDATE_ENABLED  = PASS
X4.PROD-C1.R4.TARGET_GUARD    = PASS (fail-closed, pin exato)
X4.PROD-C1.R4.AUTHZ/TRACKING  = UNCHANGED
X4.PROD-C1.R4.UPSTREAM        = UPSTREAM_PENDING (token 401; suppliers não probeado — auth pré-requisito)
X4.PROD-C1.R4.END_TO_END      = INCONCLUSIVE
NEXT_STEP                     = Gabriel publica API + credencial válida → G8 read-only recheck → GO separado p/ 1ª escrita
```
