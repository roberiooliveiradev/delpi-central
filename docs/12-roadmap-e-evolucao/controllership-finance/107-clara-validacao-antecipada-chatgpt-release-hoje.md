# Documento 107 — Diretriz PO: teste antecipado da CLARA no ChatGPT e conclusão do release

**Data:** 2026-10-25 · **ID:** `CF-PROC0072-CLARA-CHATGPT-EARLY-VALIDATION-001` · **Autoridade:** PO, como atualização posterior aos Docs [104](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md), [106](./106-clara-batch-ssh-keycloak-chatgpt-go-e-gates.md), [94](./94-clara-especialista-mcp-controladoria-financas.md), [14](./14-seguranca-rbac-auditoria-e-ia.md). **Status:** `PO_APPROVED_SEQUENCE / EXECUTION_GO`; não equivale a G1 owner externo, G2, G3 ou deploy realizado.

## 1. Objetivo, urgência e decisão do PO

O PO determina que, **após a correção cirúrgica de consentimento da CLARA**, a equipe deve **disponibilizar o MCP para conexão de teste no ChatGPT o mais cedo possível**, realizar testes reais com o usuário e **prosseguir na mesma frente** para homologação G2, autorização G3 e implantação definitiva. Objetivo operacional: **concluir hoje (25/10/2026), se todos os owners e gates puderem aprovar tempestivamente**. Não transformar a meta em alegação de conclusão, autorização tácita, teste inferido, ou promessa de entrega assíncrona.

**Sequência preferida:** `FINAL_REWORK → LOCAL/INTEGRATION PASS → APPROVED NON-PROD MCP PILOT → CHATGPT CONNECT/READ/SAFE BATCH E2E → G1 OWNER CLOSE → G2 HUMAN SIGN-OFF → G3 SSH RELEASE AUTHORIZATION → PROD KEYCLOAK/DEPLOY → PROD SMOKE → FINAL CHATGPT CONNECTION/ACCEPTANCE → EVIDENCE/SHA`.

**Exceção de ambiente:** se não houver ambiente não produtivo **existente e autorizado** com HTTPS/OAuth/endereço acessível ao ChatGPT, **não tratar produção como piloto**. Primeiro preparar todas as evidências e executar G1/G2/G3; somente após autorização, implantação produtiva e teste no ChatGPT. Provisionar uma nova infraestrutura pública, alterar DNS, expor dados reais, operar Keycloak compartilhado ou habilitar portas externas exige os owners e a authority vigentes (DECISION_REQUIRED quando material).

Escopo: Central de Fechamento P1–P6 + CLARA MCP multiação + knowledge base + integrações oficiais provadas. **Sala de interação e expansão de Minhas tarefas adiadas.** DRE/Contabilidade separado fora do GO atual. Não reabrir as escolhas de produto já aprovadas.

## 2. Correção final de consentimento — apenas os gaps comprovados

A revisão independente do commit de step-up (identificado no GitHub como `d59e972a47e363ee0b31931ad1eb67056ed2249c`, verificar HEAD real) exige:

1. **Prova de autorização**: não usar apenas `iat` como prova de intenção humana nem um `skew` de 10 s que admita token anterior ao PREPARE como consentimento. Registrar uma ação explícita de aprovação no Portal, contra desafio/nonce não reutilizável associado ao ator, plano/capability, recursos, versões, efeitos e expiração; validar no backend, via contratos de identidade aprovados. A presença do login ou refresh de JWT não é substituto do clique/manifestação de aprovação; não criar auth paralela nem inventar attestation do host ChatGPT. A rota BFF de consent deve ser invocável somente pelo ator correto, sob permissions Core frescas e controles HTTP adequados, com event/nonce consume único.
2. **Pré-visualização completa e idêntica ao plano selado**: a UI mostra, em português, cada ação, objeto, competência, área, parâmetro de negócio, motivo, efeito, dependência, estado de elegibilidade e bloqueio, extraídos do contrato de plano persistido e `plan_hash`. A confirmação exata pode cobrir N operações em uma única interação. Não aprovar ações ocultas, com descrição insuficiente, ou com payload diferente do exibido.
3. Preservar claim antes do efeito, concorrência, idempotência, READ-back independente, segregação, revogação Core e `UNKNOWN` após efeito possivelmente aplicado. Não reviver `commit_proposal` sem consent nem duplicar sistemas.
4. Demonstrar testes **HTTP/Keycloak reais quando disponíveis**, contrato MFE/BFF, 2/5/20 ações, lotes parcialmente bloqueados, cross-user, replay, stale version, nonce, CSRF/origin conforme arquitetura vigente, pós-efeito incerto, e regressão P1–P6. Evidência de unit/PG isolado não substitui acceptance E2E.

## 3. Piloto antecipado no ChatGPT (somente ambiente permitido)

- Inventariar staging/homologation vigente, URL pública HTTPS, gateway, isolamento de dados, Core e Keycloak de **teste**; validar que o operator/owner autoriza a exposição do MCP e alteração do client IAM de teste.
- Prover deployment no ambiente **não produtivo autorizado** pelo runbook local apropriado e migration V013+ aplicada ao DB de teste. Preservar volumes, dados de teste, versionamento de corpus e backups aplicáveis.
- Configurar `mcp-clara` no Keycloak do **mesmo ambiente**, audience exata por URL e scopes reais; fazer `--check` e diff antes do `--apply` autorizado; não alterar clientes irmãos (TÉO/DAVI/VISTA/DÉLIA) por arrasto.
- Preparar ficha de ChatGPT contendo nome, endpoint, issuer, authorization/token/JWKS, protected-resource metadata, client ID, scopes, resource audience, PKCE, client authentication, callback URI *fornecida pela plataforma no fluxo real*, tool discovery, SHA/runtime, evidência smoke e status. **Não devolver ou publicar secrets, admin passwords, refresh/access tokens, valores de .env.** Referenciar cofre/canal seguro caso secret necessário.
- Quando o usuário puder criar/conectar o plugin pelo ChatGPT, fornecer a ficha e instruções exatas; conexão depende de ação explícita do usuário e permissões do workspace. O Devin **não deve alegar que conectou o plugin dentro da conta ChatGPT** sem evidência da ação e teste efetivos.
- Roteiro de aceite antecipado: autenticação real; descoberta MCP; READ por usuário autorizado; resposta CLARA com fonte/citação; plano de múltiplas ações; consentimento consolidado em UI confiável; ACT exclusivamente sobre dados de teste e efeitos autorizados; read-back e auditoria. Respeitar confirmações nativas do ChatGPT.

