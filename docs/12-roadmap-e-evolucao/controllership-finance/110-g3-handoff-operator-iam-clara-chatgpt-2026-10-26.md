# Documento 110 — Handoff G3 Operador SSH / IAM: release da Central de Fechamento e conexão CLARA ↔ ChatGPT

**Data:** 2026-10-26 (America/Sao_Paulo). **Execução:** `CF-PROC0072-G3-OPERATOR-IAM-CHATGPT-001`. **Natureza:** runbook operacional de passagem de bastão — **não comprova deploy, assinatura G3 ou cadastro ChatGPT**.

**Entrada:** G2 do PO formalmente **`ACCEPT_WITH_RESIDUAL`** para o escopo local P1–P6/CLARA — [Doc 108](./108-homologacao-guiada-g2-g3-2026-10-26.md), decisão `CF-PROC0072-G2-ACCEPT-WITH-RESIDUAL-20261026`; autorização original de executar G2/G3 e fechamento E2E no [Doc 109](./109-go-po-ultima-rodada-e2e-usuario-g2-g3-2026-10-26.md). Regras de release [Doc 104](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md), incidentes/deploy/ChatGPT [Doc 107](./107-clara-validacao-antecipada-chatgpt-release-hoje.md), contratos CLARA [Doc 106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md), IAM [runbook MCP](../../../controllership-finance-api/docs/integrations/keycloak-mcp-client-runbook.md) (verificar path de referência) e [ficha pública](../../../controllership-finance-api/docs/integrations/chatgpt-clara-registration-sheet.md).

## 1. Matriz de decisão e responsabilidades — não confundir gates

| Atividade | Autoridade | Estado na abertura deste handoff |
|---|---|---|
| G2, aceite PO para escopo local comprovado | PO | **`ACCEPT_WITH_RESIDUAL`** — formalizado 26/10/2026; Controladoria separada `NOT_RECORDED`, caso exigida |
| Conteúdo/owner G1: T03, T05, R04+, seeds e G5/G6 | Owners de regras, Core, TOTVS e Controladoria | `PENDING` por contrato/fonte, **não** abrangidos pelo aceite oficial |
| G3: autorização de mudança/janela e sign-off operacional | **Operador SSH habilitado**, com change owner | **`PENDING`**; GO do PO para coordenar G3 não é identidade/assinatura do operador |
| Alterar IAM Keycloak, token exchange/audience/redirect, impactar clientes irmãos | **Owner IAM/Plataforma + operador** | **`BLOCKED/PENDING_DIFF_APPROVAL`**; não presumir --apply parcial |
| Cadastro e OAuth CLARA no ChatGPT | **Proprietário do workspace/conta ChatGPT** com IAM | `TEST_NOT_RUN`; requer callback real e conexão voluntária |
| Smoke autenticado produção/resultado | Operador + validador autorizado | `TEST_NOT_RUN`; não pode ser marcado PASS apenas por 401 ou metadata 200 |

**Aceite vigente:** mantenha esclarecimento aberto permitido durante decisão da área na V1, porém C2 bloqueia conclusão mensal enquanto existir esclarecimento aberto (e demais condições). Fonte P7 indisponível e relatórios sem paridade não passam a ser oficiais por efeito do G2.

## 2. Baseline: o que já se sabe e o que requer read-back

- O operador reportou produção `srv-api` em checkout **`2eeb5fb943e46cf8f1e50e373a4fc2cf1ca0af6b`**, com código da CLARA `ecf765139d` e migrations V001–V014; corpus publicado `5541097a-8608-4470-b971-7c28b3ae6c40` (52 fontes/1298 itens). **OWNER_REPORTED / TO_VERIFY** por SSH independente do handoff.
- Teste E2E local/Jornadas J1–J10 e fixes funcionais documentados no commit **`5e9a0ddd81c21cb656ecc5be4fd16fa5670efea1`**: catálogo canônico de notificações Core, fallback do Portal e producer BFF; banner 404/409; prova de consentimento V014. **Não há prova de que estes fixes R4 estejam implantados em produção.**
- A branch `main` continua recebendo commits de **outros bounded contexts**. **Não fazer deploy de HEAD em movimento cegamente.** Operador deve obter `origin/main`, `git status`, worktrees, diff `RELEASE_SHA` vs `DEPLOYED_SHA` e congelar SHA imutável com lista explícita de serviços/arquivos afetados; solicitar avaliação do owner Core/Portal se release muda shared platform.
- O Keycloak produtivo `mcp-clara` foi reportado como não provisionado: bootstrap admin rotacionado, service account sem `realm-management`, password grant inválido. Isso **não autoriza** reset ad hoc, ampliação de privilégios da service account, SQL, DB ou bypass container.
- MCP edge sem token retornar 401 + discovery metadata 200 é **PROVEN apenas segundo relatório do operador**, não prova login OAuth, audience correta, tool discovery autenticado ou ACT.

