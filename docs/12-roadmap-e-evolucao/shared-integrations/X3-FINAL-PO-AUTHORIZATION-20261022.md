# SHARED-INTEGRATIONS-01 / X3.FINAL — autorização do Product Owner (2026-10-22)

> **PO AUTHORIZED / RUNTIME INCONCLUSIVE** — Product Owner autorizou prosseguir com a preparação e execução da próxima task `X3.FINAL — Provider Activation & E2E Acceptance` e atualizar o GitHub. **Essa autorização de produto não constitui, por si só, parecer DPO nem prova de enquadramento/registro ROPA institucional.** Não afirmar `GATE-I3=PASS` sem evidência verificável da autoridade competente. Não há autorização de escrita Protheus nem de início X4.

## Baseline e situação

- X0 contract freeze: `7a043525b4`; X1 external-data-api: `0da1467b3b`; X2 consumer: `07b2f79095`; X2 contact minimization: `36ada077c7` (SHAs reportados, revalidar ancestrais no HEAD).
- X3 production source `74289c8495`; documentação X3 `b1d089a558`. Consultar [evidência de runtime](./X3-RUNTIME-EVIDENCE-20261022.md) e revalidar infraestrutura atual antes de operar.
- Redis `delpi-redis`, audiência Keycloak S2S `external-data-api`, serviços `external-data-api` e `supplies-api` e migrations Suprimentos V001/V002/V003 reportados implantados e saudáveis.
- Em produção `COMPANY_REGISTRY_PROVIDER=external-data-api` e `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable`; **nenhuma consulta produtiva BrasilAPI foi comprovada**.
- `GATE-I3 LGPD/ROPA=INCONCLUSIVE`; E2E usuário autorizado = `TEST_NOT_RUN`; runtime completo X3 = `INCONCLUSIVE`. Não inferir PASS de health/S2S isolados.

## Decisão e escopo da próxima task

O PO aprova preparar e, **quando gates aplicáveis passarem**, ativar o provider BrasilAPI e realizar smoke E2E autenticado controlado via SSH `operador@192.168.1.237`, sem autorização adicional de produto. A ativação produtiva requer:
1. **GATE-I3 / PRIVACY**: localizar e registrar evidência de autorização institucional aplicável (ROPA/base/finalidade/minimização/responsável/endosso DPO quando exigido). Se não comprovada, manter `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable` e parar ANTES do flip; registrar `INCONCLUSIVE`, sem simular ou inferir aprovação.
2. **GATE-IDENTITY**: identidade de usuário de teste e fornecedor/ambiente de teste explicitamente autorizados; nunca coletar tokens em logs/repo e não criar/usar identidades improvisadas.
3. **GATE-TECH**: conferir HEAD/status produtivo, backups, configuração Redis/Keycloak efetiva, saúde dos serviços, controles por actor distribuídos entre workers, paridade de origem e ausência de escrita ERP.
4. **GATE-ROLLBACK**: imagem/configuração anteriores, contenção por `EXTERNAL_DATA_CNPJ_PROVIDER=unavailable` e/ou `COMPANY_REGISTRY_PROVIDER=unavailable`, procedimento e smoke pós-rollback conhecidos.

Somente após gates PASS: realizar ajuste configuracional mínimo no `infra/.env` não versionado (com backup), reiniciar **apenas** `external-data-api` pela receita oficial, provar provider realmente habilitado, executar uma consulta CNPJ real em fixture/autorização permitida e smoke via `supplies-api`: SA2 canonical read → CNPJ external-data-api → S1 comparison → S2 review → decisões/idempotência → prepare-update draft-only. Checar 401/403, falha do provider, 429 e quotas, sem gerar carga real excessiva. Nunca emitir PUT/POST ERP. Documentar SHAs, image digests, estados efetivos e evidência saneada. Se falhar pós-flip, desligar provider e verificar contenção. **X4 UX segue NÃO AUTORIZADA nesta task.**

## Critérios de aceite

- `GATE-I3=PASS` com evidência institucional identificável, não substituída por esta aprovação PO.
- `GATE-IDENTITY=PASS` com usuário/fornecedor de teste autorizados e AuthZ Core fail-closed.
- `GATE-TECH=PASS` com Redis, multiworker, Keycloak S2S e status de migrations verificados.
- `GATE-PROVIDER=PASS` consulta real controlada por `external-data-api` com `THIRD_PARTY_API`, QSA/CPF/contatos omitidos.
- `GATE-E2E=PASS` revisão/decisões/prepare-update comprovados sem escrita ERP.
- `GATE-ROLLBACK=PASS` contenção conhecida e verificável; sem rollback destrutivo de DB.
- Relatório `BASE HEAD, FINAL HEAD, PRODUCTION HEAD, CONFIG, GATES, SMOKES, TESTS, ROLLBACK, SHAs, DIGESTS, RESIDUAL, OUTCOME`, sem secrets. Classificação `PASS/FAIL/INCONCLUSIVE/TEST_NOT_RUN`, conclusão GPT somente após revisão.

## Autoridades e cuidados

Seguir instruções oficiais GPT Arquiteto, regras `.cursor`, freeze X0 e contratos X1/X2, além de evidência X3. Não alterar Core/RBAC, api-delpi, S1/S2 ou MFE, nem criar permissões por endpoint. Não assumir que aprovação do Product Owner corresponde a autorização institucional DPO/ROPA. Se faltar aprovação ou identidade de teste, registrar bloqueio com próxima ação objetiva.
