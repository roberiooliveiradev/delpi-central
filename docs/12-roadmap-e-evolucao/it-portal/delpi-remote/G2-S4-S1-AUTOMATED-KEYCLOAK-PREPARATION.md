# G2-S4-S1 | Preparacao automatizada de identidades de computadores

**Data:** 14/11/2026. **Estado:** EM REVISAO / desabilitado por padrao.
**Objetivo:** retirar o cadastro repetitivo de Clients do Keycloak do fluxo cotidiano de TI, sem criar uma credencial compartilhada entre todos os computadores.

## O que foi implementado

1. Nova tabela aditiva **V012** `it_portal.workstation_agent_identities` e trilha `workstation_agent_identity_events`. Um `workstation_id` corresponde a exatamente um `client_id` deterministico `itp-ws-<UUIDsemhifens>` e um UUID de Client no Keycloak. Nao guarda nenhum segredo, token, sessao ou endereco IP.
2. API `GET /workstations/{id}/agent-identity`, autorizacao humana `it-portal.computers.view`, retorna estado e flags de segurança, sem credenciais. `POST /workstations/{id}/agent-identity/prepare`, com `confirmed:true`, exige `it-portal.computers.view` + `it-portal.computers.manage` **revalidados no Core**, e feature flag separada.
3. Servico transacional reserva o nome e impede concorrencia antes de tocar no Keycloak. Somente workstation ativa `in_operation` e nao arquivada. Repetir pedido de identidade ja preparada retorna estado anterior (idempotencia); uma tentativa interrompida exige reconciliacao manual, NUNCA segundo Client automatico.
4. Gateway Keycloak Admin REST: usa **credencial administrativa exclusiva** do backend, URL **HTTPS** verificada, sem redirecionamentos; `POST /admin/realms/<realm>/clients` com `enabled=false`, `serviceAccountsEnabled=true`, `fullScopeAllowed=false`, browser/redirect/login interativo desativados; remove scopes default/optional adicionados pelo realm, relê a configuracao e exige estado **desabilitado** antes de marcar como preparado. Se falhar, mantem registro `failed` e bloqueia retries automaticos.
5. UI ficha do computador: secao **Identidade do agente**, estado, Client ID, ausencia de credencial e coleta desabilitada. Somente operadores com permissao de gestao veem **Preparar identidade** quando o backend liberar a flag. Exige confirmacao, sem jamais enviar segredos ao navegador.
6. Pytest unit/HTTP com testes de revogacao de permissoes do Core, flag off, concorrencia logica, falha do Keycloak e mock do Admin REST, teste real Postgres V001..V012, Vitest do frontend e tests de contratos de API.

## Limites muito importantes

**ESTA FASE SO PREPARA UM CLIENT DESABILITADO.** Nao cria credencial para Windows, nao informa client secret, nao habilita scopes, nao ativa S2S, nao configura o arquivo de binding de G2-S2 nem instala agente. Mesmo com a flag de G2-S4 ligada em homologacao, os Clients permanecem **incapazes de obter tokens enquanto disabled**.

A melhoria seguinte sera o **G2-S4-S2, ativacao individual e enrolment seguro**:
- Vinculo ativo no PostgreSQL em vez de editar manualmente `IT_PORTAL_WORKSTATION_COLLECTOR_BINDINGS`, com fallback **negado** quando o modo dinamico estiver ligado.
- Autorizacao S2S via JWT assinado/issuer/audiencia/expiracao + scope `it-portal.workstations.ingest` e allowlist **derivada do UUID e do banco**, nao de claims nao verificadas.
- Provisionamento/rotacao e entrega de credencial por bootstrap local de uso unico no Windows, com expiracao curta, identidade do host, DPAPI e revogacao no Keycloak, jamais client secret no navegador nem script publico.
- Revogacao individual em arquivamento, perda, roubo, reinstalacao; processar falhas de compensacao e reconcile.
- Permissao granular dedicada de enrolment em Core/manifest, alem da gestao de computadores, antes de habilitar em escala.

## Configuracao (tudo OFF por padrao)

No Compose e no `infra/.env.prod.example`:
```dotenv
IT_PORTAL_WORKSTATION_PROVISIONING_ENABLED=false
IT_PORTAL_WS_KC_ADMIN_URL=
IT_PORTAL_WS_KC_REALM=
IT_PORTAL_WS_KC_PROVISIONER_CLIENT_ID=
IT_PORTAL_WS_KC_PROVISIONER_CLIENT_SECRET=
```

**Nao preencher nem habilitar estas variaveis em producao nesta etapa.** A senha do provisionador nao deve ser a conta `admin-cli`, `delpi-core-admin` ou qualquer usuario pessoal. Usar conta tecnica separada, com privilegios administrativos mínimos para Clients dentro do realm correto, auditada e protegida em cofre/ambiente privado. Requer caminho HTTPS do backend ao Keycloak: o endpoint HTTP interno comum em algumas instalacoes **nao atende ao contrato**, nao afrouxar TLS para contornar.

As variaveis `IT_PORTAL_WORKSTATION_INGEST_ENABLED=false` e `IT_PORTAL_WORKSTATION_COLLECTOR_BINDINGS` devem permanecer como estao. **Nao migrar bindings de servidores**, escopos `host-services.control-agent` nem roles administrativas.

## Checklist antes de qualquer futuro deploy

- Confirmar commit e CI verde: API/HTTP, Keycloak mock, V012 em PostgreSQL descartavel, frontend lint/Vitest/build.
- Gerar `pg_dump -Fc -n it_portal`, validar catalogo com `pg_restore -l`; preparar rollback das imagens, **nao remover V012**.
- Verificar `IT_PORTAL_WORKSTATION_PROVISIONING_ENABLED=false`, `IT_PORTAL_WORKSTATION_INGEST_ENABLED=false` e ausencia de credenciais administrativas do novo provisionador.
- A API deve subir antes do frontend para que `GET /workstations/{id}/agent-identity` encontre V012.
- Confirmar schema `it_portal.workstation_agent_identities` + eventos e `SELECT version FROM it_portal.schema_migrations WHERE version=12`; GET responde `not_prepared`, `can_prepare:false`; POST deve responder 409 sem qualquer chamada de rede ao Keycloak.
- Somente em HML separado, com Keycloak dedicado de testes, auditar permissao fresh (revogada deve dar 403), criar um unico Client **desabilitado**, verificar scopes vazios e inexistencia de secret no HTTP/frontend, repetir teste sem duplicar.
- Registrar aceites em sistema privado antes de habilitar qualquer preparo produtivo; nao autorizar provisionamento em massa ou envios S2S nesta etapa.

## Rollback seguro

1. Deixar a flag `IT_PORTAL_WORKSTATION_PROVISIONING_ENABLED=false` e nao provisionar novos dispositivos.
2. Em falha apos POST Keycloak, a API marca o registro `failed`; **nao** criar novamente, revisar manualmente se o Client desabilitado ficou orfao. Desabilitar/revogar no Keycloak em caso de duvida.
3. Reverter imagem API/frontend para release anterior sem `git reset --hard`. Manter V012 aditiva historica, sem deletar banco ou registros; caso precise de reparo usar migration nova.
4. Nenhum acesso remoto foi criado; G0-SEC e G3 permanecem bloqueados. Piloto G2-S1..S3 continua aguardando Windows real presencial.

Fontes: [API Admin oficial Keycloak](https://www.keycloak.org/docs-api/latest/rest-api/), [roadmap](README.md), [issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179).
