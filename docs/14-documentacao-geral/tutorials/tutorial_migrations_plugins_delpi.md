# Tutorial Oficial — Manipulação de Migrations de Plugins

## 1. Objetivo

Este fluxo serve para:

- subir o ambiente
- entrar no container correto
- consultar status das migrations
- aplicar migrations pendentes
- resetar o schema de um plugin
- reaplicar tudo do zero

Esse procedimento é para o contexto de plugins, que usa o banco `plugins_hub` e o runner `run_plugins_migrations.py`.

---

## 2. Pré-requisitos

Antes de executar os comandos, confirme que você está na pasta da infraestrutura:

```bash
cd ~/delpi-central/infra
```

---

## 3. Subir o ambiente com Docker Compose

Suba toda a stack:

```bash
docker compose up -d --build
```

Para conferir os containers:

```bash
docker ps --format "table {{.Names}}\t{{.Image}}"
```

Na stack atual, os principais para esse fluxo são:

- `delpi-api-delpi`
- `delpi-postgres-plugins`

---

## 4. Entrar no container da API

O script de migrations roda dentro do container da API:

```bash
docker exec -it delpi-api-delpi bash
```

Você ficará em algo como:

```bash
root@<container>:/app#
```

---

## 5. Comandos disponíveis no runner

O runner aceita comandos por argumento posicional:

- `status` → mostra o status das migrations
- `up` → aplica migrations pendentes
- `reset` → remove o schema inteiro do plugin

---

## 6. Ver status de um plugin

Para ver se as migrations de um plugin já foram aplicadas:

```bash
python scripts/run_plugins_migrations.py status --plugin strategic-indicators
```

Exemplo com outro plugin:

```bash
python scripts/run_plugins_migrations.py status --plugin quality-external-nc
```

### Regra importante

O script converte o slug do plugin em schema PostgreSQL trocando `-` por `_`.

Exemplo:

- `strategic-indicators` → `strategic_indicators`

---

## 7. Aplicar migrations pendentes de um plugin

Para aplicar apenas as migrations que ainda não foram executadas:

```bash
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
```

Exemplo com outro plugin:

```bash
python scripts/run_plugins_migrations.py up --plugin quality-external-nc
```

Se não houver migrations pendentes, o script informa isso e encerra normalmente.

---

## 8. Ver status de todos os plugins

Se quiser consultar todos os plugins com diretório em `migrations/plugins`:

```bash
python scripts/run_plugins_migrations.py status
```

---

## 9. Aplicar migrations pendentes de todos os plugins

Para rodar tudo o que estiver pendente:

```bash
python scripts/run_plugins_migrations.py up
```

---

## 10. Resetar completamente o schema de um plugin

### Quando usar

Use `reset` quando houver:

- checksum divergente
- schema corrompido
- necessidade de recriar tudo do zero em ambiente dev
- alteração estrutural em migration já aplicada

### Comando

```bash
python scripts/run_plugins_migrations.py reset --plugin strategic-indicators
```

O `reset` remove o schema inteiro do plugin com `DROP SCHEMA ... CASCADE`, então ele apaga:

- tabelas do plugin
- `schema_migrations`
- índices
- objetos dentro do schema

### Regra de segurança

O comando `reset` deve sempre exigir `--plugin` para evitar remoção acidental de múltiplos schemas.

---

## 11. Recriar do zero após reset

Fluxo padrão:

### 11.1 Resetar

```bash
python scripts/run_plugins_migrations.py reset --plugin strategic-indicators
```

### 11.2 Aplicar novamente

```bash
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
```

### 11.3 Conferir status

```bash
python scripts/run_plugins_migrations.py status --plugin strategic-indicators
```

Esse é o fluxo mais seguro para resolver problemas de checksum divergente em desenvolvimento.

---

## 12. Fluxo completo recomendado para um plugin

Exemplo com `strategic-indicators`.

### Subir ambiente

```bash
cd ~/delpi-central/infra
docker compose up -d --build
```

### Entrar na API

```bash
docker exec -it delpi-api-delpi bash
```

### Consultar status

```bash
python scripts/run_plugins_migrations.py status --plugin strategic-indicators
```

### Aplicar migrations

```bash
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
```

### Se houver problema de checksum, resetar e recriar

```bash
python scripts/run_plugins_migrations.py reset --plugin strategic-indicators
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
python scripts/run_plugins_migrations.py status --plugin strategic-indicators
```

---

## 13. Exemplo com outro plugin

```bash
python scripts/run_plugins_migrations.py status --plugin quality-external-nc
python scripts/run_plugins_migrations.py up --plugin quality-external-nc
```

