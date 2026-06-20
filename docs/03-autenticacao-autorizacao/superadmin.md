# Minha DELPI — Superadmin

> **Arquivo:** `docs/03-autenticacao-autorizacao/superadmin.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** papel de superadmin, regras de bypass, proteção contra remoção do último superadmin e impactos no RBAC

---

## 1. Objetivo

Este documento descreve o papel de **superadmin** na Minha DELPI.

O superadmin é um usuário administrativo especial usado para garantir que a plataforma sempre tenha pelo menos uma identidade capaz de administrar RBAC, apps, rotas, plugins e recuperação operacional.

---

## 2. Conceito

Na Core API, o superadmin é representado pela flag:

```text
users.is_superadmin
```

Quando essa flag está ativa, o usuário possui bypass nos mecanismos comuns de autorização por permissão e nas policies avaliadas pelo `PolicyEngine`.

Isso significa que, para verificações de permissão simples, o superadmin não depende de estar vinculado a uma role que contenha a permission code exigida.

---

## 3. Responsabilidade do superadmin

O superadmin existe para:

- recuperar acesso administrativo em cenários críticos;
- administrar usuários, roles, grupos e permissões;
- gerenciar apps e plugins;
- registrar, atualizar, ativar, desativar e remover plugins;
- executar operações restritas que exigem autoridade máxima;
- evitar dependência exclusiva de uma role que pode ser removida por erro.

---

## 4. Diferença entre superadmin e permissões comuns

| Aspecto | Usuário comum | Superadmin |
|---|---:|---:|
| Precisa de JWT válido | Sim | Sim |
| Precisa existir como usuário local | Sim | Sim |
| Usa permissões efetivas do RBAC | Sim | Sim, mas pode bypassar validações |
| Passa por `require_permission` sem permissão explícita | Não | Sim |
| Passa por `require_any_permission` sem permissão explícita | Não | Sim |
| Passa por `require_all_permissions` sem permissão explícita | Não | Sim |
| Passa por `require_superadmin` | Não | Sim |
| Pode alterar outro superadmin | Não | Sim |

---

## 5. Superadmin não substitui autenticação

Superadmin não é uma forma de autenticação.

O usuário ainda precisa:

1. Autenticar no Keycloak.
2. Enviar JWT válido para a Core API.
3. Ser sincronizado como usuário local.
4. Ter `users.is_superadmin = true` no banco Core.

Fluxo:

```text
JWT válido
  ↓
Usuário local identificado
  ↓
users.is_superadmin verificado
  ↓
Bypass aplicado em decorators/policies quando cabível
```

---

## 6. Superadmin no Permission Resolver

O Permission Resolver considera a flag `is_superadmin`.

Comportamento esperado:

```text
Se is_superadmin = true:
    retornar todas as permissões cadastradas
```

Isso permite que `/me` exponha uma visão administrativa completa ao Portal.

Ponto importante:

> Mesmo que o superadmin receba todas as permissões efetivas, apps inativos continuam dependendo da regra de consulta de apps ativos. O superadmin não deve transformar automaticamente app inativo em app visível no fluxo comum.

---

## 7. Superadmin nos decorators

O arquivo de autorização HTTP implementa bypass de superadmin em decorators de permissão.

Decorators relevantes:

```text
require_permission
require_any_permission
require_all_permissions
```

Esses decorators retornam a função original quando o usuário possui `is_superadmin=True`.

---

## 8. `require_superadmin`

O decorator `require_superadmin()` é mais restritivo que uma permissão comum.

Uso:

```python
@require_superadmin()
def delete_user(...):
    ...
```

Regra:

```text
Se não houver usuário autenticado → unauthorized
Se user.is_superadmin não for true → forbidden
Se user.is_superadmin for true → executa endpoint
```

Esse decorator deve ser usado para operações sensíveis que não devem depender apenas de permission code.

---

## 9. Operações recomendadas para `require_superadmin`

Usar `require_superadmin` para ações como:

- remover usuário;
- promover ou rebaixar superadmin;
- executar procedimentos de recuperação;
- operações destrutivas globais;
- rotinas administrativas que podem comprometer o acesso ao sistema.

Evitar usar `require_superadmin` para tudo, pois isso esvazia o valor do RBAC.

---

## 10. Alteração de superadmin

A alteração da flag de superadmin é feita por use case dedicado:

```text
SetUserSuperadminUseCase
```

Entrada conceitual:

```text
actor_id
target_user_id
is_superadmin
actor_is_superadmin
```

Regra principal:

```text
Apenas um superadmin pode alterar a flag de superadmin de outro usuário.
```

Se o ator não for superadmin, a operação retorna erro de permissão.

---

## 11. Proteção contra remoção do último superadmin

A Core API protege o sistema contra a remoção do último superadmin.

Fluxo:

```text
Usuário alvo atualmente é superadmin
  ↓
