# Minha DELPI — Banco de Dados `postgres-plugins`

> **Arquivo:** `docs/09-banco-de-dados/plugins-db.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** banco PostgreSQL de plugins, módulos de domínio e dados operacionais próprios da API DELPI

---

## 1. Objetivo

Este documento descreve o banco **`postgres-plugins`** da Minha DELPI.

O `postgres-plugins` é o banco PostgreSQL destinado a dados de plugins e módulos de domínio que não pertencem ao banco de governança da Core API, ao banco interno do Keycloak ou ao datasource TOTVS.

---

## 2. Responsabilidade do banco

O `postgres-plugins` deve armazenar dados operacionais próprios de módulos e plugins.

Exemplos de uso:

- dados do módulo de qualidade;
- não conformidades externas;
- ações de plano de ação;
- comentários;
- anexos/metadados;
- auditoria de módulo;
- indicadores materializados de plugins;
- configurações específicas de módulo que não sejam governança central.

---

## 3. O que não pertence ao `postgres-plugins`

Não devem ser armazenados neste banco:

- usuários da plataforma;
- roles;
- grupos;
- permissões globais;
- apps;
- rotas de apps;
- manifestos;
- versões de plugins;
- favoritos do Portal;
- notificações globais da Core API;
- dados internos do Keycloak;
- tabelas nativas do TOTVS.

Esses dados pertencem a outros bancos ou sistemas.

---

## 4. Relação com os outros bancos

| Banco | Responsabilidade |
|---|---|
| `postgres-core` | Governança da plataforma: usuários, RBAC, apps, manifestos, rotas, favoritos, notificações e auditoria central |
| `keycloak-db` | Dados internos do Keycloak |
| `postgres-plugins` | Dados de módulos de domínio e plugins |
| TOTVS | Dados corporativos/legados consumidos pela API DELPI |

Regra:

> O `postgres-plugins` não substitui o `postgres-core` nem o TOTVS. Ele é o banco próprio para domínios novos implementados no ecossistema de plugins.

---

## 5. Serviço Docker

Serviço:

```text
postgres-plugins
```

Container:

```text
delpi-postgres-plugins
```

Imagem:

```text
postgres:15
```

Volume persistente:

```text
postgres_plugins_data
```

Arquivo de inicialização:

```text
./docker/postgres/plugins-init.sql
```

---

## 6. Variáveis de ambiente do container

O container `postgres-plugins` usa:

```env
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
TZ=
```

No Compose, essas variáveis alimentam:

```yaml
POSTGRES_DB: ${PLUGINS_DB_NAME}
POSTGRES_USER: ${PLUGINS_DB_USER}
POSTGRES_PASSWORD: ${PLUGINS_DB_PASSWORD}
TZ: ${TZ}
```

---

## 7. Variáveis usadas pela API DELPI

A `api-delpi` acessa esse banco usando:

```env
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
```

Essas variáveis são injetadas no serviço `api-delpi`.

---

## 8. Exposição em desenvolvimento

No ambiente de desenvolvimento, o banco é exposto localmente:

```yaml
ports:
  - "5433:5432"
```

Isso permite conexão por ferramentas externas, usando:

```text
host: localhost
port: 5433
```

Em produção, a porta não deve ser exposta publicamente.

---

## 9. Consumidor principal

O consumidor principal do `postgres-plugins` é:

```text
api-delpi
```

A API DELPI usa esse banco para módulos de domínio próprios, enquanto continua podendo consultar TOTVS por outro datasource.

Fluxo:

```text
Plugin frontend
  ↓
api-delpi
  ↓
postgres-plugins
```

---

## 10. Separação entre TOTVS e `postgres-plugins`

A separação é obrigatória.

```text
TOTVS            → dados corporativos/legados existentes
postgres-plugins → dados novos de módulos/plugins
```

O módulo de qualidade deixa claro que dados novos do domínio não devem ficar no TOTVS nem reutilizar infraestrutura de SQL Server/TOTVS.

Regra:

> TOTVS pode ser fonte de consulta e enriquecimento, mas o domínio novo deve persistir no `postgres-plugins`.

---

## 11. Datasource dedicado na API DELPI

Módulos que usam `postgres-plugins` devem possuir infraestrutura dedicada de persistência.

Estrutura recomendada:

```text
app/infrastructure/persistence/plugins/
  plugin_postgres_connection.py
  plugin_base_repository.py