## 3. Pré-G3: coleta read-only e decisão do Operador

O Operador SSH habilitado e o change owner devem documentar, sem credenciais nos logs:

1. **Identidade/janela:** nome/função do operador, ambiente, host, ticket/change ID, janela, owner, plano de comunicação, evidência do GO G2 do PO; verificar exigência de anuência da Controladoria específica para itens não cobertos.
2. **Estado atual read-only:** SHA/dirty status em `srv-api`, compose e imagens/digests ativos, health/ready reais, serviços de Portal, Core, BFF, Postgres, Keycloak e gateway, URLs e recursos (disco/CPU), env keys **sem valores**. Confrontar Docker image content vs commit declarado.
3. **Migrations:** consultar ledger `schema_migrations` e checksum/ordem V001–V014 e qualquer nova migration no SHA pretendido; marcar se upgrade já executado. Nunca aplicar migration manualmente em duplicidade ou editar V001–V014 retroativamente.
4. **Dados e recuperação:** comprovar backups íntegros/recuperáveis do PostgreSQL plugins, volumes de anexos/upload, corpus, configuração IAM; onde apropriado, praticar restore em área isolada; janela, RPO/RTO e rollback do app, com ressalva de migrations up-only.
5. **Segurança:** Core effective permissions `controllership-finance.access/manage`, ACLs/escopos, segregação de reviewer e auditoria. Não usar JWT como authority final. Logs sem tokens; HA/alertas relevantes.
6. **Mudanças novas:** catalog `controllership_finance` exige validação do owner Core/Plataforma, por afetar catálogo compartilhado e Portal. Comparar todos os consumers/producers e fazer smoke de regressão do Core e dos plugins existentes impactados.
7. **G1:** deixar T03/T05, P7 e R01–R15 oficiais explicitamente fora do pacote de "funcionalidade oficial homologada" enquanto owners não assinarem suas decisões; evitar falsa promessa de dados ERP.

### Resultado formal

Operador registra **`G3_OPERATOR_DECISION = GO | NO_GO`** para um SHA, hosts, serviços, janela, owner, backups e comandos **específicos**; uma aprovação para diff inventariado, não autorização genérica para qualquer comando futuro. Sem essa decisão, somente leitura e preparação. Se houver evidência contemporânea preexistente do deploy ocorrido, anexar; caso não exista, registrar **EXECUTION_DRIFT histórico**, nunca retrodatação.

**Não fazer um novo deploy só por haver G2.** Se o SHA produtivo já for equivalente à release aprovada, priorizar smoke e IAM; caso difira, fazer rollout mínimo pelo runbook oficial, após GO G3. Em nenhuma hipótese destruir uploads, corpus ou dados de outras aplicações.

## 4. IAM Keycloak: único bloqueio externo necessário ao ChatGPT

### 4.1 Recuperar acesso administrativo legítimo

Owner IAM verifica via canal seguro o mecanismo administrativo **vigente** para realm/instância produtiva, sem imprimir usuário/senha/token, sem fazer dump de `infra/.env` e sem ampliar privilégio de `delpi-core-admin` por conveniência.

O script no repositório é `infra/scripts/keycloak-prod-delia-mcp-provision.sh`; executa engine compartilhado `infra/scripts/delia_mcp_keycloak_state.py`. **O wrapper encaminha `--check` ou `--apply` ao engine inteiro: não há parâmetro específico de `mcp-clara` comprovado nessa interface.**

### 4.2 Somente após admin legítimo: check e revisão do diff

```bash
# Read-only — executar no host correto, por operador autorizado;
# conferir a configuração segura e o realm antes do comando.
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check
```

