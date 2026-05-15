# Minha DELPI — Core API: Migrations

> **Arquivo:** `docs/04-core-api/migrations.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** migrations da Core API com Flask-Migrate/Alembic

---

## 1. Objetivo

Este documento descreve como funcionam as **migrations** da Core API da Minha DELPI.

As migrations são responsáveis por versionar o schema do banco `postgres-core`, mantendo o banco alinhado aos models SQLAlchemy da aplicação.

---

## 2. Ferramentas usadas

A Core API usa:

```text
Flask-Migrate
Alembic
SQLAlchemy
PostgreSQL
```

A extensão Flask-Migrate é inicializada em:

```text
app/extensions/migrate.py
```

Conteúdo conceitual:

```python
migrate = Migrate()
```

No bootstrap da aplicação:

```python
migrate.init_app(app, db)
```

---

## 3. Banco alvo

As migrations da Core API atuam no banco:

```text
postgres-core
```

Variáveis usadas pela aplicação:

```env
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

A URI é montada em:

```text
app/infrastructure/config/settings.py
```

Formato conceitual:

```text
postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>
```

---

## 4. Localização dos arquivos

Estrutura esperada:

```text
core-api/
  migrations/
    alembic.ini
    env.py
    script.py.mako
    versions/
      <revision>_<name>.py
```

A migration inicial conhecida:

```text
migrations/versions/7aa51b680332_initial_clean_schema_from_current_models.py
```

---

## 5. Papel do `env.py`

O arquivo:

```text
migrations/env.py
```

configura o ambiente do Alembic.

Responsabilidades:

- carregar a aplicação Flask;
- carregar metadata do SQLAlchemy;
- conectar no banco correto;
- permitir autogenerate;
- evitar geração de migration vazia quando não há mudanças;
- garantir que todos os models estejam registrados no metadata.

Ponto importante:

> Todos os models precisam ser importados no bootstrap antes do autogenerate, caso contrário o Alembic pode não enxergar tabelas e colunas corretamente.

---

## 6. Models e migrations

Models ficam em:

```text
app/infrastructure/db/models/
```

As migrations devem refletir esses models.

Regra:

```text
Alterou model persistente → gerar migration correspondente
```

Exemplos de alterações que exigem migration:

- nova tabela;
- nova coluna;
- remoção de coluna;
- alteração de tipo;
- novo índice;
- nova constraint;
- nova foreign key;
- alteração de nullable;
- alteração de default de banco.

---

## 7. Migration inicial

A migration inicial cria o schema base da Core API.

Tabelas criadas:

```text
apps
groups
notifications
permissions
roles
users
app_manifests
app_routes
app_versions
audit_logs
group_roles
role_permissions
user_favorite_apps
user_groups
user_permissions
user_roles
```

Essa migration representa o ponto de partida limpo do schema atual.

---

## 8. Domínios cobertos pela migration inicial

| Domínio | Tabelas |
|---|---|
| Usuários | `users` |
| RBAC | `roles`, `groups`, `permissions`, associativas e overrides |
| Plugin System | `apps`, `app_routes`, `app_manifests`, `app_versions` |
| Favoritos | `user_favorite_apps` |
| Notificações | `notifications` |
| Auditoria | `audit_logs` |

---

## 9. Tabelas de RBAC

Tabelas criadas para RBAC:

```text
users
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
user_permissions
```

Essas tabelas sustentam:

- roles diretas;
- grupos;
- roles por grupo;
- permissões por role;
- overrides individuais;
- superadmin.

---

## 10. Tabelas do Plugin System

Tabelas criadas para apps/plugins:

```text
apps
app_routes
app_manifests
app_versions
```

Essas tabelas sustentam:

- cadastro de apps;
- rotas navegáveis;
- manifesto vigente;
- histórico de versões;
- rollback;
- unregister;
- ativação/desativação.

---

## 11. Índices e constraints importantes

A migration inicial define constraints e índices relevantes.

Exemplos:

```text
users.email unique
roles.name unique
groups.name unique
permissions.code unique
permissions.module index
app_versions(app_id, version) unique
app_versions.app_id index
notifications.user_id index
audit_logs.user_id index
audit_logs.action index
```

Esses índices suportam consultas frequentes e integridade lógica.

---

## 12. Foreign keys e cascades

A migration inicial define várias FKs com cascade.

Exemplos:

```text
user_roles.user_id → users.id ON DELETE CASCADE
user_roles.role_id → roles.id ON DELETE CASCADE
user_groups.user_id → users.id ON DELETE CASCADE
user_groups.group_id → groups.id ON DELETE CASCADE
group_roles.group_id → groups.id ON DELETE CASCADE
group_roles.role_id → roles.id ON DELETE CASCADE
role_permissions.role_id → roles.id ON DELETE CASCADE
role_permissions.permission_id → permissions.id ON DELETE CASCADE
app_manifests.app_id → apps.id ON DELETE CASCADE
app_versions.app_id → apps.id ON DELETE CASCADE
user_favorite_apps.user_id → users.id ON DELETE CASCADE
user_favorite_apps.app_id → apps.id ON DELETE CASCADE
```

Cascades devem ser usados com cuidado, especialmente em dados de governança.

---

## 13. Fluxo para criar nova migration

Fluxo recomendado:

```text
1. Alterar model SQLAlchemy.
2. Rodar autogenerate.
3. Revisar migration gerada.
4. Ajustar nomes de constraints/índices, se necessário.
5. Testar upgrade em banco limpo.
6. Testar upgrade em banco existente.
7. Testar downgrade, se aplicável.
8. Commitar migration junto com alteração de model.
```