```

Repositories por módulo:

```text
app/infrastructure/persistence/plugins/repositories/<modulo>/
```

Exemplo para qualidade:

```text
app/infrastructure/persistence/plugins/repositories/external_nc/
```

---

## 12. Não reutilizar repository TOTVS

Não reutilizar:

```text
BaseRepository do TOTVS/SQL Server
```

para persistência no `postgres-plugins`.

Motivos:

- bancos diferentes;
- drivers diferentes;
- dialetos SQL diferentes;
- regras transacionais diferentes;
- responsabilidades arquiteturais diferentes;
- risco de acoplamento com legado.

---

## 13. Schemas por módulo

Recomenda-se organizar domínios por schema.

Exemplo:

```text
quality
```

Essa estratégia ajuda a:

- separar domínios;
- evitar colisão de nomes;
- organizar migrations;
- facilitar permissões e auditoria;
- manter clareza operacional.

---

## 14. Módulo de qualidade

Para o plugin de não conformidades externas, o schema sugerido é:

```text
quality
```

Tabelas sugeridas:

```text
quality.external_nc_suppliers
quality.external_nonconformities
quality.external_nc_root_causes
quality.external_nc_actions
quality.external_nc_effectiveness_checks
quality.external_nc_attachments
quality.external_nc_comments
quality.external_nc_team_members
quality.external_nc_audit_events
```

---

## 15. Regras de modelagem para módulos

Regras recomendadas:

- usar UUID como chave primária;
- usar timestamps em entidades relevantes;
- criar índices por status, fornecedor, vencimento e datas;
- preservar snapshots textuais de dados importantes;
- manter anexos desacoplados do storage físico;
- criar constraints coerentes com o workflow;
- separar auditoria de módulo quando necessário.

---

## 16. Estratégia de migrations

O `postgres-plugins` precisa de estratégia própria de versionamento.

Recomendações:

- manter migrations versionadas no repositório da `api-delpi`;
- separar migrations do contexto TOTVS das migrations do contexto plugins;
- não depender apenas de `plugins-init.sql` para evolução contínua;
- executar migrations como etapa explícita do deploy;
- testar upgrade e rollback em ambiente de homologação;
- documentar impactos de cada migration.

---

## 17. Uso de `plugins-init.sql`

O arquivo:

```text
./docker/postgres/plugins-init.sql
```

é executado na inicialização do container quando o volume está vazio.

Uso recomendado:

- bootstrap inicial;
- criação de extensões básicas;
- criação inicial de schemas, se necessário.

Limitação:

> `plugins-init.sql` não é substituto para migrations versionadas. Depois que o volume já existe, scripts em `/docker-entrypoint-initdb.d` não são reaplicados automaticamente.

---

## 18. Segurança

Regras de segurança:

1. Não expor a porta do banco em produção.
2. Usar usuário/senha fortes.
3. Não versionar credenciais reais.
4. Rotacionar credenciais quando necessário.
5. Aplicar menor privilégio possível.
6. Não armazenar tokens ou segredos em tabelas de domínio.
7. Validar JWT/permissão nos endpoints da API DELPI.
8. Auditar ações críticas em domínios sensíveis.

---

## 19. Backup e restore

O `postgres-plugins` contém dados operacionais de módulos.

Recomendações:

- incluir `postgres_plugins_data` na política de backup;
- documentar periodicidade;
- testar restore periodicamente;
- versionar migrations junto ao backup de aplicação;
- não executar `docker compose down -v` em produção;
- tratar reset local como operação destrutiva.

---

## 20. Checklist para criar um novo domínio no `postgres-plugins`

- [ ] Confirmar que o domínio não pertence ao `postgres-core`.
- [ ] Confirmar que o domínio não deve persistir no TOTVS.
- [ ] Definir schema.
- [ ] Definir entidades.
- [ ] Definir tabelas.
- [ ] Criar migrations.
- [ ] Criar conexão PostgreSQL dedicada.
- [ ] Criar base repository de plugins.
- [ ] Criar repositories concretos.
- [ ] Criar ports e use cases.
- [ ] Validar JWT/permissões nos endpoints.
- [ ] Definir auditoria.
- [ ] Documentar backup/restore.

---

## 21. Pontos de atenção

1. `postgres-plugins` é banco de domínios de plugins.
2. Não confundir com `postgres-core`.
3. Não confundir com `keycloak-db`.
4. Não usar como espelho genérico do TOTVS.
5. Domínios novos devem ter migrations próprias.
6. `plugins-init.sql` roda apenas na criação inicial do volume.
7. A `api-delpi` é o consumidor principal.
8. O Gateway não protege o banco.
9. Endpoints precisam validar autenticação e permissão.
10. Reset de volume apaga dados.

---

## 22. Documentos relacionados

```text
docs/07-api-delpi/banco-postgres-plugins.md
docs/07-api-delpi/modulos-de-dominio.md
docs/08-plugins/qualidade.md
docs/02-infraestrutura/docker-compose.md
docs/09-banco-de-dados/core-db.md
```