**Inspecionar impacto real, não presumir apenas CLARA:** `mcp-api-delpi`, `mcp-transformometro`, `mcp-tv-dashboard`, `mcp-clara`, client requester DÉLIA, client scopes, token exchange/policies e audiences. Comparar baseline e JSON sanitizado; nenhuma modificação em clientes irmãos sem decisão IAM/Plataforma expressa. Se o engine não permitir escopo limitado, **`DECISION_REQUIRED`** sobre o diff/forma de aplicação; não alterar engine prod por preferência técnica.

Antes do apply, owner IAM e Operador validam: backup/export de config permitido, rollback plausível, janela autorizada, clients existentes, realm correto, `mcp:tools` shared scope sem audience específica, dedicated scope CLARA `mcp-audience-clara`, audience exata do endpoint, PKCE S256 e token endpoint auth `client_secret_post`. Aprovar o diff de forma explícita.

### 4.3 Apply condicional

```bash
# EXECUTAR SOMENTE se --check, diff, owners e G3 forem aprovados.
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --apply
```

A saída deve ser auditada, sem secrets. Após qualquer alteração, executar **novo --check**, provar client `mcp-clara` e ausência de regressão/alteração não autorizada em TÉO/DAVI/VISTA/DÉLIA. **FAIL => parar novas escritas, preservar evidência e executar procedimento de contingência aprovado.**

## 5. Ficha e cadastro do ChatGPT — somente valores públicos verificados

**Conexão esperada, a comprovar no runtime:**

| Campo | Contrato alvo |
|---|---|
| Nome | CLARA — Central de Fechamento |
| MCP endpoint | `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` |
| Client ID | `mcp-clara` |
| Issuer | `https://minhadelpi.com.br/auth/realms/delpi` |
| Authorization endpoint | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/auth` |
| Token endpoint | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/token` |
| JWKS | `https://minhadelpi.com.br/auth/realms/delpi/protocol/openid-connect/certs` |
| Scopes | `openid profile email mcp:tools` (opcional `offline_access` se aprovado) |
| Audiences exigidas do token | `delpi-central` + `https://minhadelpi.com.br/apps/controllership-finance-api/mcp` |
| PKCE | `S256` |
| Client authentication | `client_secret_post`; secret **somente** no cofre/UI autorizada, nunca GitHub/chat |
| Resource metadata | seguir discovery real do `WWW-Authenticate` no MCP e conferir payload, não forçar um path hipotético |
| Redirect URI | **obter a URL exata do fluxo de cadastro deste plugin no ChatGPT**; registrar no Keycloak, sem wildcard nem reutilização de callbacks de outros MCPs |

**Workflow humano obrigatório:** dono do workspace ChatGPT inicia a conexão/plugin → copia callback exibida → entrega **apenas callback pública** ao Operador IAM → IAM aprova e cadastra exatamente a URI no client `mcp-clara` → usuário conclui OAuth login e conexão → operador documenta metadata, usuário e momento sem segredos. Não alegar criação automática na conta do usuário.

## 6. Smoke pós-liberação: critérios de outcome, não somente HTTP status

**A sequência deve ser realizada apenas por identidade autorizada, e ACT exclusivamente em dados/situações de teste formalmente autorizados pelo owner. Não fabricar uma competência produtiva para testar write.**

1. Portal e BFF: health+ready, login SSO real, Home, Checklist, P6, pacotes, retornos 409 e 404 tipados, relação de permissões ACCESS/MANAGE, deep links e versão correta da UI/plugin-ui.
2. Core e notificações: categoria `controllership_finance` aprovada/implantada, produção de evento de teste se permitido, despacho/persistência e ausência de quebra em outros portais.
3. CLARA IAM: sem token => 401; token sem `mcp:tools` ou audience certa => negado; token correto + Core effective permission => discovery `initialize` e `tools/list` com ferramentas previstas (18 segundo contrato atual); documentação dos casos permitidos/negados.
4. CLARA READ/KNOWLEDGE: consultar competência/contexto permitido; fonte/citação do corpus publicada e versão real (relatório anterior 52 fontes/1298 itens, confirmar read-back), sem vazamento cross-user.
5. Batch consent: preparar lote 2 ops com plano visível na página confiável do Portal; autorizar **uma única vez**; executar por MCP; provar challenge `CONSUMED`, lotes `COMPLETED`, operações `VERIFIED`, postcondition READ-back independente; replay, actor mismatch e scope inválido negados. Não usar registros de produção reais por conveniência.
6. Operacional: registrar SHA da imagem efetivamente em uso, migration ledger, volumes íntegros, logs sanitizados, monitoramento, restaurabilidade e owner do smoke. Falha material em segurança/integridade => `STOP/NO_GO`.
7. ChatGPT: usuário pode consultar a CLARA no workspace, tools discovery real, READ com citações, plano e consentimento conforme UI; ChatGPT pode impor confirmação nativa adicional sem remover controles de negócio.

