# Minha DELPI — Padrão de Use Case

> **Arquivo:** `docs/11-padroes-de-desenvolvimento/padrao-de-use-case.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** padrão para criação de casos de uso na Core API e API DELPI

---

## 1. Objetivo

Este documento define o padrão de desenvolvimento para **use cases** na Minha DELPI.

Use cases são a camada de aplicação responsável por orquestrar regras de negócio, repositories, services, validações e eventos.

---

## 2. Princípio central

Controller não deve conter regra de negócio.

Repository não deve decidir regra de aplicação.

Use case é o local principal para coordenar a ação.

Fluxo:

```text
Controller / Route
  ↓
Use Case
  ↓
Port / Repository / Service
  ↓
Resultado de aplicação
```

---

## 3. Responsabilidade do use case

Um use case deve:

- receber dados já extraídos da requisição;
- validar regras de aplicação;
- consultar repositories;
- chamar services de domínio quando necessário;
- coletar eventos;
- retornar resultado serializável;
- lançar exceções de domínio/aplicação quando algo falhar.

---

## 4. O que não deve ficar no use case

Evitar:

```text
request Flask.
g.current_user diretamente.
jsonify.
Response HTTP.
SQL direto.
Commit manual, salvo exceção justificada.
Socket.IO direto.
Imports de repository concreto, quando houver port/UoW.
Regra de infraestrutura.
```

---

## 5. Padrão na Core API

Na Core API, use cases recebem Unit of Work.

Exemplo:

```python
class UpdateAdminAppUseCase:
    def __init__(self, uow):
        self.uow = uow

    def execute(self, plugin_id: str, data: dict) -> dict:
        app = self.uow.admin_apps.get(plugin_id)

        if not app:
            raise NotFoundError("app.not_found", "App not found")

        updated = self.uow.admin_apps.update(plugin_id, data)

        self.uow.collect_event(AdminChangedEvent(
            entity="apps",
            action="app_updated",
            payload={"appId": plugin_id},
        ))

        return {"ok": True, "data": updated}
```

---

## 6. Padrão na API DELPI

Na API DELPI, o padrão recomendado é:

```text
UseCase
  ↓
Port
  ↓
Repository concreto
```

Exemplo:

```python
class ListExternalNonconformitiesUseCase:
    def __init__(self, repository):
        self.repository = repository

    def execute(self, query):
        return self.repository.list(query)
```

O use case deve depender de uma abstração ou contrato, não do detalhe de banco.

---

## 7. Nome de use cases

Usar nomes orientados a ação.

Padrões:

```text
Create<Resource>UseCase
Update<Resource>UseCase
Delete<Resource>UseCase
List<Resource>UseCase
Get<Resource>UseCase
Replace<Resource>UseCase
Add<Resource>To<Resource>UseCase
Remove<Resource>From<Resource>UseCase
```

Exemplos reais/conceituais:

```text
RegisterPluginUseCase
RollbackPluginVersionUseCase
ListUserAppsUseCase
SetUserSuperadminUseCase
ReplaceRolePermissionsUseCase
CreateExternalNonconformityUseCase
```

---

## 8. Método de execução

Usar método principal claro:

```python
execute(...)
```

Evitar múltiplos métodos públicos de ação no mesmo use case.

Se um use case começa a ter muitas ações, provavelmente ele precisa ser dividido.

---

## 9. Entrada de dados

Entrada deve ser explícita.

Bom:

```python
execute(user_id: str, app_id: str)
execute(plugin_id: str, manifest: dict)
execute(query: ListQuery)
```

Evitar:

```python
execute(request)
execute()
```

quando o método depende de estado global.

---

## 10. Saída de dados

Use case deve retornar dados simples:

- dict;
- list;
- DTO;
- dataclass;
- objeto de resultado de aplicação.

Não retornar:

```text
jsonify(...)
Flask Response
HTTP status
HTML
```

O controller traduz resultado para HTTP.

---

## 11. Validação

Validações de negócio pertencem ao use case.

Exemplos:

- plugin não existe;
- versão já existe;
- usuário não pode remover último superadmin;
- role não existe;
- rota não pertence ao app;
- transição de workflow inválida;
- não pode encerrar não conformidade sem eficácia aprovada.

Validação sintática simples pode ocorrer na rota, mas regra de aplicação deve ficar no use case.

---

## 12. Eventos

Na Core API, use cases coletam eventos por meio do Unit of Work.

Exemplo:

```python
self.uow.collect_event(AdminChangedEvent(
    entity="rbac",
    action="role_permissions_replaced",
    payload={"roleId": role_id}
))
```

O use case não deve publicar evento diretamente.

---

## 13. Transação

Regra recomendada:

```text
Use case não chama commit.
Unit of Work externo commita.
Eventos são publicados após commit.
```

Exceções existentes devem ser tratadas como legado técnico e revisadas.

---

## 14. Exceções

Use cases devem lançar exceções claras.

Categorias:

```text
NotFound
ValidationError
Conflict
Forbidden
DomainError
```

O controller deve traduzir para erro HTTP padronizado.

Evitar:

```python
raise Exception("erro")
```

sem código estável.

---

## 15. Idempotência

Alguns use cases devem ser idempotentes.

Exemplos:

- adicionar favorito já existente;
- marcar notificação já lida;
- ativar app que já está ativo;
- remover vínculo inexistente, quando a regra permitir.

Idempotência deve ser documentada no use case e no endpoint.

---

## 16. Checklist para novo use case

- [ ] Nome orientado a ação.
- [ ] Possui método `execute`.
- [ ] Recebe dependências no construtor.
- [ ] Não acessa HTTP diretamente.
- [ ] Não acessa `request`/`g`.
- [ ] Não retorna `jsonify`.
- [ ] Não contém SQL direto.
- [ ] Usa repository/port.
- [ ] Valida regra de aplicação.
- [ ] Coleta eventos, quando necessário.
- [ ] Não publica Socket.IO diretamente.
- [ ] Não faz commit, salvo exceção justificada.
- [ ] Retorna dado serializável.
- [ ] Possui teste de sucesso.
- [ ] Possui teste de erro.

---

## 17. Anti-padrões

Evitar:

```text
UseCase gigante com muitas ações.
UseCase que importa controller.
UseCase que depende de Flask.
UseCase que monta SQL.
UseCase que chama repository concreto diretamente sem necessidade.
UseCase que publica evento antes de persistir.
UseCase que engole exceções.
UseCase que retorna tupla HTTP.
```

---

## 18. Documentos relacionados

```text
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/11-padroes-de-desenvolvimento/padrao-de-rota.md
docs/11-padroes-de-desenvolvimento/padrao-de-repository.md
```
