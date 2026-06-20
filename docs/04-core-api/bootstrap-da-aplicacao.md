# Minha DELPI — Core API: Bootstrap da Aplicação

> **Arquivo:** `docs/04-core-api/bootstrap-da-aplicacao.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** inicialização da Core API Flask, extensões, middleware, blueprints, seeds e execução com Socket.IO

---

## 1. Objetivo

Este documento descreve o bootstrap da **Core API** da Minha DELPI.

O bootstrap é o processo de criação e configuração da aplicação Flask antes de ela começar a atender requisições. Ele define:

- qual configuração será carregada;
- quais extensões serão inicializadas;
- quais handlers Socket.IO serão registrados;
- quais blueprints HTTP serão expostos;
- como o middleware global de autenticação entra no ciclo de requisição;
- como os models são carregados para SQLAlchemy/Alembic;
- quando o seed de permissões base é executado;
- como a aplicação é iniciada pelo entrypoint principal.

---

## 2. Arquivos envolvidos

Os arquivos principais do bootstrap são:

```text
core-api/app/create_app.py
core-api/app/main.py
core-api/app/extensions/db.py
core-api/app/extensions/migrate.py
core-api/app/extensions/socket.py
core-api/app/infrastructure/config/settings.py
core-api/app/infrastructure/seeds/permissions_seed.py
core-api/app/interfaces/http/auth_middleware.py
core-api/app/interfaces/socket/socket_handlers.py
```

O arquivo central é:

```text
app/create_app.py
```

Ele implementa a factory:

```python
create_app(config_name: str | None = None) -> Flask
```

---

## 3. Visão geral do fluxo de bootstrap

Fluxo real da Core API:

```text
main.py
  ↓
create_app()
  ↓
Flask(__name__)
  ↓
carrega Config ou TestingConfig
  ↓
inicializa SQLAlchemy
  ↓
inicializa Flask-Migrate
  ↓
inicializa Socket.IO
  ↓
registra middleware global before_request
  ↓
registra blueprints HTTP
  ↓
abre app_context
  ↓
executa seed_base_permissions quando não está em TESTING
  ↓
retorna app Flask configurado
```

---

## 4. Application Factory

A Core API usa o padrão **Application Factory**.

A função responsável por construir a aplicação é:

```python
def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    ...
    return app
```

Esse padrão permite:

- criar app para desenvolvimento;
- criar app para produção;
- criar app para testes;
- inicializar extensões depois da criação do objeto Flask;
- manter o bootstrap centralizado;
- facilitar testes automatizados.

---

## 5. Seleção de configuração

O bootstrap escolhe a configuração conforme o parâmetro `config_name`.

Regra atual:

```python
if config_name == "testing":
    app.config.from_object(TestingConfig)
else:
    app.config.from_object(Config)
```

Isso significa:

| Valor de `config_name` | Configuração carregada |
|---|---|
| `"testing"` | `TestingConfig` |
| `None` ou outro valor | `Config` |

O modo de teste altera comportamentos importantes, como a desativação do middleware global e do seed de permissões.

---

## 6. Configuração padrão

A configuração padrão vem de:

```text
app.infrastructure.config.settings.Config
```

Ela deve centralizar variáveis como:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
SECRET_KEY
KEYCLOAK_JWKS_URL
KEYCLOAK_ISSUER
KEYCLOAK_AUDIENCE
INITIAL_SUPERADMIN_EMAIL
INITIAL_SUPERADMIN_NAME
KEYCLOAK_ADMIN_CLIENT_ID
KEYCLOAK_ADMIN_CLIENT_SECRET
KEYCLOAK_ADMIN_REALM
KEYCLOAK_ADMIN_URL
```

Essas variáveis são injetadas no container `core-api` pelo Docker Compose.

---

## 7. Configuração de teste

Quando `config_name == "testing"`, a aplicação usa:

```text
TestingConfig
```

E o bootstrap altera dois comportamentos:

1. O middleware global de autenticação não executa.
2. O seed de permissões base não executa.

Isso evita que testes dependam de Keycloak, JWT real ou estado externo de banco.

---

## 8. Inicialização do SQLAlchemy

A extensão SQLAlchemy é inicializada no bootstrap:

```python
db.init_app(app)
```

A instância `db` vem de:

```text
app/extensions/db.py
```

Responsabilidades:

- gerenciar conexão com PostgreSQL;
- fornecer `db.Model`;
- fornecer sessão;
- permitir repositories SQLAlchemy;
- expor metadata para migrations.

---

## 9. Inicialização do Flask-Migrate

A extensão Flask-Migrate/Alembic é inicializada no bootstrap:

```python
migrate.init_app(app, db)
```

A instância `migrate` vem de:

```text
app/extensions/migrate.py
```

Responsabilidades:

- permitir comandos `flask db`;
- associar Alembic ao app Flask;
- usar metadata do SQLAlchemy;
- versionar o schema do `postgres-core`.

---

## 10. Inicialização do Socket.IO

A extensão Socket.IO é inicializada no bootstrap:

```python
socketio.init_app(app)
```

A instância `socketio` vem de:

```text
app/extensions/socket.py
```

Responsabilidades:

- permitir conexões em tempo real;
- emitir eventos administrativos ao Portal;
- permitir salas por usuário;
- integrar eventos da Core API com frontend.

---

## 11. Registro dos handlers Socket.IO

Antes de criar a aplicação, `create_app.py` importa:

```python
import app.interfaces.socket.socket_handlers  # noqa
```

Esse import é intencional.

Ele força o carregamento dos decorators/handlers Socket.IO, garantindo que eventos como `connect` e `disconnect` estejam registrados na instância global `socketio`.

Padrão:

```text
import do módulo de handlers
  ↓
decorators @socketio.on(...)
  ↓
handlers registrados
```

Se esse import for removido, o Socket.IO pode subir sem handlers registrados.

---

## 12. Import dos blueprints HTTP

O bootstrap importa os blueprints:

```python
from app.interfaces.http.health_controller import health_bp
from app.interfaces.http.rbac_controller import rbac_bp
from app.interfaces.http.apps_controller import admin_apps_bp
from app.interfaces.http.me_controller import me_bp
```

Esses blueprints representam as entradas HTTP principais da Core API.

---

## 13. Registro dos blueprints

Os blueprints são registrados nesta ordem:

```python
app.register_blueprint(health_bp)
app.register_blueprint(rbac_bp)
app.register_blueprint(admin_apps_bp)
app.register_blueprint(me_bp)
```

Responsabilidades:

| Blueprint | Responsabilidade |
|---|---|
| `health_bp` | Healthcheck |
| `rbac_bp` | Administração de RBAC |
| `admin_apps_bp` | Administração de apps, plugins, manifestos, versões e rotas |
| `me_bp` | Usuário atual, apps autorizados, favoritos e notificações |

---

## 14. Middleware global de autenticação

O bootstrap registra um `before_request` global:

```python
@app.before_request
def before_request():
    if app.config.get("TESTING"):
        return

    result = authenticate()

    if result:
        return result
```

Esse middleware chama:

```text
app.interfaces.http.auth_middleware.authenticate
```

Ele é executado antes das requisições HTTP, exceto em modo `TESTING`.

---

## 15. Papel do `authenticate()`

O `authenticate()` é responsável por:

- ler o header `Authorization`;
- validar o JWT quando presente;
- sincronizar o usuário local;
- resolver roles, grupos e permissões;
- preencher `g.current_user`;
- retornar erro quando o token é inválido.

O middleware não torna todos os endpoints obrigatoriamente autenticados.

A proteção final de cada rota depende dos decorators, como:

```python
@require_auth
@require_permission("apps.manage")
@require_superadmin
```

---

## 16. Comportamento em endpoints públicos

Como o middleware global não bloqueia automaticamente requisições sem token, endpoints públicos continuam possíveis.

Exemplo:

```http
GET /health
```

A regra é:

```text
middleware tenta autenticar se houver token
  ↓
decorator da rota decide se autenticação é obrigatória
```

Isso permite que healthcheck funcione sem autenticação.

---

## 17. Import dos models

O bootstrap importa todos os models:

```python
from app.infrastructure.db.models import *  # noqa
```

Esse import é importante porque garante que os models sejam registrados no metadata do SQLAlchemy.

Impacto direto:

- migrations conseguem enxergar as tabelas;
- relationships são carregados;
- Alembic autogenerate funciona corretamente;
- repositories conseguem operar sobre modelos registrados.

Não remover esse import sem garantir outro mecanismo de registro dos models.

---

## 18. Registro das policies