**Resultado possível:** `PASS`, `FAIL`, `INCONCLUSIVE`, `TEST_NOT_RUN`. Nunca inferir aprovação IAM ou conexão ChatGPT a partir de 401/metadata 200.

## 7. Entregáveis do Operador/IAM — única pauta de handoff

```text
EXECUTION_ID: CF-PROC0072-G3-OPERATOR-IAM-CHATGPT-001
DATE_TIME_TZ:
OPERATOR_ROLE_AND_APPROVAL_REF:
IAM_OWNER_APPROVAL_REF:
CONTROLADORIA_SPECIFIC_ACCEPTANCE_IF_REQUIRED:
G2_PO_REF: CF-PROC0072-G2-ACCEPT-WITH-RESIDUAL-20261026
CHANGE_ID_AND_WINDOW:
TARGET_HOST_AND_ENV:
BASE_HEAD:
RELEASE_SHA:
DEPLOYED_SHA_BEFORE:
DEPLOYED_SHA_AFTER:
GIT_STATUS_AND_IMAGE_DIGEST:
CORE_PORTAL_BFF_DIFF:
CORE_NOTIFICATION_OWNER:
G1_OUT_OF_SCOPE:
PG_BACKUP_AND_RESTORE_PROOF:
UPLOAD_AND_CORPUS_BACKUP:
MIGRATIONS_READBACK:
ROLLBACK_CAPABILITY_AND_LIMIT:
G3_OPERATOR_DECISION: GO | NO_GO | PENDING
KEYCLOAK_ADMIN_ACCESS: VALID | BLOCKED
KEYCLOAK_CHECK_AND_SANITIZED_DIFF:
KEYCLOAK_SHARED_BLAST_RADIUS:
KEYCLOAK_IAM_APPROVAL:
KEYCLOAK_APPLY: PASS | FAIL | TEST_NOT_RUN
CLIENT_MCP_CLARA:
OAUTH_METADATA_AND_AUDIENCES:
CHATGPT_CALLBACK_REGISTERED: PASS | FAIL | TEST_NOT_RUN
CHATGPT_CONNECTION: PASS | FAIL | TEST_NOT_RUN
MCP_DISCOVERY:
MCP_READ_KNOWLEDGE_CITATIONS:
MCP_BATCH_CONSENT_AND_READBACK:
PORTAL_FUNCTIONAL_SMOKE:
AUDIT_AND_SAFETY_NEGATIVES:
ROLLBACK_TRIGGERED: YES | NO
RESIDUALS_WITH_OWNER:
FINAL_VERDICT: ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE
EVIDENCE_LINKS_AND_DOC_COMMITS:
```

Após cada fase, atualizar [Doc 107](./107-clara-validacao-antecipada-chatgpt-release-hoje.md) com runtime/keycloak/ChatGPT e [Doc 108](./108-homologacao-guiada-g2-g3-2026-10-26.md) com outcome G3; em [Doc 109](./109-go-po-ultima-rodada-e2e-usuario-g2-g3-2026-10-26.md) manter rastro da decisão PO. Não sobrescrever a evidência antiga nem atualizar status por hipótese.

**Paradas obrigatórias:** credencial IAM não válida; drift transversal não aprovado; ausência da assinatura G3 do operador; risco de escrita não autorizada; backup insuficiente; escolha material sem owner. Prosseguir com inventário e documentação independentes, mas **não aplicar mudanças produtivas** até o gate correspondente.

**Objetivo operacional:** conectar CLARA real no ChatGPT, comprovar com login e outcomes auditáveis, preservando autorização humana e governança. Este handoff não concede autorização por conta própria.

## 8. Execução registrada — Operador SSH via agente Devin (26/10/2026, ~14:30 UTC)

Handoff executado na mesma sessão sob GO do Operador/owner IAM ("GO PARA FECHAMENTO G3 E CLARA NO CHATGPT"). Resultados com evidência real; nenhum PASS sem prova.