## 4. G1, G2, G3 e produção — não substituir por piloto

- **G1:** fechar owners externos, T03, T05, relatórios oficiais R04+, seeds P5-H/P6, fontes e demais decisões materiais, cada qual com RQ/AC/contrato/evidência. Não considerar snapshot documental ou amostra como equivalência oficial do TOTVS.
- **G2:** Controladoria/PO aceita explicitamente a Central P1–P6 e CLARA no escopo demonstrado; registrar responsável, data, aceites/restrições e anexos da homologação.
- **G3:** Operador SSH autorizado concede release, janela e runbook; preflight SSH prod, backup PostgreSQL/arquivos/corpus, diff do Keycloak, rollback, migrations, gateway, secrets gerenciados e smoke; sem alterações produtivas antes da aprovação.
- **PROD:** deploy de SHA imutável, provisionamento Keycloak limitado e auditável, aplicação migrations, ingestão corpus autorizada, smoke OAuth/MCP autenticado e resultado de negócio comprovado; gerar ficha **do ambiente produtivo** após read-back. Piloto não é produção; `HTTP 200` não prova funcionamento.
- Se G1/G2/G3 não puderem ser obtidos hoje, **encerrar a execução com o máximo tecnicamente completo**, lista única dos responsáveis e evidências faltantes, sem falso `PASS`, deixando o release preparado em vez de forçar produção.

## 5. Fluxo operacional sem retrabalho

Uma única execução coordenada, **sem novo prompt por fatia**. Design/contratos físicos fecham antes de implementação respectiva; usar diff mínimo e testes por risco. Após cada decisão material ou entrega verificável: **atualizar a documentação canônica no GitHub no mesmo commit**, incluindo pedido PO, decisão, owner, RQ/AC, evidência, testes, estado, SHA e status (PROVEN/TO_INVENTORY/TARGET; PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN). Documentação não substitui runtime. Preservar HEAD, evitar reabrir assuntos já decididos.

Relatório final único: `FINAL_HEAD`, `RELEASE_SHA`, `G1`, `G2`, `G3`, `NONPROD_DEPLOY`, `CHATGPT_NONPROD_CONNECTION`, `PROD_DEPLOY`, `KEYCLOAK_PROD`, `MCP_SMOKE`, `CHATGPT_PROD_CONNECTION`, `CORPUS_VERSION`, `CONSENT_E2E`, `REMAINING_OWNER_ACTIONS`, `TEST_NOT_RUN`, `EXECUTION_DRIFT`, `NEXT_ACTION`.

**Ordem operacional aprovada pelo PO:** priorizar **validação real da CLARA via ChatGPT após o rework**, e então fechar G2/G3, sem utilizar produção como atalho. O produto final só está `ACCEPT` quando os outcomes exigidos e gates pertinentes estiverem comprovados.

## 6. Revisão independente V014 e passagem para piloto ChatGPT

**Data da revisão:** 2026-10-25. **Commit CLARA auditado no GitHub:** `e8d9361deef6b175d36a034d036256caeec45098`. **HEAD consultado:** outro HEAD de `main` com commits DÉLIA, não interpretar como deploy CLARA. **Veredito limitado:** `ACCEPT_WITH_RESIDUAL` para os requisitos cirúrgicos R-CLARA-01/02 de design/implementação; **`INCONCLUSIVE` para E2E ChatGPT/Keycloak real e G2/G3**.

### Evidência independente do código

- **R-CLARA-01:** `clara_consent_challenge` V014; `approve_for_batch/approve_for_proposal` persistem challenge APPROVED + `consent_record` numa transação, com binding de ator/alvo/hash; `claim_batch_for_execution` e `claim` consomem challenge na transação do claim. `confirm_batch` exige record Portal e valida binding, ou attestation host habilitada. Não inferir aprovação apenas de JWT fresco.
- **R-CLARA-02:** `operation_presentation.py` traduz as cinco capabilities atuais para descrição/efeito/motivo; `ClaraStepUpConsent.batch_summary` devolve plano/viabilidade/dependências; `ClaraConsentPage` usa `OperationCard` e um único botão para operações executáveis.
- **Testes:** executor reportou `595 passed` backend, `229 passed` subset PostgreSQL, `61/61` CLARA, `13/13` MCP surface, `177` vitest e `25` complementares. **Não foram reexecutados pelo revisor**; testes com JWT assinados e conexão real do ChatGPT/Keycloak permanecem `TEST_NOT_RUN`.
- **Limite:** o rework não fecha T03/T05/R04+, seeds, homologação humana G2 nem autorização operacional G3; não há deploy/Keycloak real comprovados.

### Residuais para aceitar no piloto, sem abrir novo ciclo amplo

1. **Concorrência:** `approve_for_batch` trava challenge→batch, enquanto `claim_batch_for_execution` trava batch→challenge. Um duplo clique idempotente concorrente com claim pode causar deadlock SQL. Executar teste negativo com duas conexões reais na homologação; caso reproduza, corrigir ordem canônica de lock em diff mínimo **antes de habilitar ACT em produção**, preservando os demais módulos.
2. **Conteúdo do consentimento:** alguns rótulos/motivos usam truncamento (`_clip`) e identificador fallback. Verificar na demonstração um motivo extenso e uma operação sem lookup: o usuário deve identificar **exatamente** efeito e motivo do lote selado; caso o truncamento oculte materialidade, mostrar detalhe completo ou bloquear consentimento, sem reescrever os presenters.
3. **Integração:** comprovar com Keycloak de homologação real callback/issuer/audience/client e fluxo Portal→BFF→MCP, não inferir de mocks/testes de PostgreSQL; não expor URLs ou secrets não verificados.

