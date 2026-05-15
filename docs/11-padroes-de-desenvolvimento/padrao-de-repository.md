# Minha DELPI — Padrão de Repository

> **Arquivo:** `docs/11-padroes-de-desenvolvimento/padrao-de-repository.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** padrão para repositories, ports e acesso a dados

---

## 1. Objetivo

Este documento define o padrão de desenvolvimento para repositories na Minha DELPI.

Repositories encapsulam acesso a dados e protegem a camada de aplicação de detalhes de banco, ORM, SQL, TOTVS ou storage externo.

---

## 2. Princípio central

Use cases não devem depender de detalhes de persistência.

Fluxo:

```text
Use Case
  ↓
Port / Repository
  ↓
Implementação concreta
  ↓
Banco / serviço externo
```

---

## 3. Responsabilidade do repository

Um repository deve:

- consultar dados;
- criar registros;
- atualizar registros;
- remover registros;
- mapear models para estruturas de domínio/DTO;
- encapsular SQL/ORM;
- expor métodos claros para use cases.

---

## 4. O que não deve ficar no repository

Evitar:

```text
Regra de negócio complexa.
Resposta HTTP.
jsonify.
request/g.
Socket.IO.
Publicação de eventos.
Cálculo final de autorização.
Commit manual fora do padrão.
Dependência do Portal.
```

---

## 5. Padrão na Core API

Na Core API, repositories concretos usam SQLAlchemy e são acessados via Unit of Work.

Exemplo:

```text
uow.users
uow.roles
uow.permissions
uow.admin_apps
uow.plugin_versions
uow.notifications
```

O use case não deve criar sessão SQLAlchemy própria.

---

## 6. Padrão na API DELPI

Na API DELPI, repositories devem ser separados por datasource.

Datasources principais:

```text
TOTVS
postgres-plugins
Portal RH
exporters/storages
```

Não reutilizar repository TOTVS para `postgres-plugins`.

---

## 7. Ports

Sempre que o domínio exigir independência, criar port.

Exemplo:

```python
class ExternalNonconformityRepositoryPort(Protocol):
    def create(self, data): ...
    def get_by_id(self, id): ...
    def list(self, query): ...
```

A implementação concreta fica em infraestrutura.

---

## 8. Nome de repositories

Usar nomes claros por recurso ou consulta.

Exemplos:

```text
UserRepository
RoleRepository
PluginManifestRepository
ExternalNonconformityRepository
TotvsProductRepository
PluginPostgresExternalNcRepository
```

Evitar:

```text
DataRepository
GenericRepository
Manager
Utils
```

quando o domínio é específico.

---

## 9. Métodos

Métodos devem ser pequenos e intencionais.

Bons exemplos:

```text
get_by_id
get_by_email
list_paginated
create
update
delete
exists
list_by_user_id
remove_by_module
```

Evitar métodos genéricos demais:

```text
execute_query
process
do
handle
```

---

## 10. Paginação

Repositories que listam coleções grandes devem suportar paginação.

Entrada conceitual:

```text
page
page_size
q
sort
direction
filters
```

Saída conceitual:

```text
items
total
```

O use case transforma isso em resposta de aplicação.

---

## 11. Transação

Repository não deve controlar commit por conta própria, salvo infraestrutura muito específica.

Na Core API:

```text
Unit of Work controla commit/rollback.
```

Na API DELPI, definir padrão equivalente por módulo/datasource.

---

## 12. Erros

Repository deve retornar `None` quando recurso não existe, quando esse for o contrato.

O use case decide se isso vira:

```text
404
409
422
```

Evitar repository retornar estrutura HTTP:

```json
{
  "errors": []
}
```

---

## 13. SQL

SQL pode existir no repository concreto, não na rota e não no use case.

Para consultas complexas:

- isolar em método nomeado;
- parametrizar entradas;
- evitar concatenação insegura;
- documentar filtros;
- testar a consulta.

---

## 14. Separação TOTVS e plugins

Regra obrigatória:

```text
TOTVS Repository != Plugin PostgreSQL Repository
```

Motivos:

- bancos diferentes;
- drivers diferentes;
- dialetos diferentes;
- domínios diferentes;
- ciclo transacional diferente.

---

## 15. Mapeamento

Repositories devem mapear dados técnicos para estruturas úteis à aplicação.

Evitar vazar models SQLAlchemy ou rows brutas quando isso cria acoplamento desnecessário.

Em consultas internas simples, retornar model pode ser aceitável quando a camada de aplicação já trabalha com esse contrato. Em módulos novos, preferir DTOs/entidades.

---

## 16. Checklist para novo repository

- [ ] Existe motivo claro para o repository.
- [ ] Nome é específico.
- [ ] Métodos são pequenos.
- [ ] Não contém HTTP.
- [ ] Não publica evento.
- [ ] Não faz autorização final.
- [ ] Não faz commit indevido.
- [ ] Usa sessão/conexão injetada.
- [ ] Trata paginação quando necessário.
- [ ] Usa queries parametrizadas.
- [ ] Possui teste de consulta crítica.
- [ ] Está registrado no Unit of Work ou composer.
- [ ] Documentação foi atualizada.

---

## 17. Anti-padrões

Evitar:

```text
Repository genérico que conhece todos os domínios.
Repository que abre conexão a cada método sem controle.
Repository que retorna Flask Response.
Repository que decide permissão.
Repository que mistura TOTVS e postgres-plugins.
Repository que faz commit surpresa.
Repository que engole exceção silenciosamente.
```

---

## 18. Documentos relacionados

- [../04-core-api/repositories.md](../04-core-api/repositories.md)
- [../04-core-api/unit-of-work.md](../04-core-api/unit-of-work.md)
- [../07-api-delpi/README.md](../07-api-delpi/README.md)
- [padrao-de-use-case.md](./padrao-de-use-case.md)
- [README.md](./README.md)