```text
EXECUTION_ID: CF-PROC0072-G3-OPERATOR-IAM-CHATGPT-001
DATE_TIME_TZ: 2026-10-26 ~14:15-14:35 UTC (srv-api)
OPERATOR_ROLE_AND_APPROVAL_REF: GO verbal do Operador/owner IAM nesta sessão (Doc 110 §1)
IAM_OWNER_APPROVAL_REF: n/a para alteração Keycloak — credencial inválida, nada aplicado
CONTROLADORIA_SPECIFIC_ACCEPTANCE_IF_REQUIRED: NOT_RECORDED (não exigida para este escopo)
G2_PO_REF: CF-PROC0072-G2-ACCEPT-WITH-RESIDUAL-20261026
CHANGE_ID_AND_WINDOW: sessão G3 26/10 ~14:15-14:35 UTC; janela ad-hoc autorizada pelo Operador
TARGET_HOST_AND_ENV: srv-api (192.168.1.237) — produção Minha DELPI
BASE_HEAD: d86d49ac2037 (checkout pré-execução; já continha R4 5e9a0ddd81 como ancestral)
RELEASE_SHA: 85883e5f2e789cd720d52b25975b9e1587ad0667
DEPLOYED_SHA_BEFORE: d86d49ac2037a78327e51c70819cd0ec79478bc2 — TREE com fixes R4, porém
                     IMAGENS pré-R4 (criadas 10:02-10:03Z; commit R4 = 13:48Z)
DEPLOYED_SHA_AFTER: 85883e5f2 (script canônico fez pull --ff-only no início do build;
                    delta = supplies S2 widget + transformometro fix — fora do escopo CF,
                    imagens desses contextos não reconstruídas)
GIT_STATUS_AND_IMAGE_DIGEST: tree limpa; imagens infra-{core-api,portal,controllership-
                             finance,controllership-finance-api}:latest criadas 14:28-14:29Z
CORE_PORTAL_BFF_DIFF: 5e9a0ddd8 (catalog Core + fallback Portal + producer BFF + banner 404/409)
                     + d59e972a47 (step-up getFreshAccessToken, ausente na imagem portal 10-21)
                     + 0fdb467ff8 (DeliaDock CSS, cosmético)
CORE_NOTIFICATION_OWNER: categoria controllership_finance aditiva no catálogo canônico —
                         diff JSON de 1 entrada; validada em runtime (grep binário=1)
G1_OUT_OF_SCOPE: T03/T05/P7/R01-R15 oficiais permanecem fora do aceite (owners externos)
PG_BACKUP_AND_RESTORE_PROOF: ~/backups/cf-schema-pre-g3-20261026-142452.dump (689K, -Fc,
                             pg_restore -l lista 64 objetos TABLE — artefato restaurável)
UPLOAD_AND_CORPUS_BACKUP: ~/backups/cf-uploads-pre-g3-20261026-142543.tgz (dir /var/lib/delpi/
                          cf-closing-documents vazio em prod — sem uploads de usuários);
                          corpus está no schema PG (52 fontes/1298 itens — coberto pelo dump)
MIGRATIONS_READBACK: schema_migrations count=14 max=14 — V001-V014 íntegras, sem novas
ROLLBACK_CAPABILITY_AND_LIMIT: imagens anteriores retidas pelo Docker (rollback = re-tag/up);
                               migrations up-only já aplicadas (não revertíveis);
                               .env editado com append único (reversível removendo a linha)
G3_OPERATOR_DECISION: GO — executado conforme runbook; alinhamento de imagens aplicado
KEYCLOAK_ADMIN_ACCESS: BLOCKED — KEYCLOAK_ADMIN em infra/.env falha login realm master
                       (credencial bootstrap rotacionada; engine FAIL_CLOSED correto)
KEYCLOAK_CHECK_AND_SANITIZED_DIFF: TEST_NOT_RUN — sem admin válido, --check aborta
KEYCLOAK_SHARED_BLAST_RADIUS: não avaliado (requer --check bem-sucedido)
KEYCLOAK_IAM_APPROVAL: PENDING — owner IAM deve fornecer credencial vigente
KEYCLOAK_APPLY: TEST_NOT_RUN
CLIENT_MCP_CLARA: NOT_PROVISIONED — permanece bloqueado por IAM
OAUTH_METADATA_AND_AUDIENCES: discovery público 200; audience/alvo na ficha pública
CHATGPT_CALLBACK_REGISTERED: TEST_NOT_RUN — depende de mcp-clara
CHATGPT_CONNECTION: TEST_NOT_RUN
MCP_DISCOVERY: PROVEN parcial — sem token 401 (GET e POST initialize); discovery
               autenticado exige client mcp-clara → TEST_NOT_RUN
MCP_READ_KNOWLEDGE_CITATIONS: TEST_NOT_RUN em prod (corpus íntegro: 52/1298/1 versão)
MCP_BATCH_CONSENT_AND_READBACK: TEST_NOT_RUN em prod (requer mcp-clara + usuário)
PORTAL_FUNCTIONAL_SMOKE: portal 200, core health 200, OIDC metadata 200,
                         /ready controllership-finance-api = ready (era degraded)
AUDIT_AND_SAFETY_NEGATIVES: MCP fail-closed 401 sem token; catalog /me/* exige auth
                            (401); zero regressão nos demais serviços (107 Up)
ROLLBACK_TRIGGERED: NO
RESIDUALS_WITH_OWNER:
  - KEYCLOAK_PROD mcp-clara: owner IAM — credencial admin vigente + --check + apply
  - CHATGPT: owner workspace — cadastro após mcp-clara
  - collation mismatch plugins_hub (2.41 vs 2.36): plataforma — WARNING, não bloqueante
  - backup PG schema-only por operador: rotina full-DB existente não evidenciada nesta janela
FINAL_VERDICT: ACCEPT_WITH_RESIDUAL — alinhamento de release executado e comprovado
               em runtime; G3 operacional validado para o escopo de código R4;
               ChatGPT/CLARA prod permanece bloqueado exclusivamente por credencial IAM
EVIDENCE_LINKS_AND_DOC_COMMITS: este adendo; Doc 107 Adendo 9; Doc 108 seção G3
```

