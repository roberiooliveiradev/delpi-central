# ADR — HELPDESK-IDENTITY-002: sincronização contínua de perfil (firstname/realname)

Status: **PENDING — decisão de owner necessária**
Data: 2026-09-28
Contexto: HELPDESK-IDENTITY-001B

## Contexto e evidência

- Fonte canônica de identidade: **Keycloak** (`given_name`/`family_name` → claims `givenname`/`surname`).
- `JIT_CREATE_PARITY` resolvida: mappers SAML `saml-user-property-mapper` no client `https://helpdesk.centraldelpi.com.br/` emitem `…/claims/givenname`, `…/claims/surname`, `…/claims/emailaddress`; JIT cria usuários novos com nomes corretos (provado em runtime: GLPI user 80).
- O samlsso JIT **só roda na criação** — usuários existentes nunca são atualizados pelo SSO (`User::getOrCreateUser` retorna usuário encontrado sem sync).
- O token OAuth por-usuário (perfil "Colaborador - Chamados", `user`=READ) **não pode** escrever `Administration/User` (403 provado). O reconcile virou detecção de drift (`deferred_write_authority`, zero PATCH).
- Não existe endpoint HLAPI self-scoped para names: `/User/Me/Preference` só cobre preferências de display.

Requisito de produto remanescente: **"sempre manter atualizado"** — drift existente precisa de uma autoridade de write legítima.

## Opções avaliadas

### A — Principal técnico dedicado de profile-sync (recomendada)

Backend-only. Credencial técnica nova e separada (NÃO a H12 — escopo doc-upload), com direito `user` UPDATE no GLPI, usada exclusivamente pelo reconcile para gravar `firstname`/`realname` do `user_id` já resolvido pela sessão OAuth da pessoa (mapping inalterado).

- Pro: atende paridade contínua; write bounded pelo código da aplicação (só 2 campos, só o próprio usuário da sessão); auditoria existente já estruturada; idempotência e postcondition já implementados (basta reativar o caminho de write quando autorizado).
- **Privilégio residual obrigatório documentado:** GLPI não permite grant "UPDATE somente firstname/realname" — o direito `user` UPDATE do principal técnico é tecnicamente mais amplo que a operação exposta (a aplicação restringe; o provider não). Mitigações: credencial backend-only em env/secret, perfil técnico com o mínimo de rights além de `user` UPDATE, uso exclusivo via `ProfileSyncService`, logs de auditoria por write.
- Exige: aprovação explícita do owner de segurança.

### B — Sync provider-side via SAML no login

Fazer o samlsso atualizar atributos de usuários existentes a cada SSO login.

- O plugin (v1.2.5) não tem opção suportada: `getOrCreateUser` só chama `performJIT` quando o usuário não existe. Caminho seria alteração/customização do plugin (hook ou patch).
- Contras: código fornecedor modificado (upgrade quebra), ownership ambíguo, rollback complexo, risco de drift de versão. Não recomendado sem contribuição upstream.

### C — Batch repair aprovado (legado)

Execução one-shot com credencial admin, dry-run → candidatos → diff → aprovação → batch limitado → verify → audit.

- Útil como ação de saneamento do legado divergente (ex.: usuários criados antes dos mappers).
- **Não atende** o requisito contínuo (nome pode divergir depois). Não pode ser a solução única.

## Recomendação

**A + C**: credencial técnica dedicada para paridade contínua (A), mais um batch one-shot aprovado para zerar o drift legado (C). B descartada por ownership/upgrade risk.

## Pendências de decisão (owner)

1. Aprovar a existência da credencial técnica de profile-sync e seu perfil GLPI mínimo.
2. Definir quem executa o batch legado (escopo: usuários com firstname/realname vazios ou divergentes dos claims atuais).
3. Registrar em que fase o caminho de write do `ProfileSyncService` é reativado (o código já implementa read→diff→PATCH→reread→verify no shape necessário — a diferença é apenas a credencial usada).

## Fora de escopo

- Não expandir a credencial H12 (doc-upload).
- Não conceder `user` UPDATE a perfis de colaborador.
- Nenhum write em `Administration/User` foi executado por esta decisão.
