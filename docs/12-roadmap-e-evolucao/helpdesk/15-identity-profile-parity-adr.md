# ADR — HELPDESK-IDENTITY-002: sincronização contínua de perfil (firstname/realname)

Status: **002A — design aprovado, implementação feature-flagged (flag OFF)**
Data: 2026-09-28 (rev. 002A)
Contexto: HELPDESK-IDENTITY-001B aceito e deployado (`69c5b151a8`)

## Contexto e evidência

- **Owner canônico da identidade: Keycloak.** Os claims validados do JWT
  (`given_name`/`family_name`) são a **projeção autenticada da sessão**
  consumida pelo Helpdesk — não uma autoridade de identidade nova. Core,
  Helpdesk, MFE e GLPI não são donos de identidade.
- `JIT_CREATE_PARITY` resolvida: mappers SAML `saml-user-property-mapper` no
  client `https://helpdesk.centraldelpi.com.br/` emitem
  `…/claims/givenname`, `…/claims/surname`, `…/claims/emailaddress`; JIT
  cria usuários novos com nomes corretos (provado em runtime: GLPI user 80).
- O samlsso JIT **só roda na criação** — usuários existentes nunca são
  atualizados pelo SSO (`User::getOrCreateUser`).
- O token OAuth por-usuário (perfil "Colaborador - Chamados", `user`=READ)
  **não pode** escrever `Administration/User` (403 provado).
- Não existe endpoint HLAPI self-scoped para names: `/User/Me/Preference`
  só cobre preferências de display.

Requisito de produto: **"sempre que o usuário logar, verificar e manter
atualizado"** — drift existente precisa de autoridade de write legítima.

## Inventário de autoridade do provider (provado)

- `PATCH /Administration/User/{id}` exige right `user` **UPDATE** (bit 2)
  + `User::canUpdateItem()` — autorização **entity-scoped** via
  `glpi_profiles_users(entities_id, is_recursive)`.
- Entidades: 0=Delpi(root), 1=Matriz SC, 2=Filial ES. A população de
  colaboradores tem profile rows em {1,2} — um principal com escopo
  `{1,2}` não-recursivo cobre colaboradores e **não** alcança usuários cujo
  único profile está na entidade 0 (admins/técnicos): `canUpdateItem`
  falha → provider 403 → `failed_forbidden` (fail-closed).
- GLPI OAuth client expõe apenas grant `authorization_code` — **sem M2M**
  via HLAPI. `LEGACY_PROVIDER_DEPENDENCY`: apirest `user_token` +
  App-Token é o mecanismo técnico provado (padrão H12) e é aceito para
  esta implementação delimitada; uma futura capability M2M suportada pode
  substituir o adapter sem mudar o porto de aplicação.
- **RESIDUAL_PROVIDER_PRIVILEGE:** GLPI não oferece restrição por campo —
  `user` UPDATE escreve o objeto User inteiro dentro do escopo de
  entidade. A restrição a `firstname`/`realname` é aplicada na **porta de
  aplicação**, não no provider. Mitigações: principal dedicado, apiclient
  dedicado, restrição de entidade, credencial backend-only, porto estreito,
  nenhuma rota genérica, auditoria, kill switch e pós-condição autoritativa.

## Decisão aprovada (002A)

### Principal técnico dedicado

- Usuário GLPI dedicado `minha-delpi-profile-sync` (local, não humano) +
  perfil GLPI dedicado `Profile Sync` com `user` READ+UPDATE e **nenhum
  right não relacionado**. Escopo inicial: entidades **1 e 2**,
  não-recursivo. **Não criado ainda** — nenhuma permissão foi alterada.
- Apiclient **dedicado** (`minha-delpi-profile-sync`) — não reutiliza o
  legacy `minha-delpi-helpdesk-legacy`. Restrição `ipv4_range` desejada mas
  só após provar o egress real visto pelo GLPI nas chamadas do
  helpdesk-api — não chutar endereços Docker/NAT.
- Credencial: `user_token` do principal + `app_token` do apiclient, via
  padrão existente `infra/.env` → compose → env do container.
- **Email NÃO é gravável.** Campos permitidos: `firstname` ←
  Keycloak `given_name`; `realname` ← Keycloak `family_name`. Nada mais.

### Autoridade e binding

```text
TRIGGER AUTHORITY:      sessão autenticada do usuário (require_actor)
CANONICAL OWNER:        Keycloak (projeção da sessão = claims validados)
WRITE EXECUTOR:         principal técnico dedicado (backend-only)
TARGET AUTHORITY:       user_id GLPI resolvido internamente da sessão
PROVIDER FINAL:         GLPI (rights + canUpdateItem)
FRONTEND:               nenhuma autoridade
```

- O `user_id` alvo vem exclusivamente de `OAuth session → session_user_id`
  — nunca de body/query/rota (anti confused-deputy).
- **Nenhuma rota pública nova** — sync é fluxo interno do bootstrap
  autenticado.