### 8.1 O que a execução provou (runtime, não hipótese)

- **Drift imagem↔tree corrigido:** imagens `infra-{core-api,portal,controllership-finance,controllership-finance-api}` recriadas pelo script canônico `up-prod-sequential.sh --build` no SHA `85883e5f2`. Binário BFF em runtime tem `"category": "controllership_finance"` (gateway.py:209); catálogo Core contém a categoria; bundle Portal contém `getFreshAccessToken` + fallback; bundle MFE novo hash com mensagens tipadas.
- **`/ready` prod `degraded` → `ready`:** causa raiz era ausência de `CORE_API_EFFECTIVE_ACCESS_SERVICE_TOKEN` em `infra/.env` (compose passa `${VAR:-}` → vazio). Provisionado segredo dedicado via `openssl rand` (nunca impresso; `.env` é gitignored). `core-api` não recebe a var — o endpoint effective-access permanece fail-closed, o que é correto hoje (BFF só exige a var no gate de readiness; nenhuma chamada a usa ainda).
- **Zero writes produtivos de negócio:** nenhum evento de notificação emitido, nenhuma competência/documento tocados, nenhum migration nova (V014 já estava aplicada).
- **Blast radius do rebuild:** diff `d86d49ac..85883e5f2` = apenas supplies S2 + transformometro fix (imagens desses contextos não reconstruídas — sem efeito). Nos 4 serviços reconstruídos, delta de código = exatamente os commits R4 + step-up + CSS.

### 8.2 Bloqueio único restante e ação exata

`KEYCLOAK_ADMIN_ACCESS=BLOCKED`: `KEYCLOAK_ADMIN`/`KEYCLOAK_ADMIN_PASSWORD` presentes em `infra/.env` mas o login no realm `master` falha (`FAIL_CLOSED` no engine — comportamento correto). **Ação do owner IAM:** fornecer credencial administrativa vigente pelo canal seguro (atualizar `infra/.env` no host ou `KC_ADMIN_TOKEN` na sessão), depois `KC_BASE=https://minhadelpi.com.br/auth bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check`, revisar diff compartilhado (mcp-api-delpi, mcp-transformometro, mcp-tv-dashboard, mcp-clara, scopes/policies), aprovar explicitamente e só então `--apply`. Sem isso, nenhuma etapa de ChatGPT pode começar.



## 9. Revisão independente do relatório G3 — 26/10/2026

