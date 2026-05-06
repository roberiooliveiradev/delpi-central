# Minha DELPI — Plugins Backend-only

> **Arquivo:** `docs/05-plugin-system/backend-only.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** plugins do tipo `backend-only`

---

## 1. Objetivo

Este documento descreve plugins do tipo **backend-only** na Minha DELPI.

Plugins backend-only são usados para registrar módulos, serviços ou integrações que não possuem interface visual própria no Portal, mas que precisam existir no ecossistema da plataforma para fins de governança, permissões, dependências e descoberta técnica.

---

## 2. Conceito

Um plugin `backend-only` representa um módulo sem UI.

Ele pode ser usado para:

- registrar permissões de uma API;
- declarar dependências de outros plugins;
- representar um serviço backend usado por microfrontends;
- documentar integração com serviço interno;
- controlar acesso a recursos backend por RBAC;
- manter metadados de backend dentro do sistema de plugins.

Diferente de um microfrontend ou iframe, um backend-only não deve aparecer como uma tela navegável no Portal.

---

## 3. Tipo no manifesto

Para declarar um plugin backend-only, usar:

```json
{
  "type": "backend-only"
}
```

A versão de schema suportada continua sendo:

```json
{
  "schemaVersion": "1.0.0"
}
```

---

## 4. Regras principais

Plugins backend-only possuem regras específicas.

| Regra | Obrigatório |
|---|---:|
| `backend` deve existir | Sim |
| `backend.required` deve ser `true` | Sim |
| `backend.validateJwt` deve existir | Sim |
| `entry` não deve existir ou deve ser `null` | Sim |
| `routes` deve ser vazio | Sim |
| `ui` não é permitido | Sim |
| `permissions` deve conter ao menos uma permissão | Sim |

---

## 5. Campos proibidos

Para backend-only, estes campos não devem ser usados:

```json
{
  "entry": "/algum-entry",
  "routes": [
    {
      "path": "/apps/algum-backend",
      "label": "Backend"
    }
  ],
  "ui": {
    "renderMode": "embedded"
  }
}
```

Motivo:

> Backend-only não é uma aplicação visual navegável no Portal.

---

## 6. Campo `backend`

O campo `backend` descreve o serviço backend associado.

Estrutura:

```json
{
  "backend": {
    "required": true,
    "serviceName": "api-delpi",
    "baseUrl": "/apps/api-delpi",
    "validateJwt": true,
    "audience": "delpi-central",
    "issuer": "http://localhost/auth/realms/delpi",
    "requiredPermissionsHeader": "X-Required-Permissions"
  }
}
```

Campos:

| Campo | Obrigatório | Descrição |
|---|---:|---|
| `required` | Sim | Deve ser `true` em backend-only |
| `serviceName` | Não | Nome lógico do serviço |
| `baseUrl` | Não | URL base do backend |
| `validateJwt` | Sim | Define se backend valida JWT |
| `issuer` | Condicional | Obrigatório se `validateJwt=true` |
| `audience` | Condicional | Obrigatório se `validateJwt=true` |
| `requiredPermissionsHeader` | Não | Header opcional para permissões exigidas |

---

## 7. JWT em backend-only

Se `backend.validateJwt` for `true`, o manifesto deve declarar:

```json
{
  "issuer": "http://localhost/auth/realms/delpi",
  "audience": "delpi-central"
}
```

Campos obrigatórios nesse cenário:

```text
backend.issuer
backend.audience
```

Erros esperados se ausentes:

```text
backend_missing_issuer
backend_missing_audience
```

---

## 8. Permissões em backend-only

Mesmo sem UI, backend-only deve declarar permissões.

Exemplo:

```json
{
  "permissions": [
    {
      "code": "api-delpi.access",
      "name": "Acessar API DELPI",
      "description": "Permite consumir recursos da API DELPI.",
      "module": "api-delpi"
    }
  ]
}
```

Regras:

- `permissions` é obrigatório;
- deve conter ao menos um item;
- `module` deve ser igual ao `id` do plugin;
- `code` deve seguir padrão de permission code.

Recomendação forte:

```text
<plugin-id>.access
```

Exemplo:

```text
api-delpi.access
```

---

## 9. Manifesto completo de exemplo

```json
{
  "schemaVersion": "1.0.0",
  "id": "api-delpi",
  "name": "API DELPI",
  "description": "API operacional para integrações e domínios de negócio.",
  "version": "1.0.0",
  "type": "backend-only",
  "basePath": "/apps/api-delpi",
  "entry": null,
  "permissions": [
    {
      "code": "api-delpi.access",
      "name": "Acessar API DELPI",
      "description": "Permite consumir recursos da API DELPI.",
      "module": "api-delpi"
    }
  ],
  "routes": [],
  "backend": {
    "required": true,
    "serviceName": "api-delpi",
    "baseUrl": "/apps/api-delpi",
    "validateJwt": true,
    "issuer": "http://localhost/auth/realms/delpi",
    "audience": "delpi-central",
    "requiredPermissionsHeader": "X-Required-Permissions"
  },
  "metadata": {
    "owner": "DELPI",
    "kind": "operational-api"
  }
}
```

---

## 10. Registro

Backend-only é registrado pelo mesmo endpoint de plugins:

```http
POST /admin/apps/register
```

Permissão exigida:

```text
apps.manage
```

Durante o registro:

- cria registro em `apps`;
- salva manifesto em `app_manifests`;
- cria versão em `app_versions`;
- cria permissões em `permissions`;
- não cria rotas, pois `routes` deve ser vazio.

---

## 11. Como backend-only aparece na plataforma

Um backend-only pode existir em `apps`, mas normalmente não aparece como item navegável no Portal, porque não possui rotas.

Como o Portal recebe apps a partir das rotas autorizadas, um app sem rotas tende a não aparecer para navegação.

Uso principal:

- RBAC;
- dependências;
- metadados técnicos;
- governança de APIs;
- documentação de serviços plugáveis.

---

## 12. Dependências com backend-only

Plugins visuais podem depender de um plugin backend-only.

Exemplo:

```json
{
  "id": "dashboard-lmps",
  "dependencies": [
    "api-delpi"
  ]
}
```

Isso permite que o unregister do backend seja bloqueado se ainda houver plugins dependentes.

Fluxo de proteção:

```text
DELETE /admin/apps/api-delpi
  ↓