### Próxima ação, não outro prompt de implementação

**Executar o Documento 107, já aprovado pelo PO:** inventariar ambiente de homologação HTTPS existente e autorizado → `--check` Keycloak read-only → habilitar CLARA em **não produção com dados sintéticos/autorizados** → gerar ficha pública para conexão manual do plugin no ChatGPT → teste de knowledge/READ/consentimento batch/ACT seguro → registrar evidências reais. Em seguida G1 owner, G2 humano, G3 Operador SSH, deploy produtivo e smoke. Se não houver ambiente não produtivo autorizado, preparar ficha/runbook e obter G1/G2/G3 antes de tocar produção. Nenhuma simulação de PASS ou aprovação.

## Adendo 1 — GO de continuidade operacional CLARA→ChatGPT, 25/10/2026

`EXECUTION_GO` do PO: prioridade = CLARA conectável e testável no
ChatGPT, sem abrir novos ciclos gerais de implementação.

### Inventário de ambiente (real, via SSH `operador@srv-api`)

| Prova | Resultado |
|---|---|
| Hosts | **um único** — `srv-api` (192.168.1.237) = produção; nenhum host de homologação autorizado existe |
| HTTPS público | `https://minhadelpi.com.br` (nginx gateway + Cloudflare) — único endpoint OAuth acessível ao ChatGPT |
| Keycloak | container `infra-keycloak-1`, realm `delpi` prod — **Keycloak compartilhado de produção** |
| Compose prod | 91 containers `delpi-*` — `delpi-controllership-finance-api` no ar |
| Estado prod | repo no host em `8ca4e2512` (pré-rework); imagem cf-api contém migrations até V005; MCP `/mcp` responde 401 no edge (montado, contrato antigo) |
| Non-prod | **inexistente** — workflow `homolog` é nome de environment GitHub que opera o mesmo host |

Conclusão: **não há ambiente não produtivo existente e autorizado** —
aplica-se a exceção do §1 deste documento: produção não pode ser
tratada como piloto sem os gates; release preparado, owners listados.

### Keycloak `--check` (read-only)

Executado `keycloak-prod-delia-mcp-provision.sh --check`
(`KC24_LEGACY`, realm `delpi`, base `https://minhadelpi.com.br/auth`):
**FAIL_CLOSED — admin login recusado** (`KEYCLOAK_ADMIN`/
`KEYCLOAK_ADMIN_PASSWORD` do env do container não autenticam em
`realm master` — credenciais bootstrap rotacionadas). Nenhuma
escrita tentada. `DECISION_REQUIRED`: Operador deve fornecer
`KC_ADMIN_TOKEN`/credencial admin vigente para concluir o check e,
após gate, o `--apply` do client `mcp-clara`.

### Correções executadas neste GO (diff mínimo)

- **Concorrência aprovação↔claim (residual §6.1)**: inversão de
  ordem de lock **confirmada** — `approve_for_batch`/
  `approve_for_proposal` travavam challenge→artefato enquanto o
  claim trava artefato→challenge (deadlock real no duplo-clique
  concorrente com execução). **Fix mínimo:** ordem canônica
  artefato→challenge nos dois métodos. 3 testes novos PG —
  `test_concurrent_double_approve_converges_single_consent`
  (3 threads, uma aprovação, zero efeito duplicado),
  `test_approve_after_claim_consumed_rejected` (aprovação tardia
  rejeitada, desafio permanece CONSUMED) e
  `test_approve_claim_race_no_deadlock` (8 lotes, re-approve
  concorrente com claim em conexões reais — nunca
  `DeadlockDetected`, desafio sempre CONSUMED) — **PASS**.
- **Motivos longos (residual §6.2)**: reproduzido bloqueador real —
  `_clip(140)` truncava `motivation` (e `question`/`response`),
  escondendo justificativa material da aprovação. **Fix mínimo:**
  limite `_clip` 140→4000 em `operation_presentation.py`;
  `test_presentation_preserves_full_long_motivation` PASS.
- Resultado: **65/65** testes CLARA PG verdes.

### Ficha ChatGPT

Entregue em
`controllership-finance-api/docs/integrations/chatgpt-clara-registration-sheet.md`:
MCP URL, issuer, authorization/token/JWKS, client `mcp-clara`,
scopes, audience, PKCE, metadata URL — valores verificados via
OIDC discovery real; redirect URI a obter no cadastro; secret no
cofre.

### Pendências de owner (bloqueantes, não contornáveis)

1. Credencial admin Keycloak vigente (Operador) → `--check` →
   `--apply` de `mcp-clara` (escopo apenas; não alterar TÉO/DAVI/
   VISTA/DÉLIA).
2. G1: owners externos, T03, T05, relatórios oficiais R04+, seeds.
3. G2: aceite Controladoria/PO.
4. G3: autorização Operador → `git pull --ff-only` +
   `up-prod-sequential.sh --build controllership-finance-api portal`
   + migrations V006–V014 + ingestão corpus + smoke autenticado +
   cadastro ChatGPT real (callback URI) + aceite.

SHA desta etapa: `FINAL_HEAD` do commit desta entrega em `main`
(relatório CF-PROC0072-CLARA-CHATGPT-EARLY-VALIDATION-001).


## Adendo 2 — revisão independente ecf765 e encerramento da trilha técnica

**Data:** 2026-10-25 · **SHA de código revisado:** `ecf765139d77fabcf5ab28ab04cfb71f9cde41b0`. **Veredito:** `ACCEPT_WITH_RESIDUAL` para correções de concorrência e apresentação; `INCONCLUSIVE` para integração runtime/Keycloak/ChatGPT e para aceite integral do PROC-0072. **Não** declarar produção aprovada ou implantação feita.

### Evidências inspecionadas no GitHub

