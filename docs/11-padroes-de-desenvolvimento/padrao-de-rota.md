# Minha DELPI — Padrão de Rota

> **Arquivo:** `docs/11-padroes-de-desenvolvimento/padrao-de-rota.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** padrão para criação e manutenção de rotas HTTP na Core API e API DELPI

---

## 1. Objetivo

Este documento define o padrão de desenvolvimento para rotas HTTP na Minha DELPI.

Ele deve ser usado como referência para criar, revisar e manter endpoints na:

- Core API;
- API DELPI;
- backends de módulos de domínio;
- endpoints operacionais consumidos por plugins.

---

## 2. Princípio central

Rotas HTTP devem ser finas.

A rota não deve concentrar regra de negócio, SQL, autorização complexa ou montagem manual de dependências.

Fluxo recomendado:

```text
Route / Controller
  ↓
validação básica de entrada
  ↓
Composer ou Unit of Work
  ↓
Use Case
  ↓
Repository / Port / Service
  ↓
Resposta HTTP padronizada
```

---

## 3. Responsabilidade da rota

A rota deve ser responsável por:

- receber a requisição HTTP;
- extrair path params;
- extrair query params;
- extrair body JSON;
- validar entrada básica;
- verificar autenticação/autorização por decorator/middleware;
- chamar use case;
- transformar resultado em resposta HTTP;
- traduzir exceções conhecidas para erro padronizado.

---

## 4. O que não deve ficar na rota

Evitar em rotas:

```text
SQL direto.
Regra de negócio extensa.
Commit manual de transação.
Publicação direta de Socket.IO.
Cálculo complexo de permissão.
Acesso direto a models SQLAlchemy.
Acesso direto a banco TOTVS.
Montagem extensa de dependências.
Lógica de domínio.
```

---

## 5. Padrão na Core API

Na Core API, as rotas ficam em controllers HTTP.

Exemplos de arquivos:

```text
app/interfaces/http/health_controller.py
app/interfaces/http/me_controller.py
app/interfaces/http/apps_controller.py
app/interfaces/http/rbac_controller.py
```

O controller deve delegar para use cases usando Unit of Work.

Exemplo conceitual:

```python
@admin_apps_bp.post("/admin/apps/register")
@require_permission("apps.manage")
def register_plugin():
    payload = request.get_json(silent=True) or {}

    with SqlAlchemyUnitOfWork() as uow:
        use_case = RegisterPluginUseCase(uow)
        result = use_case.execute(payload)

    return jsonify(result), 201
```

---

## 6. Padrão na API DELPI

Na API DELPI, o padrão recomendado segue Clean Architecture:

```text
Route
 ↓
Composer
 ↓
UseCase
 ↓
Port
 ↓
Repository concreto
 ↓
Banco / TOTVS / Exporter / integração
```

A rota deve chamar o composer do módulo, não instanciar repositories manualmente.

Exemplo conceitual:

```python
@router.get("/quality/external-nc/nonconformities")
def list_nonconformities():
    query = parse_query(request)
    use_case = make_list_external_nonconformities_use_case()
    result = use_case.execute(query)
    return jsonify(result), 200
```

---

## 7. Nome de rotas

Usar nomes claros e orientados a recurso.

Bom:

```text
GET /me
GET /me/apps
GET /admin/apps
POST /admin/apps/register
GET /admin/rbac/roles
POST /apps/api-delpi/quality/external-nc/nonconformities
```

Evitar:

```text
GET /getData
POST /doAction
POST /process
GET /list
```

---

## 8. Métodos HTTP

Usar métodos HTTP conforme intenção:

| Método | Uso |
|---|---|
| `GET` | Leitura |
| `POST` | Criação, comandos e ações |
| `PUT` | Substituição completa |
| `PATCH` | Atualização parcial |
| `DELETE` | Remoção |

Exemplos:

```http
GET /admin/rbac/roles
POST /admin/rbac/roles
PUT /admin/rbac/roles/<role_id>
DELETE /admin/rbac/roles/<role_id>
```

---

## 9. Path params

Path params devem identificar recursos.

Exemplos:

```text
/admin/apps/<plugin_id>
/admin/rbac/roles/<role_id>
/me/notifications/<notification_id>/read
```

Regras:

- usar nomes específicos;
- validar formato quando necessário;
- não expor IDs internos desnecessariamente;
- preferir IDs estáveis de domínio quando fizer sentido.

---

## 10. Query params

Query params devem ser usados para filtros, paginação e ordenação.

Padrão recomendado:

```text
q
page
page_size
sort
direction
status
from
to
```

Exemplo:

```http
GET /admin/apps?q=dashboard&page=1&page_size=20&sort=name&direction=asc
```

---

## 11. Body JSON

Para endpoints que recebem corpo, usar JSON.

A rota deve validar se o body existe quando obrigatório.

Exemplo:

```python
payload = request.get_json(silent=True)

