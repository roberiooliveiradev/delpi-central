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