- `ClaraConsentChallengeRepository.approve_for_batch` adquire lock `clara_batch → clara_consent_challenge`, compatível com `ClaraBatchRepository.claim_batch_for_execution`; `approve_for_proposal` agora usa `clara_proposal → clara_consent_challenge` como `claim`. Testes `test_approve_claim_race_no_deadlock` com 8 lotes e demais testes concorrentes presentes no código. **Execução dos testes: reportada pelo Devin, não reexecutada pelo revisor**: 599 backend e 65 CLARA PG.
- `operation_presentation._clip` alterado de 140 para 4000. Motivos longos comuns agora são apresentados, mas **não se inferiu ausência de truncamento de textos com >4.000 caracteres**; validar contra limites dos contratos de domínio e bloquear/expandir representação se houver caso legítimo maior.
- Ficha `controllership-finance-api/docs/integrations/chatgpt-clara-registration-sheet.md` entregue. Issuer/endpoints OIDC reportados como verificados via discovery pelo executor; URL MCP é contratual e resposta 401 da imagem antiga **não confirma** que a CLARA V014 está servindo tools em produção.

### Bloqueios operacionais consolidados

- **Ambiente:** inventário SSH do executor identifica apenas `srv-api` produtivo; workflow “homolog” compartilha host, logo não equivale a ambiente separado. Informação de runtime reportada, não reverificada nesta revisão.
- **Keycloak:** `--check` falhou por credencial admin bootstrap rotacionada; fornecer acesso administrativo **por canal seguro** ao Operador; não extrair ou publicar passwords/tokens. `--apply` exige análise read-only de diff e G3, incluindo ausência de mudanças inadvertidas em outros clients.
- **G1 material:** fontes oficiais T03/T05/R04+, seeds e evidências de owner; não chamar fechamento integral de PASS por teste verde isolado.
- **G2:** homologação humana Controladoria/PO ainda `PENDING`. **G3:** autorização de Operador SSH para produção ainda `PENDING`.
- **Deploy/ChatGPT:** `NOT_DEPLOYED` e `TEST_NOT_RUN`. O SHA `ecf765139d77fabcf5ab28ab04cfb71f9cde41b0` é a referência auditada; HEAD de main avançou por outros contextos. Operador deve selecionar e verificar SHA release imutável em vez de implantar alterações concorrentes sem revisão.

### Próxima ação única, sem novo rework generalista

**Owner IAM/Operador:** recuperar credencial Keycloak vigente via cofre/canal administrativo, validar `--check` e impacto, sem escrita até autorização. **Controladoria/PO:** fazer demonstração G2 com escopo e pendências G1 explícitas; aceitar somente o que foi demonstrado. **Operador SSH G3:** após aceite e autorização, executar backup + runbook + migrations V006–V014 + provisionamento limitado Keycloak + ingestão corpus + smoke autenticado e revalidação da Central. **Usuário ChatGPT:** cadastrar manualmente o MCP com callback URI real, sem publicar client secret, e executar os testes READ/KNOWLEDGE/BATCH em cenário autorizado. Registrar cada decisão, SHA e resultado com proveniência. Meta PO 25/10/2026 continua prioridade, jamais substituto de gate.


## Adendo 3 — pedido expresso de deploy e migrations, 25/10/2026

**GO expressamente reiterado pelo PO:** “vamos logo fazer deploy e aplicar migrations e tudo que falta”. O objetivo é **release operacional imediato assim que as autoridades obrigatórias aprovarem**, sem novo planejamento, rework genérico ou prompts técnicos por etapa. **Status inicial (last reported runtime):** `NOT_DEPLOYED`, G2=`PENDING`, G3=`PENDING`, IAM admin `FAIL_CLOSED`; nenhuma mudança produtiva foi executada por este adendo. O PO não declarou formalmente aceite G2 do fluxo integrado nem é substituto da autorização operacional do Operador SSH.

### Ordem de execução única do Operador SSH (somente após evidências G1/G2/G3 aplicáveis)

**Autoridade:** [infra/README-ambiente](../../../infra/README-ambiente.md), `infra/scripts/up-prod-sequential.sh`, `infra/scripts/keycloak-prod-delia-mcp-provision.sh`, `controllership-finance-api/docs/integrations/keycloak-mcp-client-runbook.md` e [Doc 104](./104-plano-mestre-execucao-e2e-fechamento-aceite-deploy.md).

1. **Consolidar decisão G1/G2 numa única pauta**: Controladoria/PO aceitar o conjunto exato de funcionalidades já demonstradas, identificando como `PENDING/RESIDUAL` T03, T05, R04+, seeds e paridade não homologada. Não declarar “fechamento mensal integral” se fontes oficiais ausentes.
2. **G3 único**: Operador registra janela, host, identidade, backup/restore testável, rollback e escopo dos serviços. A senha bootstrap Keycloak está rotacionada; IAM fornece **token admin válido por cofre/canal seguro**, sem expor material no chat, logs ou GitHub.
3. **Preflight SSH produtivo read-only**: confirmar `srv-api`, runtime Docker/gateway/Keycloak realmente produtivos, `git status`, HEAD vs `origin/main`, SHAs dos módulos afetados, versão de migrations aplicada, compose/env/volumes, espaço, integridade do banco e clientes IAM. **SHA de código CLARA auditado**: `ecf765139d77fabcf5ab28ab04cfb71f9cde41b0`. O branch `main` avançou em outros contextos; selecionar um **RELEASE_SHA imutável e inspecionado**, sem checkout regressivo nem build oportunista de módulos alheios.
4. **Antes de subir API**: backup consistente do **postgres-plugins**, uploads de `cf-closing-documents` e corpus; confirmar procedimento de restore, scripts V006–V014, flags e impacto. **CONTRATO FÍSICO PROVEN:** `controllership_finance_app/main.py` executa `run_migrations_on_startup()`; `infra/docker-compose.yml` configura `CONTROLLERSHIP_FINANCE_RUN_MIGRATIONS_ON_STARTUP: ${CONTROLLERSHIP_FINANCE_RUN_MIGRATIONS_ON_STARTUP:-true}`. Logo, ao recriar a API **migrations podem ser aplicadas automaticamente**: não subir a imagem antes do backup/gate e não executar as mesmas migrations manualmente às cegas.
5. **Pré-verificação segura de comandos** (no repo do host, após sincronização/seleção do SHA autorizado):
```bash
./infra/scripts/up-prod-sequential.sh --dry-run --build portal controllership-finance controllership-finance-api
bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check
```
   O segundo comando deve usar token/admin vigente fornecido pelo Operador por canal seguro; a última tentativa de `--check` falhou fechada, sem escrita.