Nova flag solicitada é false
  ↓
Conta total de superadmins
  ↓
Se total <= 1, bloqueia operação
```

Mensagem conhecida:

```text
O sistema deve possuir pelo menos 1 superadmin
```

Essa regra evita que a plataforma fique sem autoridade administrativa máxima.

---

## 12. Operação idempotente

Se a alteração solicitada não muda o estado atual, o use case retorna sucesso sem alterar banco.

Exemplo:

```text
Usuário já é superadmin
Solicitação: is_superadmin = true
Resultado: { "ok": true }
```

Isso torna a operação segura para repetição.

---

## 13. Evento emitido

Quando a flag de superadmin muda, a Core API coleta evento administrativo:

```text
entity: rbac
action: user_superadmin_updated
payload:
  userId
  is_superadmin
target_user_id: target_user_id
```

Esse evento permite:

- invalidar cache de permissões do usuário afetado;
- notificar o Portal;
- recarregar `/me` e `/me/apps`;
- atualizar UI administrativa durante a sessão.

---

## 14. Superadmin e Policy Engine

O `PolicyEngine` também aplica bypass de superadmin.

Fluxo:

```text
PolicyEngine.evaluate(name, context)
  ↓
Obtém g.current_user
  ↓
Se não houver usuário, retorna unauthorized
  ↓
Se user.is_superadmin = true, retorna True
  ↓
Busca policy registrada
  ↓
Executa policy
  ↓
Se policy falhar, retorna forbidden
```

Isso garante comportamento consistente entre decorators simples e policies mais complexas.

---

## 15. Superadmin e Portal

O Portal pode usar `is_superadmin` retornado por `/me` para adaptar a experiência.

Exemplos:

- exibir área administrativa;
- liberar abas de recuperação;
- exibir ações sensíveis;
- mostrar avisos de alto privilégio.

Atenção:

> O frontend nunca deve ser a única barreira. Toda ação sensível precisa ser protegida no backend.

---

## 16. Superadmin e apps/plugins

Superadmin normalmente consegue acessar todos os apps ativos retornados pela Core API, independentemente de permissões específicas de rota.

Isso não significa que:

- apps inativos devam aparecer;
- plugins removidos possam ser acessados;
- backends externos possam ignorar validação JWT;
- APIs operacionais devam confiar apenas no Portal.

Backends protegidos continuam devendo validar JWT e permissões/policies quando aplicável.

---

## 17. Riscos do uso incorreto

Riscos:

- excesso de usuários superadmin;
- operações sensíveis sem auditoria;
- dependência de superadmin para tarefas rotineiras;
- bypass usado para esconder falhas de RBAC;
- remoção acidental de todos os administradores se a proteção for quebrada.

Mitigações:

- manter poucos superadmins;
- usar roles para operação diária;
- auditar mudanças de superadmin;
- nunca remover a proteção do último superadmin;
- revisar endpoints que usam `require_superadmin`.

---

## 18. Boas práticas

1. Usar superadmin apenas para autoridade máxima e recuperação.
2. Usar RBAC para operação cotidiana.
3. Proteger alteração de superadmin com `require_superadmin` ou regra equivalente.
4. Nunca permitir zerar o número de superadmins.
5. Emitir evento em toda alteração real.
6. Invalidar cache RBAC do usuário afetado.
7. Recarregar `/me` e `/me/apps` no Portal após alteração.
8. Não criar atalhos de admin fora do fluxo auditável.
9. Não depender de role do Keycloak para superadmin da Minha DELPI.
10. Revisar periodicamente quem possui superadmin.

---

## 19. Checklist de validação

- [ ] `users.is_superadmin` existe no banco Core.
- [ ] Middleware coloca `is_superadmin` em `g.current_user`.
- [ ] `require_superadmin` bloqueia usuário comum.
- [ ] `require_permission` bypassa superadmin.
- [ ] `require_any_permission` bypassa superadmin.
- [ ] `require_all_permissions` bypassa superadmin.
- [ ] `PolicyEngine` bypassa superadmin.
- [ ] Alterar superadmin exige ator superadmin.
- [ ] Remover último superadmin é bloqueado.
- [ ] Evento `user_superadmin_updated` é emitido em alteração real.

---

## 20. Documentos relacionados

```text
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/03-autenticacao-autorizacao/policies-e-decorators.md
docs/03-autenticacao-autorizacao/jwt.md
docs/04-core-api/use-cases.md
docs/04-core-api/erros-api.md
```
