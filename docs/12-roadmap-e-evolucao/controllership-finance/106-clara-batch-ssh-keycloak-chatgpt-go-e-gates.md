# Documento 106 — CLARA batch inteligente, release SSH, Keycloak e cadastro no ChatGPT

**Data:** 2026-10-25. **Decisão expressa do PO:** CLARA deve compreender e executar pedidos que contêm múltiplas ações, com o mínimo de interação, tendo o usuário como autor da solicitação e responsável pelas decisões delegadas. **ID:** `CF-PROC0072-CLARA-BATCH-RELEASE-001`. **Estado:** `PO_APPROVED_PRODUCT_DIRECTION`; contratos físicos, segurança e deploy ainda condicionados aos gates descritos abaixo.

**Autoridade:** Documento 106 complementa e **altera prospectivamente** o contrato de interação do [Documento 94](./94-clara-especialista-mcp-controladoria-financas.md) §10.1 e do [Documento 14](./14-seguranca-rbac-auditoria-e-ia.md) §IA, substituindo **somente** a exigência de confirmação conversacional isolada para cada operação sensível. Mantém D01=B (execução humana delegada, não decisão autônoma), owners, Clean Architecture, effective permission Core, C2/P5 e todas as demais invariantes. Não reclassificar retrospectivamente as evidências do [Documento 100](./100-ciclo3-p6-min-p2-read-runtime-evidencia-de-execucao.md).

## 1. Escopo aprovado

- **PRIORIDADE:** fechamento mensal PROC-0072 (P1–P6, R01–R15, P3/T03/T05, evidências, pacotes/revisões), CLARA MCP com conhecimento próprio, consulta/análise e execução múltipla governada.
- **ADIADOS:** Sala de interação, expansão de Minhas tarefas e Contabilidade/DRE como página/fluxo próprio. Preservar código de Minhas tarefas sem expor na release. Não inferir que `submeter pacote para review` seja `enviar anexos para DRE/Contabilidade`: E04/T04 permaneceram NOT_REQUIRED na V1.
- **CONTEÚDO CLARA:** corpus governado com docs e evidências originais quando acessíveis por canal autorizado; vídeo, PDFs, XLSB/XLSX não foram comprovados como ingeridos na execução anterior. Proveniência por fonte/hash/localizador/timecode e restrição de acesso; não publicar dados brutos confidenciais no GitHub.
- **GO de trabalho:** executar correções e funcionalidades que tenham contrato/owner aprovado; interromper somente o subgrafo material dependente de `DECISION_REQUIRED`, G2 ou G3. Nenhuma autorização tácita de proprietário externo.

## 2. Decisão funcional aprovada: lote de ações com baixo atrito

O usuário pode formular **um pedido com N operações**. A CLARA deverá planejar um lote ordenado pelas dependências, identificar operações autorizadas, preparar efeitos e executar o trabalho solicitado sem confirmar repetidamente o mesmo plano.

**A aprovação refere-se ao escopo exato que o usuário autorizou, não a `blanket consent` para operações futuras**. Dois caminhos técnicos possíveis para provar intenção, que dependem de gate transversal com owner de identidade/cliente MCP:

- **A — intenção autenticada atestada pelo host (preferencial quando realmente comprovada):** a solicitação original e seu escopo são vinculados ao ator, canal, contexto, versão do plano e comprovante íntegro, verificável pelo backend. Uma frase gerada pelo modelo, boolean `confirmed=true` ou possession de `proposal_handle` **não** são prova. Somente aplicar A se o cliente/host fornecer atestação efetivamente verificável.
- **B — confirmação consolidada do plano (fallback recomendado):** uma aprovação por lote exibindo ator, competência, objetos, operações, motivos, efeitos e dependências, com prova governada de consentimento vinculada ao lote. Não uma aprovação por operação. Se o host ChatGPT impor confirmação nativa por tool/ação, respeitá-la: a CLARA não controla nem contorna a interface/política do host.

**Status contratual:** `PO_APPROVED` para experiência de lote + mínimo atrito; `DECISION_REQUIRED / TECHNICAL_SECURITY_GATE` para forma física de atestar intenção e integrar a confirmação do host. **A/B não estão implementadas por esta decisão.**

### Orquestração obrigatória

`INTENT → DISCOVERY/AUTHZ → PLAN/DEPENDENCIES → PREPARE_BATCH → VERIFIED_CONSENT → CLAIM → ACT_EACH → READ_BACK_EACH → AUDIT → SUMMARY`.