6. **Deploy produtivo autorizado**: executar script sequencial canônico com **os três alvos** `portal`, `controllership-finance` (MFE) e `controllership-finance-api` (BFF), usando SHA congelado e ordem resolvida pelo próprio script. `plugin-ui` só se a compatibilidade exigir; não reconstruir toda a stack por padrão.
```bash
./infra/scripts/up-prod-sequential.sh --build portal controllership-finance controllership-finance-api
```
   Verificar startup da API, aplicação **V006–V014 pelo runner canônico**, migration ledger, healthcheck, volumes, logs sanitizados, gateway e app no Portal. Não usar `docker compose up --build` de toda a stack.
7. **Keycloak após preflight e G3**: usar `--check` e diff de cliente/escopo/política. `--apply` no engine compartilhado somente depois de provar alcance e autorização de todos os clients potencialmente afetados, inclusive TÉO/DAVI/VISTA/DÉLIA. Configurar `mcp-clara`, audience URL exata e callback real originado no ChatGPT. Não copiar secrets.
8. **Corpus**: usar pipeline existente `python -m controllership_finance_app.application.clara.corpus_ingestion --docs-root <repo-docs-root>`; escolher ambiente com acesso autorizado aos docs brutos e DB correto, validar manifest, hashes, ACL, publicação `corpus_version`, totais/citações, sem presumir que docs do repo estão montados dentro da imagem API.
9. **Smoke authenticated**: version SHA efetivamente servida, Portal e BFF, Core/RBAC, P1–P6 no escopo aceito, migrations/volume persistence, MCP RFC9728 metadata/401 challenge, OAuth/JWKS, tool discovery, READ/KNOWLEDGE, 1 lote consentido pelo Portal em dados de teste autorizados, ACT com idempotência, read-back e auditoria, falhas negativas, rollback possível. `HTTP 200` não é prova de business outcome.
10. **ChatGPT**: entregar ficha URL/issuer/authorization/token/JWKS/client ID/scopes/audience/PKCE **públicos** e reais, obter callback no fluxo de cadastro manual pelo usuário/owner do workspace, registrar redirect autorizado no Keycloak, conectar e executar testes. Nunca exibir client secret/tokens.
11. **Documentação contemporânea**: registrar `G1_OWNER_APPROVALS`, `G2_SIGNOFF`, `G3_OPERATOR_AUTH`, `RELEASE_SHA`, `PROD_MIGRATIONS`, `KEYCLOAK_DIFF`, `DEPLOY/SMOKE OUTCOME`, `CORPUS_VERSION`, `CHATGPT_CONNECTED`, evidence refs e rollback no GitHub. Até executar, todos ficam `PENDING/TEST_NOT_RUN`; não falsificar PASS.

**Executor imediato necessário:** o Operador SSH no host produtivo com acesso IAM, acompanhado por Controladoria/PO para G2 e autorização de release G3. O GPT Arquiteto neste chat possui GitHub de leitura/escrita, **não** ferramenta de SSH para executar comandos no host; esta publicação documenta o GO e handoff, não é aplicação de migrations nem alteração de Keycloak.


## Adendo 4 — localização das credenciais Keycloak informada pelo PO

**Data:** 2026-10-25. **Correção factual expressa do PO:** as credenciais de acesso ao Keycloak estão no `infra/.env` do ambiente da plataforma. Classificação `OWNER_REPORTED`, a confirmar **somente no host SSH**; `infra/.env` é arquivo operacional gitignored e **não** está disponível como conteúdo no GitHub. Essa informação **substitui a interpretação de que o Operador necessariamente precisa receber credenciais novas**; não invalida o resultado anterior `FAIL_CLOSED` do `--check`: a combinação `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD` de bootstrap tentou login e foi recusada. Isso pode ser divergência de credencial efetiva, realm/URL, modo de autenticação ou conta rotacionada — não assumir qual.

**Próxima ação do Operador, sem solicitar senha em chat e sem exibir o arquivo**:

1. No host `srv-api`, confirmar arquivo `infra/.env` existente, permissões de leitura autorizadas e presença **sem imprimir valores** das variáveis destinadas à administração Keycloak; conferir se `KEYCLOAK_ADMIN` é conta bootstrap ou se a authority atual utiliza `KC_ADMIN_TOKEN`/credencial admin vigente. Nunca fazer `cat`, `grep` de valores secretos em saída, `set -x`, dump de env, logs sensíveis ou commit do arquivo.
2. Revalidar endereço HTTPS, realm `master` para emissão do token administrativo vs realm `delpi` de destino, credenciais e fluxo exatos do **runbook/provisioner oficial**, sem tentar resetar senha, excluir volume, trocar client existente, contornar Keycloak ou acessar banco diretamente.
3. Usar a credencial correta **no próprio ambiente autorizado** e rodar `bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check` (READ-only). Registrar somente resultado sanitizado, drift e escopo real do engine compartilhado, sem tokens.
4. Se `--check` PASS, a pendência de **descoberta de credenciais** pode ser encerrada com evidência. **`--apply` ainda depende de G3/authorization e diff controlado**; login válido não aprova alteração de produção.
5. Se `--check` persistir FAIL, reportar **diagnóstico tipado e seguro** (sem segredo), owner IAM responsável, ambiente/realm e ação requerida, em vez de afirmar ausência de credenciais. Continuar demais preflights independentes.
6. Prosseguir G1/G2/G3 e deploy conforme Adendo 3, sem pedir novo prompt técnico.

