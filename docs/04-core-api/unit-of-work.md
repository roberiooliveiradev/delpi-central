# Minha DELPI — Core API: Unit of Work

> **Arquivo:** `docs/04-core-api/unit-of-work.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** padrão Unit of Work, transações, repositories e eventos

---

## 1. Objetivo

Este documento descreve o padrão **Unit of Work** usado na Core API da Minha DELPI.

O Unit of Work centraliza o ciclo transacional da aplicação, disponibiliza repositories aos use cases, controla commit/rollback e publica eventos após persistência bem-sucedida.

---

## 2. Papel do Unit of Work

O Unit of Work é a fronteira transacional da Core API.

Responsabilidades principais:

- agrupar repositories em uma única unidade de trabalho;
- compartilhar a mesma sessão SQLAlchemy entre repositories;
- controlar commit;
- controlar rollback;
- coletar eventos durante a execução dos use cases;
- publicar eventos após commit bem-sucedido;
- encapsular detalhes de infraestrutura para a camada de aplicação.

---

## 3. Arquivos principais

Arquivos relacionados:

```text
app/application/unit_of_work.py
app/infrastructure/persistence/sqlalchemy/unit_of_work.py
app/application/event_bus.py
app/domain/events/admin_events.py
```

O arquivo de aplicação define o contrato/abstração.

O arquivo de infraestrutura implementa o Unit of Work usando SQLAlchemy e repositories concretos.

---

## 4. Fluxo transacional esperado

Fluxo padrão:

```text
Controller HTTP
  ↓
with SqlAlchemyUnitOfWork() as uow:
  ↓
Instancia use case
  ↓
Executa use case
  ↓
Use case usa repositories
  ↓
Use case coleta eventos
  ↓
Sai do contexto sem erro
  ↓
Unit of Work executa commit
  ↓
Unit of Work publica eventos
```

Exemplo conceitual:

```python
with SqlAlchemyUnitOfWork() as uow:
    use_case = RegisterPluginUseCase(uow)
    result = use_case.execute(manifest)

return jsonify(result), 201
```

---

## 5. Commit e publicação de eventos

O padrão correto é publicar eventos somente depois que a transação foi confirmada.

Fluxo:

```text
use_case.execute()
  ↓
uow.collect_event(...)
  ↓
uow.commit()
  ↓
event_bus.publish(events)
```

Motivo:

> Eventos devem refletir mudanças persistidas. Se a transação falhar, eventos não devem ser emitidos como se a alteração tivesse ocorrido.

---

## 6. Rollback

Se ocorrer exceção durante o bloco `with`, o Unit of Work deve executar rollback.

Fluxo:

```text
with uow:
  use_case.execute()
  ↓
Exceção
  ↓
uow.rollback()
  ↓