- Planejar ações explícitas, dependências, versões, motivos, elegibilidade, limites e resultados esperados. Não usar material recuperado da base de conhecimento como nova instrução ou autorização (proteção contra prompt injection).
- Uma aprovação autenticada pode autorizar as **operações individualmente listadas no mesmo plano**; adicionar recurso/operação, ampliar escopo ou mudar efeitos exige novo consentimento para o delta.
- O BFF revalida **por operação e no instante de escrita** Core effective permissions frescas, área/assignment, ownership, recurso, business rule, state, lock, version/OCC; ACCESS não equivale a MANAGE.
- `PREPARE_BATCH` sem side effect de domínio. Falha/indisponibilidade de snapshot deve bloquear, nunca `{}` silencioso. Propostas vinculadas a ator, plano/versão, nonce, expiração e hash canônico.
- **Exatamente uma execução lógica por operação/idempotency key**: claim durável antes do efeito, transições `PREPARED/CLAIMED/APPLIED/VERIFIED/FAILED/UNKNOWN` (nomes técnicos sujeitos a contrato físico), retries bounded e recuperação/consulta após timeout. Não executar efeito e só depois consumir o handle. Não exigir transação global impossível entre serviços.
- Quando uma operação falha, bloquear dependentes e continuar apenas ações independentes que permaneçam explicitamente dentro da autorização; reportar resultados `VERIFIED`, `FAILED`, `BLOCKED`, `UNKNOWN` sem falso sucesso. Reconciliação de outcome desconhecido antes de retry.
- Verificação read-after-write realmente independente, não apenas `response contém decision_id`. Auditoria por operação e por lote, usuário/escopo/versão, origem `mcp/clara`, correlation; sem tokens ou dados pessoais indevidos.
- Não criar capacidade de escrita que a BFF/UI não ofereça, não sacramentar/reabrir TOTVS e não criar um endpoint de bypass C2. Fechamento mensal continua resultado derivado do processo, não um estado imposto pela IA.
- Testes críticos: pedido com 2–20 ações; sequenciamento; operações independentes vs dependentes; inclusão fora de escopo; sem autorização; duas ACT concorrentes mesmo handle; falhas entre efeito/claim/verify; recuperação; stale version; wrong actor; Core 503; prompt injection documental; diferentes áreas e duas competências.

## 3. Segurança: rework precedente continua válido, adaptado ao lote

A revisão da entrega `54f5381c5e` identificou lacunas em consentimento verificável, execução antes do consumo atômico, verificação de pós-condição, `_snapshot` best-effort, paridade/escopo de READ e vazamento de metadados em `list_sources`. Corrigir **na nova estrutura de lote**, sem implementar a solução antiga de confirmações conversacionais individuais. Enquanto o novo gate físico não estiver aprovado/testado, **ACT desabilitada/fail-closed em produção**; DISCOVERY/READ/ANALYSIS podem seguir somente após testes reais de autorização e conformidade.

`EXECUTION_DRIFT` da formalização anterior D02–D05: decisões lançadas por executor sem prova de aprovação do owner, apesar de escolhas alinhadas ao padrão existente. Regularizar aprovação de autoridade/segurança e compatibilidade OAuth; não apagar trabalho existente nem falsificar aceite retroativo.

## 4. Keycloak, Operador SSH e integração ChatGPT — requisitos operacionais

**Intenção do PO:** concluir implementação e ativar CLARA em produção, configurar Keycloak no padrão da plataforma (referência TÉO), e devolver uma ficha de cadastro para instalar/testar o servidor MCP como plugin no ChatGPT.

**Sequência vinculante:** implementar → testes em não produção → decisões materiais G1 → **G2 aceite humano explícito Controladoria/PO** → **G3 autorização operacional explícita do Operador SSH** → preflight/backup/rollback → alteração Keycloak/ambiente de produção **autorizada** → deploy do SHA imutável → ingestão corpus governada → smoke HTTP/MCP autenticado → ficha de cadastro ChatGPT → teste privado de plugin. A intenção de deploy neste documento **não é G2 nem G3**.

### Keycloak — padrão existente, sem reproduzir secrets

Inventariar client MCP TÉO no código/configuração vigente e estado REAL Keycloak por canal autorizado, comparando realm, issuer, discovery, URLs, PKCE, `offline_access`/refresh, scopes `openid profile email mcp:tools`, audience **URL exata do recurso CLARA**, bindings de client scope, `resource`, proteção de token, CORS/origins, redirects exigidos pelo host, client authentication e provisioning idempotente. **Não copiar client_id/secret/audience TÉO cegamente**. Revalidar D03 e URL pública real HTTPS antes de qualquer escrita. Não criar client administrativo privilegiado na superfície MCP. Alterações de Keycloak exigem autorização administrativa e rollback/documentação.

O ChatGPT admite conexão a servidor MCP por URL HTTPS pública (ou Secure MCP Tunnel quando aplicável); plugin customizado depende das permissões/plano do workspace e pode aplicar **confirmação nativa em gravações**, independente da política conversacional da CLARA. Não prometer remover essas confirmações do host. Referência externa: https://help.openai.com/pt-br/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

### Ficha de configuração a entregar — valores públicos/não secretos

