# 133 — Autorização operacional do Product Owner: deploy R1 + R2

**Data:** 2026-10-23  
**TASK_ID:** DELIA-ORCH-REFAC-R1R2-INTEGRATED-RELEASE-AND-HOMOLOGATION-01  
**Plano:** DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01  
**Autorização:** declaração explícita do Product Owner nesta conversa: "eu autorizo o deploy, coloque na documentação".  
**STATUS:** DEPLOY_AUTHORIZATION=YES_CONDITIONAL_GATES; DEPLOY_STATUS=NOT_EXECUTED_BY_THIS_RECORD; R3_AUTHORIZED=NO.

## Escopo autorizado

Deploy **produtivo governado da DÉLIA API** contendo as implementações acumuladas e aceitas com resíduos **R1/M01 + R2/M02–M03**, com testes locais e homologação produtiva da mesma versão após a promoção. A autorização dispensa nova solicitação administrativa genérica de deploy ao PO **se** o release proposto continuar estritamente nesse escopo e cumprir todos os gates de 16, 20, 25, 125, 129 e 130. Não autoriza outras aplicações, backend Core/Domain, migrations, credenciais, infraestrutura nova, mudança funcional, R3–R7 ou ações empresariais ACT.

**Referências de implementação/review:** R1 runtime `aac06af292162f31723c98c65cc104339fb022bd`, review `f7d24b380031d6167a21af7b7f86b75b9a37e26c`; R2 runtime `3e7b063de68139a4960b4aff5417dad4d3ade70b`, review `3f6765270e4c98663889deb2b2323adf8314699f`. Esses SHAs **não são automaticamente o SHA de deploy**: executor identifica HEAD candidato, conteúdo efetivo, configurações, imagem e alterações concorrentes; se o artefato contiver código de outros escopos não homologados, STOP e solicite decisão de release.

## Gates pré-deploy obrigatórios

1. Reancorar HEAD/origin/main/status, authorities e ledger; confirmar owner do deploy, host, serviço, build e procedimento existente. Não pressupor acesso SSH/ambiente.
2. Congelar RELEASE_CANDIDATE_SHA e incluir seus recursos R1 JSON e R2 imports; comprovar identidade checkout→build→imagem→runtime e rollback anterior testável.
3. Executar testes locais no candidato: backend completo, R1 fail-closed por composição real, R2 sanitização/projeção, arquitetura/import DAG, AP-01–20, segurança/AuthZ, generalização, CRI ON/OFF e cenários D4/D5/D5-R/D5-schema/D8/D8-R/N1 aplicáveis. Modelo local Ollama e eval live real quando necessários/disponíveis; ausência de prova material = STOP/TEST_NOT_RUN.
4. Revisão independente de readiness pela coordenação sobre evidence local e riscos; `ACCEPT_WITH_RESIDUAL` somente se nenhum residual material bloquear release. Esta autorização PO satisfaz o gate de consentimento **não** substitui o gate técnico/operacional.
5. Confirmar janela/impacto, procedimento já aprovado, usuário técnico/credenciais sancionadas, backup/rollback, sem alterações concorrentes não aprovadas. Nunca criar usuário, impersonar, usar password grant improvisado ou expor secrets.

## Execução e homologação

Com gates PASS, executor autorizado pode efetuar deploy da DÉLIA pelo script/fluxo operacional já existente, registrar digest da imagem anterior/nova, SHA/config/modelo/recurso, observabilidade e resultado do health (200 não é outcome). Testar 401/403, comportamento fail-closed, D4/D5/D5-R/D5-schema/D8/D8-R/N1 e continuidade contextual, com identidade autorizada. Postconditions empresariais exigem fonte Domain efetiva. Em falha material, interromper e executar rollback governado, relatando outcome real. Não declarar produção PASS sem teste e evidência.

## Evidência final e próxima etapa

Preencher `LOCAL_TEST_STATUS`, `INDEPENDENT_READINESS_REVIEW`, `DEPLOY_AUTHORIZATION=YES`, `DEPLOY_STATUS`, `RELEASE_CANDIDATE_SHA`, `IMAGE_DIGEST`, `PROD_SHA`, `MODEL_CONFIG`, `PROD_AUTH_HOMOLOGATION`, `BUSINESS_OUTCOME_STATUS`, `ROLLBACK_READY`, `EXECUTION_DRIFT` e `NEXT_STAGE_AUTHORIZED=NO`. Commit/push relatório e ledger com fatos, sem autopromoção de fase.

**Decisão:** autorização operacional para deploy R1+R2 registrada; execução física ainda pendente. Esta autorização é bounded e não permite prosseguir automaticamente para R3.