Core API lista manifestos
  ↓
Verifica dependencies
  ↓
Se outro plugin depende de api-delpi, bloqueia remoção
```

Erro:

```text
plugin.has_dependents
```

---

## 13. Atualização de backend-only

Mudanças não estruturais podem usar:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Exemplos:

- alterar nome;
- alterar descrição;
- alterar ícone, se usado;
- alterar metadados não estruturais.

Mudanças estruturais exigem nova versão via register:

- alterar permissões;
- alterar `basePath`;
- alterar `type`;
- alterar contrato do backend;
- alterar `validateJwt`, issuer ou audience de forma significativa.

---

## 14. Rollback

Backend-only também pode passar por rollback.

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

Efeitos:

- restaura `apps.version`;
- restaura manifesto vigente;
- remove e recria permissões do módulo;
- mantém ausência de rotas;
- emite evento `plugin_version_rolled_back`.

---

## 15. Relação com API DELPI

A API DELPI é um serviço real da stack Docker.

Ela pode ser representada por um manifesto backend-only quando for necessário governá-la dentro do Plugin System.

Exemplo de uso:

```text
api-delpi como backend-only
  ↓
permissões registradas na Core API
  ↓
microfrontends dependem de api-delpi
  ↓
unregister é protegido por dependencies
```

Regra:

> Registrar a API DELPI como backend-only não substitui a existência do serviço Docker `api-delpi`. O manifesto apenas declara esse serviço no sistema de governança da plataforma.

---

## 16. Segurança

Backends declarados como backend-only devem validar JWT quando expostos a usuários ou plugins.

Se `validateJwt=true`, o backend deve validar:

- assinatura;
- issuer;
- audience;
- expiração;
- claims necessárias.

Se também houver controle fino de permissão, o backend deve validar permissões exigidas pela rota ou recurso.

Ocultar UI no Portal não é controle de segurança suficiente.

---

## 17. Boas práticas

1. Usar backend-only para serviços sem UI.
2. Declarar pelo menos `<plugin-id>.access`.
3. Manter `module` igual ao `id`.
4. Declarar `backend.required=true`.
5. Usar `validateJwt=true` para serviços protegidos.
6. Declarar `issuer` e `audience` corretamente.
7. Não declarar rotas visuais.
8. Não declarar `ui`.
9. Usar `dependencies` em plugins visuais que dependem desse backend.
10. Versionar mudanças estruturais do contrato backend.

---

## 18. Checklist para backend-only

- [ ] `type` é `backend-only`.
- [ ] `schemaVersion` é `1.0.0`.
- [ ] `entry` é `null` ou ausente.
- [ ] `routes` é `[]`.
- [ ] `ui` não existe.
- [ ] `backend` existe.
- [ ] `backend.required` é `true`.
- [ ] `backend.validateJwt` está definido.
- [ ] Se `validateJwt=true`, `issuer` existe.
- [ ] Se `validateJwt=true`, `audience` existe.
- [ ] `permissions` possui ao menos uma permissão.
- [ ] `permissions[].module` é igual ao `id`.
- [ ] Existe permissão `<id>.access` quando aplicável.

---

## 19. Pontos de atenção

1. Backend-only não deve ter rotas.
2. Backend-only não deve ter UI.
3. Backend-only não deve ter entry visual.
4. Backend-only pode não aparecer no Portal.
5. O valor principal é governança, permissões e dependências.
6. Backends expostos devem validar JWT.
7. Dependências podem bloquear unregister.
8. Alterações em permissões exigem nova versão.
9. O manifesto não sobe o serviço; o serviço precisa existir na infraestrutura.
10. `basePath` deve continuar coerente com o gateway/API real.

---

## 20. Documentos relacionados

```text
docs/05-plugin-s