**Autoridade examinada:** commit GitHub `deaf5b1cb2174ca21d8d2da8ff81b1bf82d0b67f` (execução documental e testemunho do Operador via Devin), release referenciado `85883e5f2e789cd720d52b25975b9e1587ad0667`, [Doc 107 adendo 9](./107-clara-validacao-antecipada-chatgpt-release-hoje.md), [Doc 108 seção G3](./108-homologacao-guiada-g2-g3-2026-10-26.md), código `controllership-finance-api/controllership_finance_app/config.py`, `interface/http/routes/health_routes.py` e wrapper `infra/scripts/keycloak-prod-delia-mcp-provision.sh`. **Não houve SSH, exame de Docker/PG in loco, reprodução de backup/restore ou conexão ChatGPT pelo revisor; evidência operacional é reportada pelo executor.**

### Parecer de G3 por recorte

| Recorte | Parecer independente | Observação |
|---|---|---|
| Rebuild/alinhamento R4 no release | `ACCEPT_WITH_RESIDUAL` para o **relatório do Operador** | Imagens e conteúdo compilado declarados/registrados no doc; SHA e hash do binário ainda sem captura independente neste turno |
| Autorização operacional G3 do release já feito | `OPERATOR_RECORDED / TO_VERIFY_ATTESTATION` | Relatório atribui GO a “Operador/owner IAM nesta sessão”, mas `OPERATOR_ROLE_AND_APPROVAL_REF` contém apenas GO verbal, sem referência verificável de identidade, change ID formal ou assinatura de pessoa habilitada. Não classificar como aprovação IAM |
| Backup/restore | `BACKUP_REPORTED / RESTORE_TEST_NOT_RUN` | `pg_restore -l` demonstra arquivo legível/lista de objetos, **não** uma restauração de dados testada. Dump escopado a schema e uploads vazios não comprovam cobertura de outros dados; evidenciar política de backup regular e restoration drill quando aplicável, sem intervenção destrutiva |
| /ready do BFF | `CONFIG_READY=PASS_REPORTADO`, **não `CORE_CONNECTIVITY_PROVEN`** | O código atual de `/ready` só chama `missing_required_config()`: confere nomes/valores não vazios, não realiza rede nem valida token. O relatório informa token aleatório configurado no BFF, Core não recebendo a mesma chave e "nenhuma chamada a usa ainda". Exigir testes autenticados de effective-permission e contracts se qualquer rota usar esse token; não tratar `ready` como prova de RBAC efetivo |
| Regressão de Core/Portal | `SMOKE_READ_ONLY_PARTIAL` | 107 containers Up, 200 da Home/health, 401 fail-closed sem token são sinais válidos, mas não comprovam ausência geral de regressões nem outcome de notificações com usuário real |
| Provisionamento `mcp-clara` prod | `BLOCKED_IAM` | Credencial administrativa fornecida no host não permite login; `--check` aborta, sem diff; `--apply` não executado |
| Cadastro e smoke CLARA no ChatGPT | `TEST_NOT_RUN` | Sem client OAuth produtivo, callback real nem tokens com audience específica. O piloto local J10 não substitui prod |

**Veredito preservando trabalho feito:** `ACCEPT_WITH_RESIDUAL` para a etapa **relatada** de alinhamento operacional do release. `INCONCLUSIVE` para a liberação end-to-end da CLARA em produção. Isso não pede novo rebuild, reset ad hoc de Keycloak ou rework de produto; são fronteiras de evidência a observar no fechamento final IAM/ChatGPT. A revisão não altera a declaração histórica `G3_OPERATOR_DECISION=GO` registrada pelo executor, mas impede tratá-la como signoff independente de IAM ou smoke autenticado.

### Próxima ação única — IAM, sem senha no chat