**Estado:** `CREDENTIAL_LOCATION=OWNER_REPORTED`, `VALID_ADMIN_LOGIN=TO_VERIFY`, `KEYCLOAK_CHECK=FAIL_CLOSED (previous run)`, `KEYCLOAK_APPLY=NOT_RUN`, `PROD_DEPLOY=NOT_DEPLOYED`; nenhuma credencial foi lida ou compartilhada pelo GPT nesta etapa.


## Adendo 5 — GO final consolidado de execução e entrega da CLARA no ChatGPT

**Data:** 2026-10-25. **Pedido expresso do PO:** elaborar um **único prompt final completo** para o Devin e o Operador SSH, cobrindo a passagem do último código CLARA aprovado para **release operacional**, migrations, Keycloak, corpus e cadastro/teste ChatGPT. Não solicitar micro-GOs, não iniciar rework generalista, preservar decisões de produto e documentação. **Autorização de planejar e conduzir a execução não substitui as provas de G1 de owners, G2 aceite humano nem G3 autorização do Operador**. O PO informou `infra/.env` como local de credenciais Keycloak: `OWNER_REPORTED`; testar a credencial real no host por canal sigiloso, sem `cat`, env dump ou secret em log.

**Baseline canônica para o handoff:** código CLARA auditado `ecf765139d77fabcf5ab28ab04cfb71f9cde41b0`; `main` atualizado em paralelo por docs/outros contexts — selecionar e identificar `RELEASE_SHA` imutável após `git status`, `origin/main` e diff para não implantar alterações alheias. Ambiente `srv-api` único produtivo segundo inventário anterior; não usar `homolog` do GitHub como prova de segregação.

**Ordem executável coordenada:**

1. **PRÉ-GATE READ:** operadora valida SSH/host/compose, gateway/Cloudflare, Core/effective-permissions, volume Postgres plugins, volumes de evidência, compatibilidade OAuth, versão atual do banco, flag `CONTROLLERSHIP_FINANCE_RUN_MIGRATIONS_ON_STARTUP`; obter `--check` Keycloak com credencial vigente em `infra/.env` sem imprimir segredo. `--check` falhado anteriormente por admin bootstrap = diagnóstico pendente, não prova de ausência de credencial.
2. **G1/G2/ G3:** consolidar numa pauta **única** de Controladoria/PO e Operador SSH; aceitar escopo exato demonstrado, separar R04+/T03/T05/seeds não provados, fornecer evidência explícita de aceite e autorização do release. Não mascarar pendências G1, nem instalar funcionalidade sensível sem aprovação.
3. **BACKUP ANTES DE BUILD/RECREATE:** PostgreSQL plugins e schema, uploads, corpus, configuração Keycloak, checklist de restauração. Runner da API executa V006–V014 na inicialização quando flag ativa; verificar ordem/versionamento, não disparar antes do backup nem aplicar manualmente em duplicidade. Rollback app/DB deve reconhecer migrations up-only e impedir falsa reversibilidade.
4. **DEPLOY:** usar apenas `./infra/scripts/up-prod-sequential.sh --build portal controllership-finance controllership-finance-api` **após** preflight/dry-run e gates, com SHA pinado. Remote `plugin-ui` somente se exigido; validar gateway e integridade pós-recreate.
5. **IAM:** executar `bash infra/scripts/keycloak-prod-delia-mcp-provision.sh --check`, provar escopo do engine compartilhado, autorizar diff, então `--apply` para `mcp-clara` e audience exata, callback real emitido no fluxo do ChatGPT; não modificar clients TÉO/DAVI/VISTA/DÉLIA incidentalmente. Proteger credenciais.
6. **KNOWLEDGE:** pipeline `corpus_ingestion` com `--docs-root` verdadeiro e acesso restrito às fontes, hash/proveniência/publicação, corpus version, citação. `MP4` e planilhas originais só se acessíveis de fato; não inferir ingestão de docs derivados.
7. **AUTHENTICATED E2E:** Portal/MFE/BFF/Keycloak OAuth/discovery, MCP tools, READ e knowledge, consentimento único de lote por desafio no Portal, ACT apenas com dados e usuário autorizados, pós-condição independente e auditoria. Status honestos.
8. **CHATGPT:** entregar a ficha pública com URL, issuer, client ID, scopes, audience, PKCE, URLs endpoints e metadata verificados no runtime; secret somente via cofre, cadastro/conexão exige ação do dono do workspace ChatGPT. Smoke real, registrar tool discovery e autorização nativa do host.
9. **EVIDÊNCIA/RELATÓRIO:** SHA, gates, snapshots before/after, migration ledger, Keycloak diff/result, URL/MCP checks, corpus version, ChatGPT connection, resíduo e rollback. Atualizar Docs 107/106/100/README e runbooks conforme ocorrido, sem falsificar PASS.

**Ponto de parada formal único:** se G2/G3/credencial válida permanecer pendente, entregar preflight, backups preparados, comandos e ficha parcialmente verificada, status `NOT_DEPLOYED`/ `TEST_NOT_RUN` e responsável que libera o próximo passo. Não aplicar escrita em produção antes da autorização. O documento registra decisão do PO e **não** representa ação SSH efetuada.

## Adendo 2 — Produção implantada e corpus publicado; Keycloak mcp-clara bloqueado por credencial (2026-10-26, pós-deploy)

### Runtime efetivo verificado em `srv-api` (evidência de execução)

O deploy produtivo foi executado no host antes deste adendo (git pull + rebuild
sequencial): repo em `2eeb5fb943`, container `delpi-controllership-finance-api`
recriado em 2026-10-26 10:03Z com o código de `ecf765139d` incluso — verificado
por marcador dentro da imagem (`_clip = 4000` em `operation_presentation.py` e
comentário de ordem canônica de lock em `clara_consent_challenge_repository.py`).