Se precisar recriar tudo:

```bash
python scripts/run_plugins_migrations.py reset --plugin quality-external-nc
python scripts/run_plugins_migrations.py up --plugin quality-external-nc
python scripts/run_plugins_migrations.py status --plugin quality-external-nc
```

---

## 14. Quando usar cada comando

### `status`
Use para:

- verificar o que está aplicado
- conferir se existe pendência
- validar após um `up`

### `up`
Use para:

- aplicar migrations novas
- subir schema e tabela `schema_migrations` automaticamente
- concluir deploy local de plugin

### `reset`
Use para:

- apagar tudo do plugin em dev
- resolver migration alterada com checksum divergente
- reiniciar o schema do zero

---

## 15. Comportamento no startup da API

Existe um startup hook que pode executar as migrations automaticamente ao iniciar a aplicação, mas isso só acontece se a variável `RUN_PLUGINS_MIGRATIONS_ON_STARTUP=true` estiver habilitada.

Nesse caso, o startup chama o script com `up`.

Ou seja:

- startup automático → roda `up`
- operações manuais de manutenção → usar `status`, `up` e `reset` no container

---

## 16. Banco usado pelo runner

O runner conecta no banco de plugins usando as variáveis:

- `PLUGINS_DB_HOST`
- `PLUGINS_DB_PORT`
- `PLUGINS_DB_NAME`
- `PLUGINS_DB_USER`
- `PLUGINS_DB_PASSWORD`

No ambiente atual, o banco de plugins está configurado como:

- host: `postgres-plugins`
- port: `5432`
- database: `plugins_hub`
- user: `plugins_user`

---

## 17. Problemas comuns

### 1. `Checksum divergente`

**Causa:**

- uma migration já aplicada foi alterada

**Solução:**

```bash
python scripts/run_plugins_migrations.py reset --plugin strategic-indicators
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
```

---

### 2. `Pasta de migrations não encontrada`

**Causa:**

- o diretório do plugin não existe em `migrations/plugins/<slug>`

**Solução:**

- criar a pasta correta
- conferir o slug usado no comando

---

### 3. `Nenhuma migration encontrada`

**Causa:**

- a pasta existe, mas não tem arquivos `V*.sql`

**Solução:**

Criar arquivos no padrão:

```text
V001__nome_da_migration.sql
V002__outra_migration.sql
```

---

### 4. `psql: command not found`

**Causa:**

- o container da API não tem cliente `psql`

**Solução:**

- para usar o banco manualmente, entrar no container `delpi-postgres-plugins`
- para o fluxo normal de migrations, isso não é necessário, porque o script já conecta via `psycopg`

---

## 18. Checklist operacional

Antes de rodar:

- containers subidos
- `delpi-api-delpi` ativo
- plugin com pasta em `migrations/plugins/<slug>`
- arquivos nomeados como `V001__...sql`

Para aplicar:

```bash
python scripts/run_plugins_migrations.py up --plugin NOME_DO_PLUGIN
```

Para conferir:

```bash
python scripts/run_plugins_migrations.py status --plugin NOME_DO_PLUGIN
```

Para zerar:

```bash
python scripts/run_plugins_migrations.py reset --plugin NOME_DO_PLUGIN
```

---

## 19. Resumo rápido

### Subir ambiente

```bash
cd ~/delpi-central/infra
docker compose up -d --build
```

### Entrar na API

```bash
docker exec -it delpi-api-delpi bash
```

### Ver status

```bash
python scripts/run_plugins_migrations.py status --plugin strategic-indicators
```

### Aplicar

```bash
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
```

### Resetar

```bash
python scripts/run_plugins_migrations.py reset --plugin strategic-indicators
```

### Reaplicar

```bash
python scripts/run_plugins_migrations.py up --plugin strategic-indicators
python scripts/run_plugins_migrations.py status --plugin strategic-indicators
```

---

## 20. Fluxo recomendado no dia a dia

Para rotina normal:

```bash
python scripts/run_plugins_migrations.py status --plugin NOME_DO_PLUGIN
python scripts/run_plugins_migrations.py up --plugin NOME_DO_PLUGIN
python scripts/run_plugins_migrations.py status --plugin NOME_DO_PLUGIN
```

Para correção de ambiente quebrado:

```bash
python scripts/run_plugins_migrations.py reset --plugin NOME_DO_PLUGIN
python scripts/run_plugins_migrations.py up --plugin NOME_DO_PLUGIN
python scripts/run_plugins_migrations.py status --plugin NOME_DO_PLUGIN
```

