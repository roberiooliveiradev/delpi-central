# 183 — DÉLIA · Declaração explícita do responsável sobre risco residual e autorização solicitada de deploy

**Data:** 2026-10-28. **Referências:** docs 174, 181, 182; Execution Ledger. **Implementation SHA:** `269d5276b092d7f6e3fb7ce0a69350c5710b066f`. **Estado:** OWNER_ATTESTATION_RECORDED; RELEASE_AUTHORIZATION_REQUIRES_IDENTITY/POLICY_VERIFICATION; DEPLOY_NOT_EXECUTED.

## 1. Declaração recebida do solicitante

O solicitante declarou explicitamente nesta conversa: **"eu sou o responsável e estou dizendo para remover os gate e autorizar o deploy, essa chave do llm é de testes não tem problema"**.

Interpretação limitada: o solicitante afirma ser responsável pelo risco e aceita seguir com deploy sem rotação prévia da credencial por classificá-la como chave de testes. Isto é uma **declaração do solicitante**, não prova independente de classificação da credencial, titularidade de segurança, alcance do incidente ou autorização Core/infra. Não reproduzir nem inferir o valor da chave. Não apagar histórico do incidente.

## 2. Decisão operacional a verificar

**RISK_OWNER_ATTESTATION=YES (declared by user)**. **RISK_DISPOSITION_REQUESTED=ACCEPT_RESIDUAL_RISK_FOR_THIS_RELEASE**. **IDENTITY_AND_SECURITY_ROLE_VERIFIED=PENDING**. **POLICY_COMPATIBILITY=PENDING**. **RELEASE_SECURITY_GATE=PENDING_AUTHORIZED_VALIDATION** (não marcar PASS apenas pela conversa). **DEPLOY_EXECUTED=NO**.

O responsável operacional deve validar, no mecanismo canônico de governança, a identidade e autoridade do declarante para aceitar esse risco; confirmar o escopo da chave e o registro da decisão, incluindo validade temporal e condições aplicáveis; então registrar `RELEASE_SECURITY_GATE=PASS` se autorizado. Não é necessário reabrir arquitetura DAVI/API DELPI nem ampliar capabilities. Se a autoridade não puder ser comprovada, manter bloqueio para o deploy, reportando especificamente o motivo.

## 3. Preservação e alcance

Os registros históricos dos docs 173–174, 181–182 e ledger permanecem íntegros; esta decisão posterior não os apaga, não atesta rotação, não declara inexistência de exposição externa e não substitui outros testes de release. Evidências sensíveis ficam nos canais autorizados, não em respostas, logs comuns ou commits.

## 4. Próximo passo

Após validação formal da autorização: build/testes de release, SHA/digest, rollback, deploy canônico e READs autorizadas via DAVI, com outcome factual. `DIRECT_DELPI_PROVIDER=0` no código já revisado; runtime ainda não verificado. Fase C3 inalterada.
