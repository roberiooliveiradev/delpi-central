# Minha DELPI — Padrão de Erro

> **Arquivo:** `docs/11-padroes-de-desenvolvimento/padrao-de-erro.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** padrão de erro para APIs da Minha DELPI

---

## 1. Objetivo

Este documento define o padrão de erro para APIs da Minha DELPI.

O objetivo é manter respostas previsíveis para o Portal, plugins e integrações.

---

## 2. Formato oficial

Toda resposta de erro deve seguir:

```json
{
  "errors": [
    {
      "code": "validation_error",
      "message": "Campo obrigatório.",
      "path": "name"
    }
  ]
}
```

---

## 3. Campos

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `code` | Sim | Código estável para lógica do frontend |
| `message` | Sim | Mensagem legível |
| `path` | Não | Campo ou `_global` |

---

## 4. `code`

O campo `code` é parte do contrato.

Regras:

- lowercase;
- sem espaços;
- sem acentos;
- usar namespace quando necessário;
- não depender de texto da mensagem.

Exemplos:

```text
unauthorized
forbidden
validation_error
plugin.not_found
plugin.version_already_exists
user.last_superadmin
```

---

## 5. `message`

A mensagem é para humanos.

Regras:

- clara;
- sem stack trace;
- sem SQL interno;
- sem token;
- sem senha;
- sem segredo;
- não usada como chave lógica no frontend.

---

## 6. `path`

O path indica onde ocorreu o problema.

Exemplos:

```text
_global
name
email
$.version
$.routes[0].path
query.page
path.plugin_id
```

---

## 7. Status HTTP

| Status | Uso |
|---:|---|
| `400` | Requisição inválida |
| `401` | Não autenticado |
| `403` | Autenticado sem permissão |
| `404` | Recurso inexistente |
| `409` | Conflito |
| `422` | Entrada semanticamente inválida |
| `500` | Erro inesperado |

---

## 8. Erro de autenticação

```json
{
  "errors": [
    {
      "code": "unauthorized",
      "message": "Authentication required",
      "path": "_global"
    }
  ]
}
```

Status:

```text
401
```

---

## 9. Erro de autorização

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

Status:

```text
403
```

---

## 10. Erro de validação

```json
{
  "errors": [
    {
      "code": "validation_error",
      "message": "Name is required",
      "path": "name"
    }
  ]
}
```

Status:

```text
400
```

ou:

```text
422
```

conforme decisão da rota.

---

## 11. Erro de conflito

Exemplo:

```json
{
  "errors": [
    {
      "code": "plugin.version_already_exists",
      "message": "This version is already registered",
      "path": "$.version"
    }
  ]
}
```

Status:

```text
409
```

---

## 12. Erro interno

```json
{
  "errors": [
    {
      "code": "internal_server_error",
      "message": "Internal server error",
      "path": "_global"
    }
  ]
}
```

Status:

```text
500
```

Nunca expor detalhes internos.

---

## 13. Tradução de exceções

Use cases podem lançar exceções de domínio/aplicação.

Controllers devem traduzir essas exceções para:

```text
status HTTP
errors[]
```

Evitar use case retornando resposta HTTP diretamente.

---

## 14. Tratamento no Portal

O Portal deve usar `code` para lógica.

Exemplo:

```typescript
if (error.code === "forbidden") {
  showAccessDenied()
}
```

Não usar `message` como chave lógica.

---

## 15. Checklist para novo erro

- [ ] Possui `code` estável.
- [ ] Possui `message` clara.
- [ ] Possui `path` quando aplicável.
- [ ] Usa status HTTP correto.
- [ ] Não vaza detalhe sensível.
- [ ] Está documentado na rota.
- [ ] Portal consegue tratar pelo `code`.
- [ ] Teste cobre o erro.

---

## 16. Anti-padrões

Evitar:

```text
Retornar string solta.
Retornar HTML.
Retornar traceback.
Retornar Exception completa.
Usar message como contrato.
Usar códigos diferentes para o mesmo erro.
Retornar 200 com erro.
Vazar token, senha, SQL ou stack trace.
```

---

## 17. Documentos relacionados

- [../04-core-api/erros-api.md](../04-core-api/erros-api.md)
- [padrao-de-rota.md](./padrao-de-rota.md)
- [README.md](./README.md)
