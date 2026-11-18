# GLPI #887 — Portal RH → Core API: equipe por Gestor Direto

**Status:** integração em PR, sem deploy; Delpi Reports semanal é etapa posterior.

## Autoridade de dados

- Portal RH (`Delpi-ti/portal-epi`, PR #12 já mergeada) é a fonte oficial:
  `CollaboratorProfile.manager` → `epi_collaborator`.
- Core API **não** replica a árvore hierárquica; faz uma consulta S2S fresca por solicitação.
- Core API guarda **apenas** uma associação explicitamente verificada:
  `user_hr_registrations(user_id UUID, registration VARCHAR(30) UNIQUE, verified_at, verified_by_user_id)`.
- Matrícula é **texto exato** e globalmente único no RH. Preservar zeros à esquerda:
  `"001" != "1"`. Nunca usar nome, e-mail presumido, `SYS_USR.USR_ID`
  ou `epi_collaborator.id` para mapear um usuário Core.
- Ausência de associação => `coreUserId: null` e `identityStatus: "unmapped"`.
  Não inferir identidade nem converter ausência de rastreio em inatividade.

## Contrato upstream (Portal RH)

```http
GET {PORTAL_RH_API_URL}/api/v1/integrations/managers/00001/team/?include_indirect=true&include_inactive=false&page=1&page_size=500
X-Delpi-Service-Token: <PORTAL_RH_API_SERVICE_TOKEN>
```

O token acima tem o **mesmo valor** da variável
`PORTAL_RH_INTEGRATION_SERVICE_TOKEN` no Portal RH, mas o nome usado
pelos clientes do monorepo é `PORTAL_RH_API_SERVICE_TOKEN`.

O gateway pagina até 20 páginas (máximo 10.000 membros) e falha fechado
em identidade divergente, duplicidade, contrato inesperado, indisponibilidade
ou erro de autenticação do RH. Sem cache de hierarquia.

## Contrato Core API para serviço autorizado

```http
GET /integrations/organization/managers/00001/team?include_indirect=true&include_inactive=false
X-Delpi-Service-Token: <CORE_ORGANIZATION_READ_SERVICE_TOKEN>
```

- Apenas **backend ↔ backend**. Nunca enviar o segredo ao navegador.
- **Novo segredo exclusivo** de leitura da hierarquia;
  `CORE_API_INTEGRATIONS_SERVICE_TOKEN` e o segredo do Portal RH não servem.
- Exclusivamente header `X-Delpi-Service-Token`, sem Bearer;
  exigência de token em comparação de tempo constante.
- `include_indirect` default `false`; `include_inactive` default `false`.
- Usuários Core **inativos** não retornam UUID, mesmo que exista mapping.
- GET somente; sem escrita de RH ou atualização de hierarquia.

Exemplo sintético:

```json
{
  "source": "portal-rh",
  "manager": {
    "registration": "00001",
    "fullName": "GESTOR EXEMPLO",
    "branchCode": "02",
    "active": true,
    "coreUserId": "11111111-1111-4111-8111-111111111111",
    "identityStatus": "mapped"
  },
  "members": [
    {
      "registration": "00002",
      "fullName": "COLABORADOR EXEMPLO",
      "branchCode": "02",
      "active": true,
      "coreUserId": null,
      "identityStatus": "unmapped",
      "relationship": "direct",
      "managerRegistration": "00001"
    }
  ],
  "count": 1,
  "unmappedCount": 1,
  "includeIndirect": true,
  "includeInactive": false
}
```

Respostas esperadas: 200, 400 (parâmetros), 401 (sem Core token),
403 (Core token inválido), 404 (gestor RH ausente), 502 (contrato RH),
503 (RH indisponível / credencial RH inválida) e 500 (erro interno).

> A leitura de equipe é um contrato técnico para serviços autorizados,
> **não** concede visibilidade a qualquer supervisor no Portal ou Reports.
> A autorização por gestor/destinatário e tratamento LGPD dos dados de uso
> permanecem escopo da próxima etapa.

## Associação manual e controlada matrícula → usuário Core

Somente usuário autenticado com `rbac.manage` **e** `users.manage`:

```http
GET /admin/organization/users/{core_user_uuid}/hr-registration
PUT /admin/organization/users/{core_user_uuid}/hr-registration
DELETE /admin/organization/users/{core_user_uuid}/hr-registration
```

Body PUT:

```json
{"registration": "00001", "confirmIdentity": true}
```

A API confirma que a matrícula **existe e está ativa** no RH e que o
usuário Core está ativo. A opção `confirmIdentity` registra uma
**conferência humana** do vínculo; existência da matrícula não prova
sozinha que ela pertence ao usuário Core. Conferir com cadastro RH
oficial antes do PUT. Sem conferência, não cadastrar.

A associação é única (uma matrícula por usuário, um usuário por
matrícula), reversível (DELETE) e tem trilha de auditoria. Não há
migração automática por nome ou e-mail.

## Configuração / operação

No `infra/.env` do ambiente Minha Delpi, configurar:

```dotenv
# URL base RH acessível a partir do container Core
PORTAL_RH_API_URL=https://rh.exemplo.interno
# Igual ao PORTAL_RH_INTEGRATION_SERVICE_TOKEN no host do Portal RH
PORTAL_RH_API_SERVICE_TOKEN=<segredo-rh>
PORTAL_RH_API_TIMEOUT=5
# Novo segredo dedicado, distinto dos demais
CORE_ORGANIZATION_READ_SERVICE_TOKEN=<segredo-core-organizacao>
```

Secrets reais ficam apenas no ambiente, nunca no repositório.
`infra/docker-compose.yml` repassa esses valores ao container Core;
em `docker-compose.hml.yml`, Portal RH permanece explicitamente
**desabilitado**, para impedir conexão acidental com produção.

**Antes do deploy, após merge/autorização:** fazer backup e conferir a
migração Core antes de iniciar o container. O `core-api/docker-entrypoint.sh`
já executa `flask db upgrade` automaticamente na inicialização; portanto,
o deploy da nova imagem **poderá aplicar a migration de produção**.
Não disparar um segundo upgrade manual sem necessidade. Validar acesso
de rede/firewall, secrets, testes e plano de rollback.

Smoke pós-deploy (usar matrícula de teste autorizada):

```bash
curl -sS -H 'X-Delpi-Service-Token: <segredo-core-organizacao>' \
  'https://<host-minha-delpi>/core-api/integrations/organization/managers/00001/team?include_indirect=true'
```

Verificar permissões negativas: sem token => 401; token genérico => 403;
gestor não cadastrado no RH => 404; usuário Core não mapeado => null.

Testes unitários de integração (sem tocar RH/produção):
`pytest app/tests/test_portal_rh_organization.py -q`.

## Limites desta etapa

- Sem relatório semanal, provider Delpi Reports ou e-mail.
- Sem consulta/redistribuição de `app_usage_events` ou consentimentos.
- Sem UI ou autorização para supervisores.
- Sem cache ou replicação permanente dos vínculos de gestão.
- Sem criação automática de vínculos de identidade pela heurística de nomes.
- Avaliação LGPD da finalidade de monitoramento individual deve ocorrer
  antes de disponibilizar relatórios nominais aos supervisores.