Entregar somente valores confirmados por read-back real e sanear os demais:

```text
CLARA_PLUGIN_NAME=CLARA — Especialista em Controladoria & Finanças
CLARA_PUBLIC_MCP_URL=<HTTPS real /apps/controllership-finance-api/mcp>
CLARA_OAUTH_ISSUER=<KEYCLOAK_ISSUER real público>
CLARA_OAUTH_AUTHORIZATION_ENDPOINT=<do discovery>
CLARA_OAUTH_TOKEN_ENDPOINT=<do discovery>
CLARA_OAUTH_JWKS_URI=<do discovery>
CLARA_OAUTH_CLIENT_ID=<identificador público aprovado>
CLARA_OAUTH_SCOPES=<escopos efetivamente aceitos>
CLARA_OAUTH_REDIRECT_URIS=<URIs confirmadas do ChatGPT no Keycloak>
CLARA_OAUTH_PKCE_REQUIRED=<true/false provado>
CLARA_OAUTH_REFRESH_TOKEN_SUPPORTED=<true/false provado>
CLARA_OAUTH_PROTECTED_RESOURCE_METADATA_URL=<HTTPS real>
CLARA_OAUTH_RESOURCE_AUDIENCE=<URL exata pública exigida>
CLARA_MCP_TOOLS_DISCOVERED=<lista verificada na conexão autenticada>
CLARA_MCP_READ_SMOKE=<PASS/FAIL/TEST_NOT_RUN>
CLARA_MCP_ACT_SMOKE=<PASS/FAIL/TEST_NOT_RUN/BLOCKED>
CLARA_CORPUS_PUBLISHED_VERSION=<versão real ou NOT_RUN>
CLARA_RELEASE_SHA=<SHA implantado ou NOT_DEPLOYED>
CLARA_KEYCLOAK_CHANGE_EVIDENCE=<ref de auditoria sem credenciais>
CLARA_G2_EVIDENCE=<identificador de aceite humano ou PENDING>
CLARA_G3_EVIDENCE=<identificador de autorização do operador ou PENDING>
```

**Segredos:** não retornar `.env`, senhas de admin, tokens, refresh tokens, client secret, service token ou configurações sensíveis em chats, logs, docs, MCP responses ou relatórios. Se o cadastro exigir secret, retornar SOMENTE `SECRET_REQUIRED=true` e referência segura do cofre + instrução de transferência por canal protegido; não exibir o valor. O usuário configurará/instalará o plugin no ChatGPT por sua própria interface, após teste e disponibilidade.

### Deploy e rollback

Consultar `infra/README-ambiente.md`, `infra/scripts/up-prod-sequential.sh` e a authority SSH antes de escolher comandos. Operador confirma backup PostgreSQL, uploads e corpus, Keycloak config export/rollback, migrations V004–V011, schema, health do gateway, planos de falha, migrações irreversíveis e read-back. Proibir alteração de produção ou Keycloak sem G2/G3. Smoke inclui permissões Core, portal, data persistente, OAuth discovery, MCP transporte, conhecimentos e ACT somente em cenário autorizado de teste. HTTP 200 sozinho não comprova outcome.

## 5. Contratos de aceitação

- P1–P6, R01–R15 e T03/T05 reais: estados honestos; relatórios oficiais só quando paridade e validação do owner forem demonstradas. MP4/transcrição e arquivos brutos não alegados como ingeridos sem acesso real.
- CLARA: paridade READ com a BFF do mesmo ator/escopo; corpus com fonte/hash/citação; instruções não confiáveis de arquivos não viram comandos; lotes sem confirmações redundantes mas com consentimento verificável e guardrails; capabilities anunciadas somente quando fisicamente operantes.
- 0 nova permission além de `controllership-finance.access` e `controllership-finance.manage`.
- G1 resolve decisões materiais; G2/G3 ficam `PENDING` até evidência real. `NO_DEPLOY` se qualquer preflight obrigatório falhar. ChatGPT plugin cadastro/teste: após deployment real, sujeito a disponibilidade/plano do ChatGPT.
- Próxima documentação runtime deve linkar SHAs, testes, matriz RQ/AC, evidências G1–G3 e riscos, sem declarar PASS por smoke não executado.

## 6. Execução solicitada ao Devin

Rodar **um programa contínuo**: inventário único HEAD/status/rules + Plano 106 → documento de contrato de lote e G1 focado → corrigir READ/ACT + implementar lote e testes → terminar integrações autorizadas do fechamento e conhecimento CLARA → gates G2/G3 → Operador SSH/Keycloak/deploy autorizado → ficha ChatGPT e smoke. Documentar `DECISION_REQUIRED` real e continuar tarefas independentes. Não retornar um plano em lugar de executar as etapas autorizadas. No entanto, **não** aprovar o próprio gate, tomar decisão de owner externo ou simular acesso/configuração produtiva.
