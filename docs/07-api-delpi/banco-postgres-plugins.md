# Minha DELPI — API DELPI: Banco `postgres-plugins`

> **Arquivo:** `docs/07-api-delpi/banco-postgres-plugins.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** uso do banco `postgres-plugins` pela API DELPI e por módulos de domínio/plugins

---

## 1. Objetivo

Este documento descreve o uso do banco **`postgres-plugins`** pela API DELPI.

O `postgres-plugins` é o banco PostgreSQL destinado a módulos de domínio e plugins que não devem persistir dados no `postgres-core`, no banco do Keycloak ou no datasource TOTVS.

---

## 2. Papel do `postgres-plugins`

O `postgres-plugins` existe para persistir dados operacionais próprios de plugins e módulos de domínio.

Exemplos de uso:

- qualidade;
- não conformidades externas;
- indicadores específicos;
- dados complementares de módulos;
- tabelas de domínio que não pertencem ao TOTVS;
- dados persistidos por plugins oficiais.

O banco não substitui o `postgres-core`.

---

## 3. Separação entre bancos

A plataforma usa bancos com responsabilidades diferentes.

| Banco | Responsabilidade |
|---|---|
| `postgres-core` | Governança da plataforma: usuários, RBAC, apps, rotas, manifestos, favoritos, notificações |
| `keycloak-db` | Dados internos do Keycloak |
| `postgres-plugins` | Dados de plugins e domínios operacionais |
| TOTVS | Dados corporativos/legados consultados pela API DELPI |

Regra:

> Governança fica na Core API. Domínio operacional novo fica no `postgres-plugins`. TOTVS deve ser tratado como integração, não como banco de domínio novo.

---

## 4. Serviço Docker

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

## 5. Configuração no Docker Compose

Trecho conceitual:

```yaml
postgres-plugins:
  image: postgres:15
  container_name: delpi-postgres-plugins
  restart: unless-stopped

  environment:
    POSTGRES_DB: ${PLUGINS_DB_NAME}
    POSTGRES_USER: ${PLUGINS_DB_USER}
    POSTGRES_PASSWORD: ${PLUGINS_DB_PASSWORD}
    TZ: ${TZ}

  volumes:
    - postgres_plugins_data:/var/lib/postgresql/data
    - ./docker/postgres/plugins-init.sql:/docker-entrypoint-initdb.d/plugins-init.sql

  networks:
    - delpi-network
```

No ambiente de desenvolvimento, o banco é exposto localmente:

```yaml
ports:
  - "5433:5432"
```

---

## 6. Variáveis de ambiente

Variáveis usadas pela API DELPI:

```env
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
```

Variáveis usadas pelo container PostgreSQL:

```env
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
TZ=
```

---

## 7. Consumidor principal

O consumidor principal do `postgres-plugins` é:

```text
api-delpi
```

No Compose, a API DELPI depende de:

```yaml
depends_on:
  - keycloak
  - postgres-plugins
```

Isso significa que módulos hospedados na `api-delpi` podem usar o banco de plugins como persistência própria.

---

## 8. Datasource separado na API DELPI

Para evitar acoplamento com o datasource TOTVS, módulos persistidos em `postgres-plugins` devem possuir infraestrutura própria de conexão.

Estrutura recomendada:

```text
app/infrastructure/persistence/plugins/
  plugin_postgres_connection.py
  plugin_base_repository.py
