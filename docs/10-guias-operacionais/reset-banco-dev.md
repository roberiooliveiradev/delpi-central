# Minha DELPI — Guia Operacional: Reset de Banco em Desenvolvimento

> **Arquivo:** `docs/10-guias-operacionais/reset-banco-dev.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** reset destrutivo dos bancos locais de desenvolvimento

---

## 1. Objetivo

Este guia descreve como resetar o ambiente local da Minha DELPI em desenvolvimento.

O reset remove volumes Docker e recria o estado dos bancos. Ele é útil durante fases estruturais de desenvolvimento, especialmente quando há mudanças profundas em migrations, RBAC, Plugin System ou Keycloak.

---

## 2. Atenção: operação destrutiva

Este procedimento remove dados locais.

Ao executar reset com volumes, você perde:

- dados do `postgres-core`;
- dados do `keycloak-db`;
- dados do `postgres-plugins`;
- realm/client/usuários do Keycloak;
- apps/plugins registrados;
- permissões e vínculos RBAC locais;
- notificações, favoritos e auditoria locais.

Não executar em produção.

---

## 3. Quando usar

Use este guia quando:

- migrations locais estão quebradas;
- Alembic está com revision inválida;
- banco local está inconsistente;
- Keycloak local precisa ser recriado;
- dados de teste ficaram inválidos;
- você quer reconstruir o ambiente do zero.

Não use para:

- atualizar ambiente com dados importantes;
- produção;
- homologação com dados compartilhados;
- problemas simples que podem ser resolvidos com migration.

---

## 4. Entrar na pasta `infra`

A partir da raiz do repositório:

```bash
cd infra
```

---

## 5. Derrubar containers e volumes

Execute:

```bash
docker compose -f docker-compose.dev.yml down -v
```

Isso remove containers e volumes associados ao Compose.

---

## 6. Remover migrations somente quando necessário

Se o objetivo for recriar Alembic do zero em desenvolvimento, volte para a raiz:

```bash
cd ..
```

Remova a pasta de migrations da Core API:

```bash
rm -rf core-api/migrations
```

Atenção:

> Remover migrations é uma medida extrema de desenvolvimento. Em produção, migrations nunca devem ser apagadas para resolver inconsistência.

---

## 7. Subir novamente a stack

Volte para `infra`:

```bash
cd infra
```

Suba a stack:

```bash
docker compose -f docker-compose.dev.yml up --build
```

Ou em segundo plano:

```bash
docker compose -f docker-compose.dev.yml up --build -d
```

---

## 8. Entrar no container da Core API

```bash
docker exec -it delpi-core-api sh
```

ou:

```bash
docker compose -f docker-compose.dev.yml exec core-api sh
```

---

## 9. Recriar Alembic do zero

Dentro do container:

```bash
flask db init
```

Depois:

```bash
flask db migrate -m "initial full schema"
```

Depois:

```bash
flask db upgrade
```

Se tudo estiver correto, o Alembic deve executar o upgrade sem erro.

---

## 10. Validar estrutura do banco Core

Abra outro terminal e entre no Postgres Core:

```bash
docker exec -it delpi-postgres-core psql -U <usuario> -d <database>
```

Liste as tabelas:

```sql
\dt
```

Você deve ver tabelas como:

```text
users
roles
permissions
groups
apps
app_routes
app_manifests
app_versions
user_favorite_apps
notifications
audit_logs
```

Sair:

```sql
\q
```

---

## 11. Reconfigurar Keycloak

Como os volumes foram apagados, o Keycloak perdeu:

- realm;
- client;
- usuários;
- mappers;
- audience;
- configurações de redirect.

Recriar no Keycloak:

1. Realm da Minha DELPI.
2. Client do Portal.
3. Authorization Code Flow.
4. PKCE, se configurado no padrão local.
5. Audience esperada pela Core API.
6. Usuário inicial.
7. Claims `email`, `name` e `sub`.
8. Redirect URIs do Portal.

---

## 12. Validar Core API

Teste:

```bash
curl http://localhost/core-api/health
```

Resposta esperada:

```json
{
  "status": "ok"
}
```

---

## 13. Validar login

Após reconfigurar Keycloak:

1. Acesse `http://localhost`.
2. Faça login.
3. Verifique se o Portal retorna após autenticação.
4. Verifique se `/me` funciona.
5. Verifique se `/me/apps` retorna apps para usuário autorizado.

---

## 14. Registrar plugins novamente

Após reset, a tabela `apps`, manifestos, versões, rotas e permissões de plugins são apagadas.

Registre novamente os plugins necessários usando os manifestos oficiais.

Exemplo conceitual:

```bash
curl -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @delpi.manifest.json
```

O path exato deve seguir a rota atual da Core API.

---

## 15. Checklist final

Após reset completo, verificar:

- [ ] Containers estão rodando.
- [ ] Core API responde em `/core-api/health`.
- [ ] Portal carrega em `http://localhost`.
- [ ] Keycloak está acessível.
- [ ] Banco Core possui tabelas.
- [ ] Keycloak foi reconfigurado.
- [ ] Usuário inicial consegue autenticar.
- [ ] `/me` responde.
- [ ] `/me/apps` responde.
- [ ] Plugins necessários foram registrados.
- [ ] Permissões foram associadas a roles/grupos.

---

## 16. Comando rápido

Resumo destrutivo local:

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v

cd ..
rm -rf core-api/migrations

cd infra
docker compose -f docker-compose.dev.yml up --build -d

docker exec -it delpi-core-api sh

flask db init
flask db migrate -m "initial full schema"
flask db upgrade
```

---

## 17. Pontos de atenção

1. Nunca usar este procedimento em produção.
2. `down -v` remove dados dos bancos.
3. Remover migrations é aceitável apenas em fase estrutural/local.
4. Após reset, Keycloak precisa ser reconfigurado.
5. Após reset, plugins precisam ser registrados novamente.
6. Após reset, roles e permissões precisam ser reassociadas.
7. A Core API pode subir antes do banco estar pronto; aguarde ou reinicie.
8. `plugins-init.sql` só roda na criação inicial do volume.
9. Validar healthcheck antes de investigar frontend.
10. Documentar alterações se o procedimento mudar.

---

## 18. Documentos relacionados

```text
docs/10-guias-operacionais/subir-ambiente-dev.md
docs/10-guias-operacionais/configurar-keycloak.md
docs/10-guias-operacionais/registrar-plugin.md
docs/02-infraestrutura/docker-compose.md
docs/04-core-api/migrations.md
```