O bootstrap também importa:

```python
import app.interfaces.http.security.policies
```

Esse import registra policies no `PolicyRegistry`.

O comentário no código indica a intenção:

```python
# IMPORTANT: registra policies
```

Sem esse import, policies declaradas por decorators ou registry podem não estar disponíveis em runtime.

---

## 19. Seed de permissões base

Após registrar blueprints e inicializar extensões, o bootstrap abre um contexto da aplicação:

```python
with app.app_context():
    if not app.config.get("TESTING"):
        try:
            seed_base_permissions(db.session)
        except Exception as e:
            logging.warning(f"Permission seed failed: {e}")
```

O seed chamado é:

```text
seed_base_permissions
```

Local:

```text
app/infrastructure/seeds/permissions_seed.py
```

---

## 20. Quando o seed roda

O seed roda somente quando:

```text
TESTING != true
```

Ou seja:

| Ambiente | Seed executa? |
|---|---:|
| Desenvolvimento | Sim |
| Produção | Sim |
| Testes | Não |

Isso evita interferência em testes automatizados.

---

## 21. Tolerância a falha no seed

O seed fica dentro de `try/except`.

Se falhar, a aplicação não deixa de subir automaticamente.

Comportamento:

```python
except Exception as e:
    logging.warning(f"Permission seed failed: {e}")
```

Isso evita que uma falha pontual de seed derrube o bootstrap inteiro, mas exige atenção operacional.

Ponto de atenção:

> Se o seed falhar, permissões base podem não existir. Isso pode quebrar RBAC, administração e acesso ao Portal.

---

## 22. Entry point principal

O arquivo:

```text
app/main.py
```

cria a aplicação:

```python
app = create_app()
```

E, quando executado diretamente, inicia o servidor via Socket.IO:

```python
socketio.run(
    app,
    host="0.0.0.0",
    port=8000,
    debug=False,
    use_reloader=False
)
```

Isso confirma que o servidor é executado pela instância Socket.IO, não por `app.run()` puro.

---

## 23. Relação com Docker Compose

No Docker Compose, a Core API recebe:

```yaml
FLASK_APP: app.create_app:create_app
```

E define o ambiente:

```yaml
FLASK_ENV: development
```

ou:

```yaml
FLASK_ENV: production
```

No desenvolvimento, o serviço usa:

```yaml
dockerfile: core-api/Dockerfile.dev
volumes:
  - ../core-api:/app
```

Em produção, usa:

```yaml
dockerfile: core-api/Dockerfile.prod
```

---

## 24. Bootstrap em desenvolvimento

Em desenvolvimento:

```text
core-api container
  ↓
código montado via volume
  ↓
FLASK_ENV=development
  ↓
create_app()
  ↓
middleware ativo
  ↓
seed ativo
  ↓
blueprints registrados
```

Características:

- código local montado em `/app`;
- banco `postgres-core` em container;
- Keycloak em `start-dev`;
- Gateway roteia para Core API;
- seed roda se o banco estiver disponível.

---

## 25. Bootstrap em produção

Em produção:

```text
core-api image
  ↓
FLASK_ENV=production
  ↓
create_app()
  ↓
Config
  ↓
extensões
  ↓
middleware
  ↓
blueprints
  ↓
seed
```

Características:

- sem volume de código;
- variáveis devem estar completas;
- banco deve estar migrado;
- Keycloak deve estar acessível para validação JWT;
- seed deve ser idempotente;
- Socket.IO precisa estar roteado corretamente pelo Gateway.

---

## 26. Bootstrap em testes

Em testes:

```python
create_app("testing")
```

Comportamento:

- usa `TestingConfig`;
- ignora `authenticate()` no `before_request`;
- não executa `seed_base_permissions`;
- permite testes isolados.

Esse comportamento é essencial para testes que não dependem de Keycloak real.

---

## 27. Ordem correta de inicialização

Ordem efetiva no bootstrap:

```text
1. Criar app Flask
2. Carregar configuração
3. Inicializar db
4. Inicializar migrate
5. Inicializar socketio
6. Registrar before_request
7. Registrar blueprints
8. Abrir app_context
9. Executar seed se aplicável
10. Retornar app
```

Essa ordem deve ser preservada salvo motivo técnico claro.

---

## 28. O que não deve ser feito no bootstrap

