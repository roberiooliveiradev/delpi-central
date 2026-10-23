# HANDOFF CANÔNICO — Portal Suprimentos / X4.PROD-C1 — Aguardando Gabriel
**Atualizado em:** 2026-10-23  
**Status:** `WAITING_ON_TOTVS_OWNER` — `PRODUCTION_CUTOVER = EXECUTION_DRIFT / BLOCKED` (`G8 = FAIL`)  
**Responsável pela dependência externa:** Gabriel Araújo / TOTVS — disponibilizar rota e autenticação REST de fornecedores produtiva.  
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
**A resposta de Gabriel ainda não consta das evidências deste handoff.** Não alegar que um e-mail foi enviado automaticamente; o assistente apenas redigiu uma mensagem no chat.

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