Eventos não são publicados
```

Regra:

> Falhas de validação, erro de banco ou exceções de regra devem impedir commit e publicação de eventos.

---

## 7. Repositories expostos

O Unit of Work SQLAlchemy expõe repositories para os principais domínios.

Repositories conhecidos:

```text
users
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
rbac_query
admin_apps
admin_routes
app_query
plugins
plugin_manifests
plugin_permissions
plugin_routes
plugin_versions
favorites
notifications
audit
```

Também podem existir aliases de compatibilidade para nomes antigos.

---

## 8. Repositories de RBAC

Repositories relacionados a RBAC:

```text
users
roles
groups
permissions
user_roles
user_groups
group_roles
role_permissions
rbac_query
```

Uso:

- listar usuários;
- criar/atualizar/excluir roles;
- criar/atualizar/excluir grupos;
- atribuir roles a usuários;
- atribuir grupos a usuários;
- atribuir roles a grupos;
- atribuir permissões a roles;
- consultar usuários impactados por mudanças RBAC.

---

## 9. Repositories de apps e plugins

Repositories relacionados a apps/plugins:

```text
admin_apps
admin_routes
app_query
plugins
plugin_manifests
plugin_permissions
plugin_routes
plugin_versions
```

Uso:

- listar apps administrativos;
- listar apps autorizáveis para o Portal;
- registrar plugin;
- atualizar manifesto;
- consultar manifesto;
- criar histórico de versão;
- rollback;
- unregister;
- gerenciar rotas.

---

## 10. Repositories de usuário atual

Repositories relacionados a preferências e notificações:

```text
favorites
notifications
```

Uso:

- listar favoritos;
- adicionar favorito;
- remover favorito;
- listar notificações não lidas;
- marcar notificações como lidas;
- criar notificação.

---

## 11. Repository de auditoria

Repository:

```text
audit
```

Uso:

```text
Registrar ações auditáveis.
```

Método principal conhecido:

```text
log(data)
```

---

## 12. Coleta de eventos

Use cases coletam eventos por meio do Unit of Work.

Exemplo conceitual:

```python
self.uow.collect_event(
    AdminChangedEvent(
        entity="plugins",
        action="plugin_registered",
        payload={"pluginId": plugin_id, "version": version},
    )
)
```

Eventos coletados ficam pendentes até o commit.

---

## 13. Evento administrativo padrão

Evento principal:

```python
AdminChangedEvent(
    entity="...",
    action="...",
    payload={...},
    target_user_id=None,
)
```

Campos:

| Campo | Descrição |
|---|---|
| `entity` | Domínio afetado |
| `action` | Ação executada |
| `payload` | Dados complementares |
| `target_user_id` | Usuário alvo opcional |

Se `target_user_id` estiver preenchido, o evento pode ser emitido apenas para o usuário.

Se não estiver preenchido, tende a ser broadcast.

---

## 14. EventBus

Após commit, eventos são publicados no EventBus.

Fluxo conhecido:

```text
EventBus.publish(event)
  ↓
RbacEventHandler.handle(event)
  ↓
SocketIOEventDispatcher.dispatch(event)
```

Ou seja, eventos disparam dois tipos de efeitos:

1. Efeitos internos de domínio, como invalidação de cache RBAC.
2. Efeitos de infraestrutura, como emissão Socket.IO para o Portal.

---

## 15. RbacEventHandler

O `RbacEventHandler` reage a eventos que podem impactar permissões.

Responsabilidades:

- identificar usuários afetados;
- invalidar cache de permissões;
- acionar sincronização interna de IAM/permissões;
- tratar alterações diretas e indiretas de RBAC.

Exemplos de eventos relevantes:

```text
role_added_to_user
role_removed_from_user
roles_replaced
group_added_to_user
group_removed_from_user
groups_replaced
role_added_to_group
role_removed_from_group
group_roles_replaced
permission_added_to_role
permission_removed_from_role
role_permissions_replaced
user_superadmin_updated
```

---

## 16. SocketIOEventDispatcher

O dispatcher de Socket.IO emite eventos para o Portal.

Evento emitido:

```text
admin.changed
```

Se o evento tiver `target_user_id`:

```text
emit para room = target_user_id
```

Se não tiver:

```text
broadcast
```

Isso permite que o Portal reaja a mudanças administrativas em tempo real.

---

## 17. Exemplo: registro de plugin

Fluxo com Unit of Work:

```text
Controller recebe POST /admin/apps/register
  ↓
with SqlAlchemyUnitOfWork() as uow
  ↓
RegisterPluginUseCase.execute(manifest)
  ↓
Cria/atualiza app, manifesto, versão, permissões e rotas
  ↓
uow.collect_event(plugin_registered)
  ↓
Sai do with
  ↓
commit
  ↓
EventBus publica plugin_registered
  ↓
Socket.IO emite admin.changed
```

---

## 18. Exemplo: alteração de RBAC

Fluxo:

```text
Controller recebe POST /admin/rbac/roles/<role_id>/users/<user_id>
  ↓
AddRoleToUserUseCase
  ↓
Cria vínculo em user_roles
  ↓
Coleta evento role_added_to_user com target_user_id
  ↓
commit
  ↓
RbacEventHandler invalida cache do usuário
  ↓
Socket.IO envia admin.changed para o usuário
  ↓
Portal recarrega /me e /me/apps
```

---

## 19. Exemplo: alteração global de role

Fluxo:

```text
ReplaceRolePermissionsUseCase
  ↓
Substitui permissões da role
  ↓
Coleta role_permissions_replaced
  ↓
commit
  ↓
RbacEventHandler localiza usuários afetados pela role direta ou herdada
  ↓
Invalida cache desses usuários
  ↓