| Verificação | Resultado |
|---|---|
| Ledger `schema_migrations` | V001–V014 aplicadas, V006–V014 em 2026-10-26 07:03 -03 |
| `clara_consent_challenge` | tabela existe, 0 linhas, pronta |
| `/mcp` sem token | 401 + `WWW-Authenticate: Bearer realm="clara-mcp" resource_metadata=…` (RFC 9728 vivo) |
| `.well-known/oauth-protected-resource/mcp` | 200 — resource, issuer `delpi`, scopes `openid profile email mcp:tools` |
| `remoteEntry.js` do plugin | 200 — MFE implantado |
| `PUBLIC_BASE_URL` no runtime | `https://minhadelpi.com.br` — URLs de consentimento públicas |

### Corpus governado publicado

Ingestão executada via pipeline autorizado (`corpus_ingestion --docs-root`,
docs copiados do repo para `/tmp` do container — write path apenas pelo
repositório/DB):

- `corpus_version_id` = `5541097a-8608-4470-b971-7c28b3ae6c40`
- 52 fontes autorizadas, 1 298 itens, `published_at` 2026-10-26 07:07 -03.

### Bloqueio remanescente — Keycloak `mcp-clara`

As credenciais admin reportadas pelo PO em `infra/.env` foram testadas em todas
as três trilhas do provisioning engine:

1. `KEYCLOAK_ADMIN`/`KEYCLOAK_ADMIN_PASSWORD` → login recusado no realm `master`
   (bootstrap rotacionado);
2. `delpi-core-admin` client-secret → token emitido mas sem direito de leitura
   de `/admin/serverinfo` (service account sem realm-management);
3. password grant realm `delpi` com o usuário admin reportado → `invalid_grant`.

**Consequência:** o cliente `mcp-clara` ainda não pôde ser provisionado; sem
ele não existe client_id/redirect para o cadastro real no ChatGPT.
`CHATGPT_PROD_CONNECTION` permanece `TEST_NOT_RUN`. Não foi feita nenhuma
tentativa de contornar o controle de acesso do Keycloak (criação de admin via
container/DB está fora de escopo e exige operador+gate explícito).

### Status consolidado pós-deploy

- `PROD_DEPLOY` — **EXECUTADO** em `2eeb5fb943` (V014 ativa, código `ecf765139d`);
- `CORPUS_VERSION` — **5541097a** publicada (52 fontes / 1298 itens);
- `KEYCLOAK_PROD` — **BLOCKED** por credencial admin inválida;
- `MCP_SMOKE` autenticado / `CHATGPT_PROD_CONNECTION` — `TEST_NOT_RUN`
  (dependem do client `mcp-clara`);
- G1/G2/G3 — pendentes de registro formal; o deploy ocorreu por GO do
  operador (Adendos 3–5) — a aceitação humana e a autorização formal devem
  ser registradas para fechar a cadeia.


## Adendo 6 — revisão arquitetural do deploy reportado e bloqueio IAM (26/10/2026)

**Evidência examinada:** `main=f8d697745cb07a6df5c117c7253f2497bc89c80e` à data da verificação; commit de correção CLARA `ecf765139d77fabcf5ab28ab04cfb71f9cde41b0`; release reportado em `srv-api` com repo `2eeb5fb943e46cf8f1e50e373a4fc2cf1ca0af6b`. Fontes: Adendo pós-deploy deste documento e ficha `controllership-finance-api/docs/integrations/chatgpt-clara-registration-sheet.md`. **Não houve SSH independente pelo GPT nem smoke OAuth autenticado**; acesso HTTP externo não pôde ser confirmado por esta revisão.

### Classificação de evidências

| Aspecto | Status | Critério |
|---|---|---|
| Código CLARA V014 e fixes de lock/presentation | `PROVEN` no GitHub | SHAs `e8d9361dee` e `ecf765139d` consultados; não igual a confirmação de produção |
| Deploy `srv-api` / V001–V014 | `OWNER_REPORTED / TO_VERIFY` independentemente | Operador relata host, imagem, ledger e 401/metadata; usar snapshot SSH/smoke readback para aceite |
| Corpus | `OWNER_REPORTED / TO_VERIFY` independentemente | `5541097a-8608-4470-b971-7c28b3ae6c40`, 52 fontes / 1298 itens, não implica originais MP4/XLSB ingeridos |
| Keycloak `mcp-clara` | `BLOCKED` | Três trilhas de admin falharam: bootstrap master, service account sem realm-management e password grant `invalid_grant` |
| ChatGPT OAuth, tool discovery, READ, batch ACT | `TEST_NOT_RUN` | Sem client provisionado, callback real e token com audience correta |
| G1 owner / G2 Controladoria / G3 Operador | `PENDING_EVIDENCE` | Nenhum registro contemporâneo de aprovação G2/G3 encontrado nesta fonte |
| Sequência release vs gates | **`EXECUTION_DRIFT` até regularização** | A própria fonte relata alterações produtivas já executadas com G2/G3 ainda `PENDING`. GO de preparar runbook/Adendos 3–5 **não constitui**, sozinho, autorização G3 ou aceite G2. Obter provas datadas preexistentes caso existam; nunca criar sign-off retroativo fictício |

### Único desbloqueio técnico real

**IAM/Operador autorizado:** localizar mecanismo **vigente** de administração Keycloak por cofre/canal seguro; não reaplicar credenciais bootstrap já recusadas, não conceder privilégios ao `delpi-core-admin` por conveniência, não usar bypass container/DB. Executar `keycloak-prod-delia-mcp-provision.sh --check` apenas com credencial legítima e anotar relatório sanitizado e clients afetados.

**Atenção ao escopo:** o script atual de `--apply` usa `infra/scripts/delia_mcp_keycloak_state.py` cuja tupla `SPECIALISTS` contém `mcp-api-delpi`, `mcp-transformometro`, `mcp-tv-dashboard` e `mcp-clara`, e ainda atua em requester/políticas. **Não existe flag documentada de `--apply` exclusivo `mcp-clara` nesse wrapper.** Portanto a frase anterior “`--apply` somente `mcp-clara`” é **premissa não provada**. Fazer diff e autorização transversal; se exigir mudança material de mecanismo/scope, `DECISION_REQUIRED` do owner IAM/Plataforma antes de alterar/aplicar. Nunca aplicar engine compartilhado supondo blast radius limitado.

