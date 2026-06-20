# Minha DELPI — Plugin `dashboard-delpi`

> **Arquivo:** `docs/08-plugins/dashboard-delpi.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** plugin/microfrontend `dashboard-delpi`

---

## 1. Objetivo

Este documento registra o estado conhecido do plugin **`dashboard-delpi`** dentro da Minha DELPI.

A documentação abaixo considera apenas informações confirmadas nos arquivos enviados. Onde o código real do plugin não foi fornecido ou não foi analisado, o documento marca explicitamente como pendência.

---

## 2. Identidade conhecida

Identificador do plugin:

```text
dashboard-delpi
```

Container em Docker Compose:

```text
delpi-dashboard-delpi
```

Pasta esperada no repositório:

```text
plugins/dashboard-delpi
```

Serviço Docker:

```text
dashboard-delpi
```

---

## 3. Papel arquitetural

O `dashboard-delpi` é tratado na stack como um plugin/microfrontend frontend.

Ele é construído a partir de:

```yaml
build:
  context: ../plugins/dashboard-delpi
  dockerfile: Dockerfile
```

No ambiente de desenvolvimento, o Compose monta o código local:

```yaml
volumes:
  - ../plugins/dashboard-delpi:/app
  - /app/node_modules
```

Isso indica que o plugin foi preparado para execução isolada em container e desenvolvimento com dependências Node.

---

## 4. Tipo de plugin

Pelo contexto da stack e do Plugin System, o `dashboard-delpi` deve ser tratado como:

```text
microfrontend
```

Essa classificação deve ser confirmada no manifesto real do plugin.

Se o manifesto ainda não existir, ele deve seguir o contrato oficial:

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-delpi",
  "type": "microfrontend",
  "ui": {
    "renderMode": "federated"
  }
}
```

---

## 5. Exposição no Gateway

O caminho público esperado para plugins microfrontend segue o padrão:

```text
/apps/<plugin>/assets/remoteEntry.js
```

Para este plugin, o entry esperado seria:

```text
/apps/dashboard-delpi/assets/remoteEntry.js
```

Esse caminho precisa ser confirmado na configuração real do Gateway e no manifesto real do plugin.

---

## 6. Manifesto

Manifesto esperado:

```text
plugins/dashboard-delpi/delpi.manifest.json
```

ou arquivo equivalente usado no processo de registro.

Campos mínimos esperados:

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-delpi",
  "name": "Dashboard DELPI",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/apps/dashboard-delpi",
  "entry": "/apps/dashboard-delpi/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "dashboard-delpi.access",
      "name": "Acessar Dashboard DELPI",
      "module": "dashboard-delpi"
    }
  ],
  "routes": [
    {
      "path": "/apps/dashboard-delpi",
      "label": "Dashboard DELPI",
      "permission": "dashboard-delpi.access",
      "showInMenu": true,
      "order": 1
    }
  ],
  "ui": {
    "renderMode": "federated"
  }
}
```

> Esse exemplo é um modelo de referência. O manifesto real deve ser usado como fonte final quando estiver disponível.

---

## 7. Permissões

Permissão mínima esperada:

```text
dashboard-delpi.access
```

A permissão deve ser registrada pelo manifesto e associada a roles/grupos pela administração da plataforma.

Regra:

```text
Permissão no manifesto não concede acesso sozinha.
```

O acesso real depende do RBAC da Core API.

---

## 8. Rotas

Rota esperada:

```text
/apps/dashboard-delpi
```

A rota deve aparecer no menu somente se:

- o plugin estiver ativo;
- a rota estiver ativa;
- `showInMenu=true`;
- o usuário possuir a permissão associada;
- a Core API retornar o app em `/me/apps`.

---

## 9. Integração com Portal

Fluxo esperado:

```text
Usuário autentica no Portal
  ↓
Portal chama /me/apps
  ↓
Core API retorna dashboard-delpi se autorizado
  ↓
Portal monta item de menu
  ↓
Portal carrega entryUrl do plugin
```

O plugin deve exportar funções compatíveis com o host quando usar Module Federation:

```text
mount(el, props)
unmount(el)
```

---

## 10. Checklist técnico

- [ ] Confirmar existência de `delpi.manifest.json`.
- [ ] Confirmar `id=dashboard-delpi`.
- [ ] Confirmar `basePath`.
- [ ] Confirmar `entry`.
- [ ] Confirmar `routes`.
- [ ] Confirmar permissões.
- [ ] Confirmar build com Vite Federation ou estratégia equivalente.
- [ ] Confirmar que `remoteEntry.js` retorna JavaScript.
- [ ] Confirmar roteamento no Gateway.
- [ ] Confirmar carregamento via Portal.

---

## 11. Pendências

As informações abaixo ainda dependem dos arquivos reais do plugin:

- telas disponíveis;
- componentes principais;
- chamadas de API;
- estado interno;
- manifesto real;
- rotas reais;
- permissões finais;
- dashboards e KPIs exibidos;
- dependências backend.

---

## 12. Pontos de atenção

1. Não registrar manifesto sem validar schema.
2. Não hardcodar acesso no Portal.
3. Não depender de permissão somente no frontend.
4. Confirmar Gateway antes de registrar o plugin.
5. Confirmar cache do `remoteEntry.js`.
6. Confirmar se o plugin ainda é usado, pois o Gateway do Compose informado não lista `dashboard-delpi` em `depends_on`.

---

## Referências internas

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/microfrontends.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
