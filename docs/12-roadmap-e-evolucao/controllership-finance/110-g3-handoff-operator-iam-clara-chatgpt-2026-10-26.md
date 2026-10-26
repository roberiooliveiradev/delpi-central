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