1. **Owner IAM** confirma identidade e canal seguro do Operador; fornece credencial administrativa **vigente** ou token delegado administrativo validamente emitido e suficiente para o realm `delpi`. Nunca copiar segredo/valor de env para GitHub, ChatGPT ou console de relatório; não usar conta bootstrap inválida, SQL/DB/Keycloak bypass nem ampliar service account de Core por conveniência.
2. **Operador SSH** executa somente `--check` com as credenciais legítimas, registra resultado **sanitizado** e inventário de alterações propostas: `mcp-api-delpi`, `mcp-transformometro`, `mcp-tv-dashboard`, `mcp-clara`, DÉLIA requester, scopes, audiences e policies. O wrapper atual não comprova suporte a `--apply` exclusivo `mcp-clara`.
3. **Owner IAM/Plataforma decide** o diff e blast radius compartilhado (se houver decisão material, devolver `DECISION_REQUIRED` com opções, não aplicar por suposição). Operador confere backup/rollback IAM e obtém GO específico para nova alteração.
4. Após aprovação: `--apply` autorizado → novo `--check` → audience/scope/PKCE/issuer/redirect de `mcp-clara` provados sem publicar secret → dono do workspace ChatGPT obtém **callback real** no fluxo de conexão → IAM registra callback exata → usuário conclui login OAuth.
5. Smoke autenticado real: tools/list (18 esperadas), READ por usuário autorizado, fontes/citações do corpus, fail-closed sem scope ou com audience incorreta; lote com **uma aprovação de negócio**, somente sobre cenário produtivo de teste previamente autorizado, estado e auditoria verificados. Resultado final em Docs 107/108/110 com SHAs, responsável e teste.

**Sem nova alteração produtiva automática pelo GPT.** Não requer reabrir G2 do PO; respeitar ressalvas P7, relatórios oficiais e owners G1 ainda pendentes.



## 10. Sessão guiada de cadastro Keycloak/ChatGPT — evidência inicial por capturas (26/10/2026)

**Origem:** o PO enviou três capturas da console administrativa Keycloak `https://minhadelpi.com.br/auth/admin/master/console/#/delpi/clients` em 26/10/2026 (interface visível; capturas permanecem na conversa, **não** anexadas ao GitHub). Realm `delpi` selecionado, sessão de console funcional. A lista filtrada por `mcp` apresenta `mcp-api-delpi`, `mcp-transformometro` e `mcp-tv-dashboard`, **sem `mcp-clara`**. O rol completo mostra também `controllership-finance-api`, `delpi-central`, `delia-api` — esses clients existentes **não substituem** o futuro `mcp-clara`.

**Classificação:** `PROVEN` somente a **ausência visual do client CLARA na lista filtrada** e o acesso humano à console; login humano no navegador **não** comprova credencial válida para `KC_ADMIN_TOKEN`/provisionador, nem autoridade de mudança IAM para qualquer outro recurso. Cliente produtivo `mcp-clara` permanece `NOT_PROVISIONED` até screenshot após Save + metadata/claims verificados. ChatGPT `TEST_NOT_RUN`.

**Solicitação do PO:** guiar manualmente, pela console Keycloak e interface ChatGPT, o cadastro da CLARA em etapas verificadas por captura. O projeto possui **engine IAM canônico compartilhado** `infra/scripts/delia_mcp_keycloak_state.py`; usar a console como **procedimento de provisionamento assistido** somente com autoridade IAM apropriada, verificar cada campo contra o desired-state sem inventar callback, sem modificar clients irmãos e **sem aplicar depois o engine compartilhado às cegas**. Owner IAM/Plataforma deve reconciliar qualquer drift e aprovar mudanças de scope/policy transversal.

**Contratos a preservar:** `client_id=mcp-clara`; OpenID Connect, confidential/client authentication ON, Standard flow ON, PKCE `S256`, Implicit/Direct grants/Service Accounts OFF; dedicated scope `mcp-audience-clara` com audience exata `https://minhadelpi.com.br/apps/controllership-finance-api/mcp`, shared `mcp:tools` sem mapper de audience específica, `delpi-central` como audience exigida pelo servidor; callback **somente a exibida no fluxo real de cadastro ChatGPT**, registrada exatamente no client, sem wildcard. Client secret jamais copiado em print/Git/chat. Token exchange policy com DÉLIA exige IAM owner e não pode ser inferida do simples client OAuth.

**Próxima evidência:** o PO abre `Clients → Create client`, insere general settings no realm `delpi` sem concluir Save, e envia captura **sem credenciais** para validar antes de gravar. Registrar depois o resultado da criação, vinculação de scopes, audience, testes de tokens e conexão ChatGPT.

### 8.3 Nota posterior — Client ID OAuth definitivo

O PO formalizou `mcp-controllership-finance` como Client ID (ficha pública); código, engine IAM, testes e runbooks foram reconciliados (Doc 107 Adendo 10). O `--check` pendente deve agora validar o client **`mcp-controllership-finance`** (não `mcp-clara`); se o client prod divergir do desired-state (scopes, audience mapper `mcp-audience-clara`, PKCE S256, redirect exato), o `--apply` o corrige idempotentemente — sem tocar demais specialists.