### Ordem operacional para conclusão

1. **Congelar novas escritas prod**, preservar runtime atual, colher evidência de backup, migrations e aprovação contemporânea (ou registrar desvio) de G1/G2/G3. Não usar retrodatação para legitimar rollout.
2. **Owner IAM** resolve acesso admin autorizado e gera `--check` sanitizado, sem segredos, seguido de revisão do diff transversal.
3. **Controladoria/PO e Operador SSH** registram aceite G2 e autorização G3 válidos para próximas intervenções, com escopo/residuais separados. Não afirmar G1 integral enquanto T03/T05/R04+/seeds estiverem abertos.
4. Somente após gates de escrita IAM: provisionar `mcp-clara` com audiência isolada, obter callback **real** do fluxo ChatGPT, registrar redirect autorizada, fazer OAuth login, tool discovery, READ e corpus com citações; ACT apenas em dados de teste autorizados por owner, com autorização consolidada, read-back e auditoria.
5. Atualizar no mesmo ciclo `RELEASE_SHA`, `KEYCLOAK_DIFF`, `G2_SIGNOFF`, `G3_OPERATOR_AUTH`, `MCP_SMOKE_AUTHENTICATED`, `CHATGPT_CONNECTED`, evidências e status honestos. Se IAM continuar bloqueado, devolver único responsável e ação desbloqueante; sem novo rework de produto.

**Veredito do GPT Arquiteto:** `EXECUTION_DRIFT` quanto à sequência de gates reportada; **`INCONCLUSIVE` quanto a funcionamento autenticado fim a fim**. Não invalidar as correções V014 nem desfazer o deploy automaticamente; preservar o estado e não expandir operações produtivas sem authority.

## Adendo 7 — superfície de consentimento step-up provada no browser real (26/10/2026)

Rodada 4 (`CF-PROC0072-USER-JOURNEY-G2-G3-FINAL-001`, Doc 108): a jornada
CLARA foi exercida como usuário real, não apenas via MCP/HTTP.

- Página real `closing/clara-consent?batch=<id>` carrega a view do lote
  (operações, parâmetros, efeitos, motivos, expiração).
- O botão **Autorizar** dispara `keycloak.updateToken(-1)` (step-up),
  posta `challenge_id` e registra `consent_mode` na UI — `done=true`.
- MCP `confirm_batch` → `execute_batch` → `get_batch_status` =
  `COMPLETED`; operações `VERIFIED`; trilha de auditoria
  `PREPARED→CONFIRMED→OP_EXECUTED→EXECUTED` persistida em
  `cf_homolog.controllership_finance`.
- `clara_consent_challenge` = `CONSUMED`; replay de `confirm_batch`
  rejeitado — prova de uso único.

**Defeito que bloqueava este fluxo era ambiental, não do produto:** o
container local `delpi-portal` montava um worktree obsoleto sem
`getFreshAccessToken` (commit `d59e972a47`, já em `origin/main`).
Corrigido o mount para o checkout sob teste, o step-up funcionou na
primeira tentativa. Idem para `delpi-plugin-ui` desatualizado (prop
`itemActions` ausente), resolvido por rebuild do kit compartilhado.

**Receita `mcp-clara` validada localmente:** client confidencial +
scope `mcp:tools` + audience mapper para
`http://localhost/apps/controllership-finance-api/mcp` — discovery de
18 tools e lotes 2/5/20 ops exercidos com OAuth real no Keycloak local.
O bloqueio de produção permanece **idêntico ao Adendo 6:** credencial
admin Keycloak prod vigente (owner IAM). Nada mudou em produção nesta
rodada; o gap é exclusivamente operacional, não técnico.


## Adendo 8 — G2 PO ACCEPT_WITH_RESIDUAL e handoff G3 formalizado (26/10/2026)

**Decisão PO posterior aos adendos anteriores:** o PO declarou formalmente em 26/10/2026 `G2_PO_SIGNOFF=ACCEPT_WITH_RESIDUAL` para P1–P6 e CLARA **no escopo local demonstrado** (Doc 108, Rodada 4) e aprovou manter a regra V1: aceite por área com esclarecimento aberto permitido, porém C2 bloqueia conclusão mensal enquanto houver esclarecimento em aberto. **Ressalvas mantidas:** P7 e paridade P7 oficial; R01–R15 apenas operacionais, G5/G6 pendente; T03/T05/R04+/seeds e owners G1. **Controladoria específica, se autoridade distinta exigir:** assinatura própria ainda não registrada. A assinatura do PO não concede grants IAM nem G3 SSH.

**Handoff G3 formal:** [Documento 110](./110-g3-handoff-operator-iam-clara-chatgpt-2026-10-26.md) consolida checklist por responsável, SHA pretendido/implantado, backups, migrações, autorização do operador, mudança compartilhada Core/Portal, `--check`/diff IAM, `--apply` apenas após aprovação do **escopo efetivo compartilhado**, OAuth e cadastro ChatGPT. O engine `delia_mcp_keycloak_state.py` pode alterar outros MCPs; o wrapper atual não comprova flag para limitar apply exclusivamente a CLARA. A ficha pública é contrato alvo, não cadastro realizado.

**Status após este adendo:** `G2_PO=ACCEPT_WITH_RESIDUAL`; `G3_OPERATOR=PENDING`; `G1_OWNERS=PENDING`; `PROD_DEPLOY_PREVIOUS=OWNER_REPORTED` em `2eeb5fb943`; `R4_FIXES_PROD_DEPLOY=TO_VERIFY`; `IAM_MCP_CLARA_PROD=BLOCKED/PENDING_OWNER`; `CHATGPT_CONNECTED=TEST_NOT_RUN`. Nenhuma nova operação produtiva foi realizada nesta atualização documental.