- Write body: apenas `firstname`/`realname` **divergentes** — qualquer
  outro campo é erro de construção.
- Pós-condição: `synced` só após releitura autoritativa
  (`GET /Administration/User/{id}` via token do próprio usuário — o writer
  técnico não vira autoridade de leitura).

### Porto de aplicação (Abstraction Gate)

```python
class ProfileSyncWriterPort(Protocol):
    def update_profile_names(
        self, user_id: int, *,
        firstname: str | None = None, realname: str | None = None,
    ) -> None: ...
```

Não existe `update_user`/`GLPIAdminClient`/rota genérica. A flag
`GLPI_PROFILE_SYNC_ENABLED` (default `false`) é **kill switch operacional**
— não é AuthZ nem permissão do provider. Sem writer: drift →
`deferred_write_authority` (semântica 001B preservada, zero write).

### Cadência — uma verificação por sessão de login

- Chave semântica: `hash(subject | sid)` — o `sid`/`session_state` do JWT
  Keycloak identifica a sessão de login. **Sem hash de access token**:
  tokens rotacionam dentro da sessão e não podem dividir uma sessão em
  várias reconciliações. O `sid` é propagado pelo `delpi_auth` →
  `Actor.session_id`.
- Mudança de perfil canônico dentro da mesma sessão: fingerprint
  irreversível `sha256(first|last)` divergente → reconciliação nova.
- **Topologia (provada):** memo process-local; 1 container, 1 worker
  uvicorn. Semântica honesta: reconciliação **bounded/idempotente por
  instância/sessão** — não "exactly-once" global (não há Redis nem é
  necessário: write é idempotente e convergente).
- TTL: outcomes terminais ≤12h (> ssoSessionMaxLifespan 10h), falhas 60s.

### Entity-0 — fora do escopo inicial

Usuários cujo único profile GLPI vive na entidade 0 (admins/técnicos)
permanecem **OUT_OF_INITIAL_SYNC_SCOPE** — fail/defer closed, sem
escalonamento de privilégio.

> **HELPDESK-IDENTITY-002A.1 — PRIVILEGED/ENTITY-0 PROFILE PARITY**
> (requisito descoberto): estratégia segura para paridade de
> admins/técnicos precisa de decisão própria.
> `CONTINUOUS_PARITY_ENTITIES_1_2` ≠ `GLOBAL_CONTINUOUS_PARITY`.

### Falhas e auditoria

- Sync failure nunca invalida autenticação; `profile_sync` reporta
  `noop | synced | deferred_write_authority | failed_forbidden |
  failed_unavailable | failed_verification | failed_write | skipped_*`.
- Auditoria estruturada por write: `actor=system/profile-sync`, subject,
  `user_id`, `fields_changed`, outcome, correlation — **nunca** valores de
  nome, tokens ou credenciais. `glpi_logs` do provider é evidência
  secundária, não a auditoria primária.

### Homolog/produção

Homolog compartilha o mesmo GLPI — token separado **não** dá isolamento de
dados. Antes da aceitação live com write privilegiado: alvo canário
dedicado (identidade de teste em entidade 1/2, drift controlado, uma
reconciliação, reread, audit, segundo acesso sem write). Sem bulk write.

## Opções descartadas

- **B — sync provider-side via SAML:** samlsso só roda JIT na criação;
  exigiria patch em código de fornecedor (upgrade/ownership risk).
- **C — batch repair como solução única:** não atende requisito contínuo;
  vira o subwave 002B (dry-run → aprovação → batch limitado → verify).

## 002B — reparo do legado (PENDENTE, não implementado)

Lookup canônico por subject: **Keycloak é o dono** — não escolher Core só
porque existe endpoint. Core S2S directory pode ser usada como **projeção
de leitura** somente se o inventário provar que expõe atributos
Keycloak-owned com semântica/frescor adequados; caso contrário, credencial
de leitura legítima do Keycloak. Decisão PENDENTE.

## Pendências de decisão (owner)

1. Criar `minha-delpi-profile-sync` + perfil `Profile Sync`
   (user READ+UPDATE only), escopo entidades 1+2 não-recursivo.
2. Apiclient dedicado + inventário de egress real para `ipv4_range`.
3. Aprovar ativação de `GLPI_PROFILE_SYNC_ENABLED` após credencial.
4. 002A.1: estratégia para usuários de entidade 0.
5. 002B: fonte de lookup canônico em batch.

## Residuais registrados

- **KEYCLOAK-CONFIG-RECOVERY-001:** mappers SAML vivem em runtime
  (`delpi-keycloak-db`); recuperação determinística pendente — sem novo
  framework nesta tarefa.
- **LEGACY_PROVIDER_DEPENDENCY** (seção acima).
- Cache de sessão OAuth `helpdesk.oauth_sessions` é lookup, não authority.

## Fora de escopo

- Não expandir a credencial H12 (doc-upload).
- Não conceder `user` UPDATE a perfis de colaborador.
- Nenhum write privilegiado executado nesta subetapa.
- Nenhum bulk repair nesta subetapa.
