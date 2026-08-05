# 05 — Matriz de permissões

## 1. Autenticação

- Continua **Keycloak** via Portal; MFE recebe `getAccessToken`.
- JWT: identidade (sub, email, roles Keycloak) — **sem** lista completa de permissões Delpi.
- Permissões efetivas: Core API (`/core-api/me`, apps/routes) + checagem no endpoint (`@require_any_permission`).

## 2. Duas dimensões

| Dimensão | Onde | Exemplo |
|----------|------|---------|
| **Funcional (RBAC)** | Core API + constantes `api_delpi_permissions.py` + manifesto | `planejamento-orcamentario.capex.write` |
| **Escopo de dados** | Tabela `UserOrgScope` no schema do plugin | usuário só CC `205` unidade `01` |

**Regra de ouro:** frontend esconde botões; API **revalida** permissão **e** escopo em todo GET/PATCH. Alterar `cost_center` na URL/body não amplia acesso.

## 3. Códigos RBAC preliminares

Prefixo: `planejamento-orcamentario.`

| Código | Finalidade |
|--------|------------|
| `.access` | Enxergar o app |
| `.orientations.read` / `.orientations.manage` | Ler / publicar Carta e docs |
| `.revenue.read` / `.revenue.write` | Receita |
| `.headcount.read` / `.headcount.write` | Pessoal |
| `.capex.read` / `.capex.write` | CAPEX |
| `.approve` | Aprovar/devolver no próprio escopo |
| `.approve.all` | Aprovar qualquer escopo (Diretoria) — auditável |
| `.consolidate` | Visões consolidadas |
| `.export` | Gerar/baixar exportações |
| `.admin` | Config, escopos, reopen, lock exercício |
| `.view.filial-01` / `.view.filial-02` | Espelho do padrão filial (se unidade = filial) |

Listas compostas no estilo PAC/LNF (`*_READ_PERMISSIONS`) para decorators.

## 4. Matriz perfil × capacidade

| Capacidade | Colaborador CC | Gestor área | Aprovador | Consolidação | Diretoria | Admin |
|------------|----------------|-------------|-----------|--------------|-----------|-------|
| access | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| confirmar leitura | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| editar receita (escopo) | ✓* | ✓ | | | ✓** | ✓ |
| editar pessoal | ✓* | ✓ | | | ✓** | ✓ |
| editar CAPEX | ✓* | ✓ | | | ✓** | ✓ |
| submeter | ✓ | ✓ | | | | ✓ |
| aprovar / devolver | | | ✓ escopo | | `.approve.all` | ✓ |
| consolidar | | | | ✓ | ✓ | ✓ |
| exportar | escopo | escopo | escopo | amplo | amplo | amplo |
| admin / escopos | | | | | | ✓ |

\* se `role_in_scope` editor e RBAC write.  
\*\* somente com flag auditável de bypass de escopo (Diretoria) — nunca silencioso.

## 5. Vínculo usuário ↔ centro de custo

**Proposta MVP:** CRUD admin em `UserOrgScope` (usuário, unidade, lista de CCs, papel).  
**Não** confiar em atributo Keycloak não governado pelo Core sem processo.

Evolução: sync a partir de cadastro RH/TOTVS **quando** fonte for confirmada.

## 6. Testes de segurança obrigatórios (fase implementação)

- 403 ao ler/editar CC fora do escopo
- 403 write sem permissão mesmo com escopo
- 403 approve sem `.approve`
- Bypass Diretoria gera `AuditEvent` específico
