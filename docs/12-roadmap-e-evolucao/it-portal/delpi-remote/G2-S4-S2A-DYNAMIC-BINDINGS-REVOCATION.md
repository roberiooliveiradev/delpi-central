# G2-S4-S2a | Binding dinamico por computador e revogacao controlada

**Data:** 14/11/2026. **Estado:** EM REVISAO (codigo e testes); **sem deploy e sem homologacao Keycloak/Windows**.
**Escopo:** autorizar snapshots por um vinculo transacional no PostgreSQL, sem editar um `client_id=uuid` no `.env` para cada computador; revogar identidades de forma segura.
**Limite:** esta etapa NAO faz bootstrap, emissao de credencial, ativacao de Client no Keycloak ou liberacao de ingestao no ambiente real. O proximo item G2-S4-S2b e responsavel por isso.

## Entrega

1. Migration aditiva `V013__workstation_dynamic_binding_revocation.sql`: colunas `ingest_authorized BOOLEAN DEFAULT FALSE`, `revocation_status`, `revoked_at`, `revoked_by_id` em `it_portal.workstation_agent_identities`. Eventos `identity_revocation_requested`, `identity_revocation_failed`, `identity_revoked`. **Nenhuma identidade V012 e automaticamente autorizada**.
2. `IT_PORTAL_WORKSTATION_DB_BINDINGS_ENABLED=false`: quando **OFF**, continua valendo o modo legado `IT_PORTAL_WORKSTATION_COLLECTOR_BINDINGS`, sem alteracao nos servidores. Quando **ON**, o vinculo legado e ignorado, **sem fallback**, mesmo se o mesmo Client estiver no `.env`.
3. Na ingestao dinâmica, a rota deriva o Client ID esperado do UUID da maquina (`itp-ws-<32hex>`) e valida o JWT por assinatura, issuer, audiencia, expiracao e scope `it-portal.workstations.ingest` com a biblioteca compartilhada. A lista global `S2S_ALLOWED_CLIENTS` de **servidores** nao vira uma lista manual de todos os desktops. O verificador S2S ainda exige `S2S_AUDIENCE`; a autorizacao final ocorre por consulta ao banco na mesma transacao da gravacao do inventario, travada com `FOR SHARE`.
4. A gravacao e negada se o registro estiver ausente, `prepared` sem `ingest_authorized=true`, revogado, em erro, arquivado ou client errado. Sem modificacao em campos curados do computador. O modo DB nao tem caminho para definir `ingest_authorized=true` nesta etapa; apenas testes de Postgres descartavel simulam uma ativacao futura.
5. `IT_PORTAL_WORKSTATION_REVOKE_ENABLED=false` por default. Somente com DB mode e revogacao liberados, operador com `it-portal.computers.view + it-portal.computers.manage` **fresh no Core** pode confirmar `POST /workstations/{uuid}/agent-identity/revoke`.
6. Revogacao: (a) transacao muda `ingest_authorized=false` e `revocation_status=pending` + evento de auditoria; (b) backend Keycloak Admin HTTPS confere `clientId`, UUID e `delpi.owner`, desabilita exatamente aquele Client e faz read-back; (c) transacao confirma `state=revoked` e evento. Se a rede/Keycloak falhar, grant segue negado e status `failed` exige conciliacao manual. Sem retry silencioso nem falso sucesso. Revogacao repetida de Client ja confirmado e idempotente.
7. Painel `Identidade do agente` mostra estado de revogacao e botao `Revogar identidade` apenas se a API autorizar; requer confirmacao explicita. Nenhum secret/token transita pelo browser.

## Seguranca e limites

- **Ingestao `IT_PORTAL_WORKSTATION_INGEST_ENABLED=false` permanece obrigatoria e OFF por padrao**, independentemente de modo DB.
- Modo DB deliberadamente nao consulta `WORKSTATION_COLLECTOR_BINDINGS`. Nao ativar DB mode se houver agentes de producao dependentes de binding legado sem plano de migracao.
- O Keycloak client de G2-S4-S1 continua DESABILITADO e sem scopes. A etapa nao emite chave/secret, nao instala agente, nao permite login no Portal, nao libera shell, controle remoto ou servico Windows.
- A revogacao Keycloak e DB so protege ingestao em **modo DB**. Quando modo ENV estiver ativo, a rota de revogacao retorna 409, evitando sugerir que o env antigo foi revogado.
- O JWT S2S do equipamento deve ter assinatura, issuer confiavel, audiencia exclusiva, prazo, scope de inventario e client ID exato. Sem essas verificacoes, a rota nega; nao ha bypass por token humano ou por hostname/IP.
- Antes de qualquer uso real, testar HML com Keycloak e um computador corporativo de teste; confirmar comportamento de token emitido anteriormente, atualizacao de estado em falha de rede e exclusao de grant em janela concorrente.
- **Segredo de provisionamento administrativo** permanece exclusivo de backend, nunca no banco nem nas respostas HTTP; sem alteracao nas credenciais dos servidores.
- Cliente em `failed/pending` exige conciliacao e revisao de Keycloak por TI, sem script automatico de reset.

## Configuracao e deploy FUTURO

As duas novas variaveis estao no Compose e `infra/.env.prod.example`, **sempre false**:

```dotenv
IT_PORTAL_WORKSTATION_INGEST_ENABLED=false
IT_PORTAL_WORKSTATION_DB_BINDINGS_ENABLED=false
IT_PORTAL_WORKSTATION_REVOKE_ENABLED=false
```

**Nao fazer deploy de V013 em producao nesta atividade**: o usuario escolheu continuar desenvolvendo sem homologar. Quando houver janela aprovada, fazer `pg_dump -Fc -n it_portal` do banco correto e verificar o backup com `pg_restore -l`, atualizar API primeiro, confirmar V012/V013 e flags OFF, depois frontend. Nunca remover migracoes antigas, nem ativar variaveis por engano.

## Testes de entrega

- `python -m pytest -q tests/test_workstation_snapshot_ingest.py tests/test_workstation_dynamic_s2s_auth.py tests/test_workstation_identity_provisioning.py tests/test_http_contract.py`
- CI com Postgres 16 descartavel: migracoes `V001..V013`, grant default FALSE, positiva simulada somente em teste, revogacao antes de novo snapshot e auditoria.
- `npm test -- --run src/features/workstations/WorkstationAgentIdentityPanel.test.tsx`, lint e build.
- Regressao de S2S para servidores obrigatoria. Modo ENV legada deve continuar intocado.

## Proxima etapa G2-S4-S2b

Implementar **bootstrap de uso unico para Windows piloto**, com validade curta, prova de posse do equipamento e aprovacao do operador, sem entregar client secret pelo browser. O servidor precisara verificar a identidade local de maneira forte antes de ativar o Client e emitir credencial protegida com DPAPI (ou certificado TPM/mTLS), criar `ingest_authorized=true` somente apos confirmacao de Keycloak e homologacao, e prever expiracao/rotacao/recuperacao. O desenho final depende de teste real Keycloak e Windows para evitar confiar apenas em hostname/IP.

**Status ao finalizar S2a:** integracao e revogacao preparadas, **ativacao ainda sem implementacao**. G0-SEC segue bloqueando acesso remoto independente deste inventario.