Evitar no bootstrap:

```text
Executar regra pesada de negócio.
Chamar APIs externas lentas.
Fazer migração automática de banco.
Registrar dados não idempotentes.
Depender de usuário autenticado.
Carregar plugins externos dinamicamente sem controle.
Publicar eventos.
Abrir múltiplas sessões fora do SQLAlchemy.
```

O bootstrap deve preparar a aplicação, não executar processos operacionais complexos.

---

## 29. Responsabilidades que pertencem ao bootstrap

Pertence ao bootstrap:

- criar app Flask;
- carregar configuração;
- inicializar extensões;
- registrar middleware;
- registrar blueprints;
- carregar models;
- registrar policies;
- carregar handlers Socket.IO;
- executar seeds idempotentes leves;
- retornar app pronto.

---

## 30. Responsabilidades que não pertencem ao bootstrap

Não pertence ao bootstrap:

- executar migrations;
- registrar plugins automaticamente sem comando explícito;
- criar usuários comuns;
- consultar APIs externas operacionais;
- montar menu do Portal;
- resolver permissões de usuário sem requisição;
- publicar eventos administrativos;
- executar jobs longos.

---

## 31. Checklist para alterar o bootstrap

Antes de alterar `create_app.py`, validar:

- [ ] A aplicação ainda sobe em desenvolvimento.
- [ ] A aplicação ainda sobe em produção.
- [ ] `create_app("testing")` continua funcionando.
- [ ] SQLAlchemy inicializa antes dos repositories.
- [ ] Migrate recebe `app` e `db`.
- [ ] Socket.IO continua inicializado.
- [ ] Handlers Socket.IO continuam importados.
- [ ] Blueprints continuam registrados.
- [ ] Middleware não bloqueia `/health`.
- [ ] Seed continua idempotente.
- [ ] Models continuam carregados para Alembic.
- [ ] Policies continuam registradas.

---

## 32. Troubleshooting

### 32.1 `/health` não responde

Verificar:

- container `core-api` está de pé;
- Gateway está roteando `/core-api/health`;
- blueprint `health_bp` foi registrado;
- app Flask iniciou sem erro.

---

### 32.2 Rotas administrativas retornam 404

Verificar:

- `rbac_bp` foi registrado;
- `admin_apps_bp` foi registrado;
- prefixos dos blueprints estão corretos;
- Gateway não está removendo path incorretamente.

---

### 32.3 JWT não é processado

Verificar:

- `before_request` está registrado;
- `authenticate()` está sendo chamado;
- `Authorization: Bearer` está presente;
- variáveis Keycloak estão corretas;
- `TESTING` não está ativo indevidamente.

---

### 32.4 Permissões base não existem

Verificar:

- seed executou no bootstrap;
- banco estava acessível;
- `seed_base_permissions` não falhou;
- logs contêm `Permission seed failed`;
- migrations já foram aplicadas.

---

### 32.5 Alembic não enxerga models

Verificar:

- `from app.infrastructure.db.models import *` ainda existe ou foi substituído por registro equivalente;
- todos os models estão importados no pacote `models`;
- `migrations/env.py` carrega a aplicação corretamente;
- metadata do SQLAlchemy contém as tabelas.

---

### 32.6 Socket.IO conecta mas eventos não funcionam

Verificar:

- `socketio.init_app(app)` executou;
- `app.interfaces.socket.socket_handlers` foi importado;
- Gateway suporta WebSocket/Socket.IO;
- token é enviado no handshake;
- handlers estão usando a mesma instância `socketio`.

---

## 33. Pontos de atenção

1. `create_app.py` é o centro do bootstrap da Core API.
2. `main.py` executa a aplicação via `socketio.run`.
3. O modo `testing` desativa middleware e seed.
4. O middleware global autentica, mas decorators protegem endpoints.
5. Blueprints precisam ser registrados explicitamente.
6. Models precisam ser importados para Alembic/SQLAlchemy.
7. Policies precisam ser importadas para registro.
8. Handlers Socket.IO precisam ser importados para registro.
9. Seed deve ser idempotente.
10. Falha no seed é logada como warning, não derruba a aplicação.

---

## 34. Documentos relacionados

```text
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/use-cases.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/repositories.md
docs/04-core-api/migrations.md
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/policies-e-decorators.md
docs/02-infraestrutura/docker-compose.md
```