Socket.IO broadcast ou evento apropriado
```

---

## 20. Padrão recomendado para use cases

Use cases devem:

- receber `uow` no construtor;
- usar repositories por meio do `uow`;
- não criar sessão SQLAlchemy própria;
- não publicar eventos diretamente;
- coletar eventos via `uow.collect_event`;
- lançar exceções de regra quando necessário;
- retornar estruturas simples;
- evitar dependência de Flask.

Exemplo:

```python
class SomeUseCase:
    def __init__(self, uow):
        self.uow = uow

    def execute(self, data):
        entity = self.uow.some_repo.create(data)
        self.uow.collect_event(AdminChangedEvent(...))
        return {"ok": True, "id": str(entity.id)}
```

---

## 21. O que evitar

Evitar dentro de use cases:

```text
Abrir sessão SQLAlchemy própria.
Chamar db.session diretamente.
Publicar Socket.IO diretamente.
Acessar request Flask diretamente.
Acessar g.current_user diretamente.
Fazer commit manual sem necessidade.
Fazer rollback manual sem necessidade.
Misturar serialização HTTP com regra de negócio.
```

---

## 22. Inconsistências conhecidas

Durante a análise do código atual, foram observadas exceções ao padrão.

### 22.1 Use cases com commit/rollback interno

Alguns use cases administrativos em lote fazem controle transacional interno.

Exemplos conhecidos:

```text
BulkDeleteAdminAppsUseCase
BulkSetAdminAppsActiveUseCase
```

Risco:

- commit duplicado;
- eventos publicados fora do padrão;
- rollback inesperado;
- comportamento diferente dos demais use cases.

Recomendação:

```text
Padronizar para commit no Unit of Work externo.
```

---

### 22.2 Use case com contexto interno de UoW

`ListFavoriteAppsUseCase` conhecido abre `with self.uow:` internamente.

Risco:

- nested context;
- commit/rollback em operação de leitura;
- divergência do padrão usado pelos controllers.

Recomendação:

```text
Padronizar responsabilidade transacional no controller ou service de aplicação.
```

---

## 23. Regras para novos repositories no UoW

Ao adicionar novo repository:

1. Definir port no domínio, se aplicável.
2. Implementar repository concreto em infraestrutura.
3. Registrar repository no Unit of Work SQLAlchemy.
4. Usar o repository apenas via `uow` em use cases.
5. Evitar import direto de repository concreto na camada de aplicação.

---

## 24. Regras para novos eventos no UoW

Ao criar novo evento:

1. Definir evento em `domain/events`.
2. Coletar evento no use case.
3. Garantir publicação após commit.
4. Atualizar handlers se houver efeito interno.
5. Atualizar Portal se o evento exigir reação de frontend.
6. Documentar action, payload e entity.

---

## 25. Checklist de revisão de use case

- [ ] Recebe `uow` no construtor.
- [ ] Usa repositories via `uow`.
- [ ] Não acessa Flask diretamente.
- [ ] Não cria sessão própria.
- [ ] Não faz commit interno, salvo exceção justificada.
- [ ] Coleta eventos em vez de publicar diretamente.
- [ ] Retorna dados serializáveis.
- [ ] Regras de negócio ficam no use case/service, não no controller.
- [ ] Exceções são tratáveis pelo controller.
- [ ] Teste cobre sucesso e falha transacional.

---

## 26. Pontos de atenção

1. O Unit of Work é a fronteira transacional da Core API.
2. Eventos devem ser publicados apenas após commit.
3. Rollback deve impedir publicação de eventos.
4. Use cases devem depender de ports/repositories via UoW.
5. Controllers não devem manipular múltiplos repositories diretamente.
6. Alguns use cases atuais divergem do padrão transacional.
7. Cache RBAC depende de eventos para invalidação.
8. Socket.IO depende de eventos para atualizar o Portal.
9. Repositories devem compartilhar a mesma sessão dentro do UoW.
10. Padronização do UoW é essencial para manter Clean Architecture.

---

## 27. Documentos relacionados

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/use-cases.md
docs/04-core-api/repositories.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/notificacoes.md
docs/03-autenticacao-autorizacao/rbac.md
docs/05-plugin-system/registro-de-plugin.md
```