if payload is None:
    return bad_request("invalid_json", "JSON body is required")
```

---

## 12. Autenticação

Rotas protegidas devem exigir autenticação.

Na Core API, usar decorators:

```python
@require_auth
```

ou decorators de permissão, que também pressupõem usuário autenticado.

Na API DELPI, endpoints protegidos devem validar JWT de forma equivalente.

---

## 13. Autorização

Rotas administrativas e operacionais sensíveis devem exigir permissão explícita.

Exemplos:

```python
@require_permission("apps.manage")
@require_permission("rbac.manage")
@require_superadmin
```

Evitar proteger apenas no frontend.

Regra:

> O frontend pode esconder botão. O backend deve bloquear ação.

---

## 14. Respostas de sucesso

Respostas devem ser previsíveis.

Exemplo de objeto:

```json
{
  "ok": true
}
```

Exemplo de recurso:

```json
{
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs"
}
```

Exemplo paginado:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0
  }
}
```

---

## 15. Respostas de erro

Erros devem seguir o padrão:

```json
{
  "errors": [
    {
      "code": "forbidden",
      "message": "Permission denied",
      "path": "_global"
    }
  ]
}
```

Não retornar HTML, traceback ou mensagens técnicas sensíveis.

---

## 16. Status HTTP

Usar status adequados:

| Status | Uso |
|---:|---|
| `200` | Sucesso com conteúdo |
| `201` | Criado |
| `204` | Sucesso sem conteúdo |
| `400` | Entrada inválida |
| `401` | Não autenticado |
| `403` | Sem permissão |
| `404` | Não encontrado |
| `409` | Conflito |
| `422` | Semanticamente inválido |
| `500` | Erro inesperado |

---

## 17. Paginação

Listagens administrativas e operacionais devem ser paginadas quando podem crescer.

Parâmetros recomendados:

```text
page
page_size
```

Resposta:

```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

## 18. Eventos

Rotas não devem publicar eventos diretamente.

Fluxo correto:

```text
Rota
  ↓
Use case
  ↓
uow.collect_event(...)
  ↓
commit
  ↓
EventBus publica
```

Na API DELPI, se houver eventos, seguir padrão equivalente com camada de aplicação.

---

## 19. Logging

A rota pode registrar logs operacionais simples, mas não deve:

- logar tokens;
- logar senhas;
- logar secrets;
- logar payloads sensíveis completos;
- expor dados pessoais sem necessidade.

---

## 20. Checklist para nova rota

- [ ] Nome da rota é orientado a recurso.
- [ ] Método HTTP está correto.
- [ ] Autenticação foi definida.
- [ ] Permissão foi definida quando necessário.
- [ ] Query params foram documentados.
- [ ] Body foi documentado.
- [ ] Resposta de sucesso foi definida.
- [ ] Erros foram definidos.
- [ ] Rota chama use case.
- [ ] Rota não contém SQL.
- [ ] Rota não acessa repository diretamente sem necessidade.
- [ ] Rota não publica evento diretamente.
- [ ] Testes cobrem sucesso e erro.
- [ ] Documentação foi atualizada.

---

## 21. Documentos relacionados

- [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md)
- [padrao-de-erro.md](./padrao-de-erro.md)
- [padrao-de-use-case.md](./padrao-de-use-case.md)
- [README.md](./README.md)