```

Módulos específicos podem ter repositories próprios:

```text
app/infrastructure/persistence/plugins/repositories/<modulo>/
```

Exemplo para qualidade:

```text
app/infrastructure/persistence/plugins/repositories/external_nc/
```

---

## 9. Regra de isolamento

Regra obrigatória:

```text
Não reutilizar BaseRepository do TOTVS/SQL Server para persistência no postgres-plugins.
```

Motivo:

- bancos diferentes;
- drivers diferentes;
- transações diferentes;
- SQL dialeto diferente;
- responsabilidade arquitetural diferente;
- risco de misturar domínio novo com legado.

---

## 10. Schema por domínio

Para domínios novos, recomenda-se criar schema próprio.

Exemplo para qualidade:

```text
quality
```

Tabelas sugeridas para não conformidades externas:

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

Essa modelagem deve ser versionada por estratégia de migration própria do contexto de plugins.

---

## 11. Regras de modelagem

Regras recomendadas para tabelas de plugin:

- usar UUID como PK;
- ter timestamps em entidades relevantes;
- criar índices por status, fornecedor, vencimento e data quando aplicável;
- guardar snapshots textuais de dados externos importantes;
- desacoplar anexos do storage físico;
- manter constraints coerentes com fluxo de domínio;
- versionar migrations separadamente do contexto TOTVS.

---

## 12. Migrations de plugins

A especificação técnica exige estratégia de versionamento para o banco de plugins.

A separação deve ser clara entre:

```text
migrations do contexto TOTVS
migrations do contexto plugins
```

Recomendação:

- definir ferramenta oficial de migration para `postgres-plugins`;
- manter migrations versionadas no repositório da `api-delpi`;
- executar migrations como etapa explícita de deploy;
- não depender apenas de `plugins-init.sql` para evolução contínua;
- documentar schema e rollback de mudanças críticas.

---

## 13. Relação com o módulo de qualidade

A especificação de não conformidades externas define que o módulo deve ser composto por:

```text
frontend próprio do plugin
backend dentro da api-delpi
persistência no postgres-plugins
governança pela Core API
```

Isso torna o `postgres-plugins` o local correto para persistir o domínio do módulo.

---

## 14. O que não deve ir para `postgres-plugins`

Não devem ser persistidos no `postgres-plugins`:

- usuários da plataforma;
- roles;
- groups;
- permissions globais;
- apps;
- rotas;
- manifestos;
- versões de plugin;
- dados internos do Keycloak;
- tabelas nativas do TOTVS.

Esses dados pertencem a outros bancos ou sistemas.

---

## 15. O que deve ir para `postgres-plugins`

Podem ir para `postgres-plugins`:

- entidades de módulos de domínio;
- ocorrências de qualidade;
- ações;
- comentários;
- anexos metadados;
- auditorias específicas de módulo;
- dashboards materializados de plugin, se necessário;
- configurações específicas de módulo que não sejam governança central.

---

## 16. Segurança

A persistência no `postgres-plugins` não elimina a necessidade de autorização.

Regras:

- endpoints devem validar JWT;
- permissões devem ser verificadas por rota/caso de uso;
- dados de um módulo devem respeitar o RBAC da plataforma;
- auditoria deve ser mantida para ações críticas;
- não armazenar tokens ou segredos em tabelas de domínio.

---

## 17. Checklist para novo módulo usando `postgres-plugins`

- [ ] O módulo pertence à `api-delpi`.
- [ ] Existe schema próprio ou convenção clara de tabelas.
- [ ] Existe conexão PostgreSQL separada.
- [ ] Existe base repository própria para plugins.
- [ ] Repositories não usam infraestrutura TOTVS.
- [ ] Há migrations versionadas.
- [ ] Tabelas têm PK, índices e constraints.
- [ ] Entidades de domínio estão separadas da camada HTTP.
- [ ] Use cases controlam regra de aplicação.
- [ ] Endpoints validam JWT/permissão.
- [ ] Auditoria de ações críticas foi considerada.

---

## 18. Pontos de atenção

1. `postgres-plugins` não é banco da Core API.
2. `postgres-plugins` não é banco do Keycloak.
3. `postgres-plugins` não substitui TOTVS.
4. Módulos novos não devem persistir em TOTVS.
5. Repositories PostgreSQL de plugins devem ser separados dos repositories TOTVS.
6. `plugins-init.sql` é bootstrap inicial, não estratégia completa de migration.
7. Dados de governança continuam no `postgres-core`.
8. API DELPI é o consumidor principal do banco.
9. Gateway expõe API, mas não protege sozinho os dados.
10. A documentação de tabelas finais depende das migrations reais do módulo.

---

## 19. Documentos relacionados

```text
docs/07-api-delpi/visao-geral-api-delpi.md
docs/07-api-delpi/integracao-totvs.md
docs/07-api-delpi/modulos-de-dominio.md
docs/09-banco-de-dados/plugins-db.md
docs/08-plugins/qualidade.md
```