Comando conceitual:

```bash
flask db migrate -m "descricao_da_mudanca"
```

Aplicar:

```bash
flask db upgrade
```

Reverter uma revisão:

```bash
flask db downgrade -1
```

---

## 14. Execução dentro do Docker

### Automático no boot

`core-api/docker-entrypoint.sh`:

```text
aguarda DB_HOST:DB_PORT → flask db upgrade → python -m app.main
```

Na primeira subida do Compose, as migrations aplicam-se sem comando manual.

### Manual

```bash
cd infra
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
docker compose -f docker-compose.dev.yml exec core-api flask db current
```

Reset destrutivo: [../10-guias-operacionais/reset-banco-dev.md](../10-guias-operacionais/reset-banco-dev.md).

---

## 15. Cuidados com autogenerate

Autogenerate ajuda, mas não substitui revisão humana.

Sempre revisar:

- remoção acidental de tabelas;
- alteração indevida de tipos;
- nullable inesperado;
- default de Python versus default de banco;
- nomes de constraints;
- índices duplicados;
- FKs sem cascade ou com cascade indevido;
- diferenças causadas por imports incompletos dos models.

Regra:

> Nunca aplicar migration autogerada em produção sem revisão.

---

## 16. Migration vazia

O `env.py` possui comportamento para evitar gerar migration vazia quando não há mudanças detectadas.

Motivo:

- evitar poluir histórico;
- evitar revisões sem alteração real;
- manter linha do tempo de schema clara.

Se uma migration vazia for gerada, revisar:

- se models foram importados corretamente;
- se metadata está disponível;
- se a alteração foi realmente persistente;
- se a mudança é apenas em Python e não em banco.

---

## 17. Seeds não são migrations

A Core API possui seed de permissões base.

Permissões base:

```text
rbac.manage
users.view
users.manage
groups.manage
roles.manage
permissions.manage
apps.manage
apps.view
routes.manage
```

Esse seed roda no bootstrap da aplicação, fora do modo de teste.

Regra:

> Migration define estrutura. Seed define dados iniciais controlados pela aplicação.

Não misturar responsabilidades sem necessidade.

---

## 18. Dados de produção e migrations

Ao criar migrations para produção:

- preservar dados existentes;
- evitar drops destrutivos sem plano;
- migrar dados quando necessário;
- usar backfill em etapas para tabelas grandes;
- garantir rollback ou plano de correção;
- testar em cópia de banco real quando possível.

Exemplo de mudança segura:

```text
1. Adicionar coluna nullable.
2. Popular dados.
3. Tornar not null em migration posterior.
```

---

## 19. Alterações em permissões e plugins

Permissões de sistema podem ser adicionadas via seed.

Permissões de plugin são criadas pelo registro de plugin.

Evitar criar permissões de plugin diretamente por migration, exceto em casos de migração histórica controlada.

Regra:

```text
Permissões de plugin → manifesto/register
Permissões base da plataforma → seed controlado
Estrutura de permissions → migration
```

---

## 20. Alterações em app_routes e apps

Apps e rotas plugáveis devem ser criados pelo Plugin System, não manualmente por migration, salvo migração histórica planejada.

Regra:

```text
Estrutura de apps/app_routes → migration
Dados de plugins/apps → manifesto/register
```

---

## 21. Downgrade

Toda migration deveria considerar downgrade.

Em alguns casos, downgrade destrutivo pode ser difícil ou inseguro.

Recomendação:

- implementar downgrade quando seguro;
- documentar quando downgrade perde dados;
- evitar depender de downgrade em produção como única estratégia de rollback;
- preferir backup e plano de recuperação para mudanças críticas.

---

## 22. Checklist antes de aplicar migration

- [ ] Models foram atualizados.
- [ ] Migration foi gerada.
- [ ] Migration foi revisada manualmente.
- [ ] Upgrade funcionou em banco limpo.
- [ ] Upgrade funcionou em banco com dados existentes.
- [ ] Downgrade foi testado ou limitação documentada.
- [ ] Seeds continuam funcionando.
- [ ] Repositories foram ajustados.
- [ ] Use cases foram ajustados.
- [ ] Documentação foi atualizada.

---

## 23. Checklist para revisar migration autogerada

- [ ] Não há drop inesperado.
- [ ] Não há alteração indevida de tipo.
- [ ] Nullable está correto.
- [ ] Default de banco está correto.
- [ ] Índices estão corretos.
- [ ] Constraints únicas estão corretas.
- [ ] FKs estão corretas.
- [ ] Cascades estão corretos.
- [ ] Nomes de constraints são estáveis.
- [ ] Dados existentes foram considerados.

---

## 24. Pontos de atenção

1. Models precisam estar importados para Alembic enxergar o schema.
2. Autogenerate deve ser revisado manualmente.
3. Migrations alteram estrutura; seeds alteram dados iniciais.
4. Permissões de plugins devem vir do manifesto.
5. Apps/rotas de plugins devem vir do register.
6. Downgrades podem perder dados se não forem planejados.
7. Produção exige backup antes de migrations destrutivas.
8. Evitar migration vazia.
9. Alteração de variável de ambiente de banco pode apontar migration para banco errado.
10. Migration deve ser commitada junto com model correspondente.

---

## 25. Documentos relacionados

- [modelos-de-banco.md](./modelos-de-banco.md)
- [README.md](./README.md)
- [../09-banco-de-dados/core-db.md](../09-banco-de-dados/core-db.md)
- [../10-guias-operacionais/reset-banco-dev.md](../10-guias-operacionais/reset-banco-dev.md)

