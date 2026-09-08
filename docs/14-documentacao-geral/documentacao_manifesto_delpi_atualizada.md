# DELPI Central — Documentação Oficial do Manifesto de Plugins

**Status:** oficial e vigente  
**Base de verdade:** schema JSON e validadores atualmente implementados  
**Substitui integralmente:** qualquer documentação anterior do manifesto que descreva versão, campos ou regras diferentes do contrato real

---

## 1. Objetivo

O manifesto de plugin é o contrato formal entre um módulo plugável e a DELPI Central.

Ele define, de maneira declarativa:

- a identidade do plugin;
- sua versão e tipo de integração;
- as permissões que o módulo declara;
- as rotas que podem ser registradas na plataforma;
- a configuração opcional de backend;
- metadados auxiliares de UI, observabilidade, segurança e ciclo de vida.

Esse manifesto é consumido pelo pipeline de validação da Core API antes do registro do plugin.

---

## 2. Princípio fundamental desta documentação

Esta documentação foi reconstruída a partir dos arquivos reais do sistema e não de documentação histórica.

Portanto, o contrato oficial do manifesto é o que está implementado em:

- `delpi.manifest.schema.json`
- `manifest_normalizer.py`
- `manifest_version_resolver.py`
- `manifest_validator.py`
- `backend_only_strategy.py`
- `iframe_strategy.py`
- `microfrontend_strategy.py`

Qualquer documento antigo que descreva `schemaVersion` diferente, campos obrigatórios divergentes, objetos de UI incompatíveis ou regras não implementadas deve ser considerado obsoleto.

---

## 3. Nome do arquivo

O arquivo esperado para o manifesto continua sendo:

```json
<plugin>/delpi.manifest.json
```

---

## 4. Versão oficial do contrato

A versão atualmente suportada pelo sistema é:

```json
"schemaVersion": "1.0.0"
```

Essa é a única versão aceita pelo resolver atual.

### Observação crítica

Documentações antigas que falam em `2.0.0` não representam mais o contrato real vigente do sistema atual.

---

## 5. Pipeline real de validação

A validação do manifesto ocorre em etapas bem definidas.

### 5.1 Normalização automática

Antes de validar schema e regras de negócio, o manifesto passa por uma normalização automática.

Hoje essa normalização faz, no mínimo:

- converte `id` para string, aplica `trim`, e força lowercase;
- se `routes` vier `null`, converte para lista vazia;
- se `permissions` vier `null`, converte para lista vazia;
- aplica `trim` em `entry` global;
- aplica `trim` em `routes[].entry`;
- aplica `trim` em `backend.issuer` e `backend.audience`.

Isso significa que parte da consistência do manifesto é garantida antes mesmo da validação estrutural.

### 5.2 Resolução de versão

Após a normalização, o sistema valida a versão do contrato.

Se `schemaVersion` não for suportado, o manifesto é rejeitado.

### 5.3 Validação por JSON Schema

Em seguida, o manifesto é validado pelo `Draft202012Validator` com base no schema oficial.

Essa etapa garante:

- campos obrigatórios;
- tipos corretos;
- restrições de pattern;
- `additionalProperties: false` nas estruturas fechadas;
- diferenciação estrutural por tipo de plugin.

### 5.4 Strategy por tipo

Depois do schema, o sistema aplica uma estratégia específica conforme `type`:

- `backend-only`
- `microfrontend`
- `iframe`

Essa camada cobre regras condicionais que seriam mais difíceis ou menos legíveis apenas no schema.

### 5.5 Regras de domínio

Por fim, o manifesto ainda passa por regras de domínio (`validate_manifest_rules`), responsáveis por validações semânticas da plataforma, como colisões, coerência de registro e outras regras de governança.

---

## 6. Estrutura oficial do manifesto

A estrutura abaixo representa o contrato atual suportado.

```json
{
  "schemaVersion": "1.0.0",
  "id": "crm",
  "name": "CRM DELPI",
  "description": "Sistema de gestão comercial",
  "category": "comercial",
  "version": "1.2.0",
  "icon": "chart-line",
  "type": "microfrontend",
  "basePath": "/crm",
  "entry": "/apps/crm/remoteEntry.js",
  "healthcheck": "/apps/crm/health",
  "dependencies": ["shared-components"],
  "permissions": [
    {
      "code": "crm.access",
      "name": "Acessar CRM",
      "description": "Permite acessar o módulo CRM",
      "module": "crm"
    }
  ],
  "routes": [
    {
      "path": "/crm",
      "label": "Dashboard",
      "icon": "layout-dashboard",
      "entry": "/apps/crm/remoteEntry.js",
      "permission": "crm.access",
      "showInMenu": true,
      "order": 1,
      "menuGroup": "Comercial"
    }
  ],
  "backend": {
    "required": true,
    "serviceName": "crm-api",
    "baseUrl": "/apps/crm/api",
    "validateJwt": true,
    "audience": "delpi-central",
    "issuer": "https://central.delpi.com.br/auth",
    "requiredPermissionsHeader": "x-user-permissions"
  },
  "features": {},
  "lifecycle": {},
  "security": {},
  "observability": {},
  "ui": {
    "renderMode": "federated"
  },
  "metadata": {}
}
```

---

## 7. Campos obrigatórios no contrato atual

Os campos obrigatórios de nível raiz são:

- `schemaVersion`
- `id`
- `name`
- `version`
- `type`
- `basePath`
- `permissions`

### Atenção importante

No contrato atual, `routes` **não é obrigatório no nível raiz para todos os tipos**.

A obrigatoriedade de `routes` depende do tipo de plugin:

- para `microfrontend`: obrigatório e deve ter ao menos 1 item;
- para `iframe`: obrigatório e deve ter ao menos 1 item;
- para `backend-only`: deve existir como array vazio ou ser normalizado para array vazio, sem itens.

Portanto, qualquer documentação que diga que `routes` é universalmente obrigatório sem considerar o tipo está tecnicamente imprecisa.

---

## 8. Regras gerais de cada campo

### 8.1 `schemaVersion`

- tipo: `string`
- valor aceito: `"1.0.0"`

### 8.2 `id`

- tipo: `string`
- tamanho: 1 a 50
- pattern: `^[a-z0-9-]+$`
- o normalizador ainda aplica lowercase e trim automaticamente

#### Recomendação

Use IDs curtos, estáveis e sem espaços, por exemplo:

- `crm`
- `dashboard-lmps`
- `gpt-api`

### 8.3 `name`

- tipo: `string`
- tamanho: 1 a 150

### 8.4 `description`

- tipo: `string`
- opcional

### 8.5 `category`

- tipo: `string`
- opcional

### 8.6 `version`

- tipo: `string`
- deve seguir SemVer compatível com o pattern atual:

```regex
^(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?$
```

Exemplos válidos:

- `1.0.0`
- `2.1.3`
- `1.0.0-beta`

### 8.7 `icon`

- tipo: `string`
- opcional

### 8.8 `type`

- enum suportado:
  - `microfrontend`
  - `iframe`
  - `backend-only`

### 8.9 `basePath`

- tipo: `string`
- pattern: `^/[-a-z0-9/]*$`

Exemplos válidos:

- `/crm`
- `/dashboard-lmps`
- `/apps/gpt`

### 8.10 `entry`

- tipo: `string | null`
- semântica depende do tipo do plugin
- pode ser global ou sobrescrito por `routes[].entry`

### 8.11 `healthcheck`

- tipo: `string`
- opcional

### 8.12 `dependencies`

- tipo: `array[string]`
- opcional

### 8.13 `permissions`

- tipo: `array`
- obrigatório
- mínimo: 1 item

Cada item de permissão exige:

- `code` — obrigatório
- `name` — obrigatório
- `module` — obrigatório

Campos opcionais por permissão:

- `description`

#### Estrutura oficial de uma permissão

```json
{
  "code": "crm.leads.read",
  "name": "Visualizar leads",
  "description": "Permite visualizar leads",
  "module": "crm"
}
```

### 8.14 `routes`

- tipo: `array`
- obrigatoriedade condicional por tipo

Cada rota exige:

- `path`
- `label`
- `permission`

Campos opcionais da rota:

- `icon`
- `entry`
- `showInMenu`
- `order`
- `menuGroup`

#### Estrutura oficial de rota

```json
{
  "path": "/crm/leads",
  "label": "Leads",
  "permission": "crm.leads.read",
  "icon": "users",
  "entry": "/apps/crm/remoteEntry.js",
  "showInMenu": true,
  "order": 2,
  "menuGroup": "Comercial"
}
```

### 8.15 `backend`

- tipo: `object`
- `additionalProperties: false`
- obrigatório para `backend-only`
- opcional para os demais tipos

Campos internos suportados:

- `required` — obrigatório quando `backend` existir
- `validateJwt` — obrigatório quando `backend` existir
- `serviceName`
- `baseUrl`
- `audience`
- `issuer`
- `requiredPermissionsHeader`

### 8.16 `features`

- tipo: `object`
- aberto
- opcional

### 8.17 `lifecycle`

- tipo: `object`
- aberto
- opcional

### 8.18 `security`

- tipo: `object`
- aberto
- opcional

### 8.19 `observability`

- tipo: `object`
- aberto
- opcional

### 8.20 `ui`

- tipo: `object`
- fechado (`additionalProperties: false`)
- atualmente suporta apenas:

```json
{
  "renderMode": "embedded | external | federated"
}
```

### 8.21 `metadata`

- tipo: `object`
- aberto
- opcional

---

## 9. Regras por tipo de plugin

## 9.1 Microfrontend

Um plugin `microfrontend` representa um módulo carregado no shell principal por integração de frontend.

### Regras estruturais

- `type` deve ser `microfrontend`
- `entry` deve existir no schema
- `routes` deve ter ao menos 1 item

### Regras adicionais da strategy

Mesmo após o schema, a strategy reforça a semântica de entrada:

- `routes` são obrigatórias;
- deve existir `entry` global **ou** cada rota precisa definir `routes[].entry`.

### `ui.renderMode` permitido

Para `microfrontend`, o schema permite apenas:

- `embedded`
- `federated`

### Exemplo válido

```json
{
  "schemaVersion": "1.0.0",
  "id": "crm",
  "name": "CRM DELPI",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/crm",
  "entry": "/apps/crm/remoteEntry.js",
  "permissions": [
    {
      "code": "crm.access",
      "name": "Acessar CRM",
      "module": "crm"
    }
  ],
  "routes": [
    {
      "path": "/crm",
      "label": "CRM",
      "permission": "crm.access"
    }
  ],
  "ui": {
    "renderMode": "federated"
  }
}
```

---

## 9.2 Iframe

Um plugin `iframe` representa um módulo externo embutido ou aberto externamente.

### Regras estruturais

- `type` deve ser `iframe`
- `entry` deve existir no schema
- `routes` deve ter ao menos 1 item

### Regras adicionais da strategy

A strategy de iframe valida:

- `routes` obrigatórias;
- `entry` global, quando informado, deve começar com `http://` ou `https://`;
- se não existir `entry` global, então cada `routes[].entry` precisa existir;
- cada `routes[].entry`, quando usado, também deve começar com `http://` ou `https://`.

### `ui.renderMode` permitido

Para `iframe`, o schema permite apenas:

- `embedded`
- `external`

### Exemplo válido

```json
{
  "schemaVersion": "1.0.0",
  "id": "bi-externo",
  "name": "BI Externo",
  "version": "1.0.0",
  "type": "iframe",
  "basePath": "/bi",
  "entry": "https://bi.delpi.com.br/dashboard",
  "permissions": [
    {
      "code": "bi.access",
      "name": "Acessar BI",
      "module": "bi"
    }
  ],
  "routes": [
    {
      "path": "/bi",
      "label": "BI",
      "permission": "bi.access"
    }
  ],
  "ui": {
    "renderMode": "embedded"
  }
}
```

---

## 9.3 Backend-only

Um plugin `backend-only` representa um módulo sem UI, utilizado apenas como API ou integração de backend governada pela central.

### Regras estruturais

- `type` deve ser `backend-only`
- `entry` deve ser `null`
- `routes` deve ser array vazio
- `backend` é obrigatório

### Regras adicionais da strategy

A strategy atual exige:

- `backend.required` deve ser `true`;
- se `backend.validateJwt` for `true`, então `backend.issuer` é obrigatório;
- se `backend.validateJwt` for `true`, então `backend.audience` é obrigatório.

### Regra adicional de schema

Para `backend-only`, `ui` não é permitida.

### Exemplo válido

```json
{
  "schemaVersion": "1.0.0",
  "id": "gpt-api",
  "name": "GPT API",
  "version": "1.0.0",
  "type": "backend-only",
  "basePath": "/apps/gpt",
  "entry": null,
  "permissions": [
    {
      "code": "gpt.access",
      "name": "Acessar GPT API",
      "module": "gpt"
    }
  ],
  "routes": [],
  "backend": {
    "required": true,
    "validateJwt": true,
    "serviceName": "gpt-api",
    "baseUrl": "/apps/gpt",
    "issuer": "https://central.delpi.com.br/auth",
    "audience": "delpi-central"
  }
}
```

---

## 10. Objeto `ui` no contrato atual

Uma das mudanças mais importantes em relação a documentações antigas está no objeto `ui`.

### Hoje, `ui` suporta apenas:

```json
{
  "renderMode": "embedded | external | federated"
}
```

### Isso significa que não fazem parte do contrato atual campos como:

- `displayInAppLauncher`
- `launcherOrder`
- `badge`

Se esses campos forem enviados dentro de `ui`, o manifesto falha no schema, porque `ui` é um objeto fechado.

---

## 11. Objeto `permissions` no contrato atual

Outra divergência importante da documentação antiga está na estrutura das permissões.

### Hoje, cada permissão exige:

- `code`
- `name`
- `module`

### `description` é opcional

Portanto, um manifesto que declare apenas `code`, `description` e `module`, sem `name`, está inválido no contrato atual.

---

## 12. Objeto `routes` no contrato atual

As rotas não incluem campos arbitrários. Elas são estruturas fechadas.

Campos aceitos por rota:

- `path`
- `label`
- `icon`
- `entry`
- `permission`
- `showInMenu`
- `order`
- `menuGroup`

Qualquer outro campo dentro de uma rota deve ser considerado inválido.

---

## 13. Objeto `backend` no contrato atual

O objeto `backend` também é fechado.

Campos aceitos:

- `required`
- `serviceName`
- `baseUrl`
- `validateJwt`
- `audience`
- `issuer`
- `requiredPermissionsHeader`

Qualquer propriedade extra deve ser rejeitada pelo schema.

---

## 14. Regras de coerência arquitetural

Além do schema e das strategies, o manifesto está inserido em uma arquitetura maior da DELPI Central.

Na prática, ele suporta um fluxo como este:

1. o plugin é publicado;
2. o manifesto é enviado para a Core API;
3. a Core valida versão, schema, strategy e regras de domínio;
4. o sistema registra aplicação, permissões, rotas e manifesto;
5. a resolução dinâmica de apps e rotas passa a considerar esse módulo;
6. o portal monta menu e acesso conforme RBAC.

Essa lógica faz sentido dentro do ecossistema descrito pela plataforma, em que existem entidades como:

- `apps`
- `app_routes`
- `permissions`
- `audit_logs`
- `app_manifests`

E endpoints centrais como:

- `GET /core-api/me`
- `GET /core-api/me/apps`
- `GET /core-api/me/routes`
- `POST /core-api/plugins/register`

---

## 15. O que a documentação antiga não deve mais afirmar

A partir do estado atual do código, **não deve mais constar como regra oficial** nenhuma afirmação como:

### 15.1 `schemaVersion: "2.0.0"`

Incorreto para o contrato atual.

### 15.2 `routes` sempre obrigatórias no manifesto inteiro

Incorreto sem qualificação por tipo.

### 15.3 permissões com `description` no lugar de `name`

Incorreto. `name` é obrigatório.

### 15.4 `ui` com vários campos livres de launcher

Incorreto. Hoje `ui` é restrito e só aceita `renderMode`.

### 15.5 backend-only com UI

Incorreto. Para `backend-only`, `ui` não é permitida.

### 15.6 iframe com `entry` sem URL absoluta

Incorreto. A strategy exige prefixo `http://` ou `https://`.

---

## 16. Boas práticas recomendadas

Mesmo quando o schema não obriga tudo semanticamente, estas práticas devem ser adotadas:

### Identidade

- mantenha `id` estável ao longo da vida do plugin;
- use o mesmo identificador em permissões e agrupamentos de módulo.

### Permissões

- use `module` igual ao domínio principal do plugin;
- adote códigos de permissão consistentes, como:
  - `crm.access`
  - `crm.leads.read`
  - `crm.leads.write`

### Rotas

- mantenha `path` coerente com `basePath`;
- use `showInMenu`, `order` e `menuGroup` para governar navegação sem duplicidade de lógica no portal.

### Backend

- quando `validateJwt=true`, sempre informe `issuer` e `audience` explicitamente;
- use `requiredPermissionsHeader` somente quando o backend realmente consumir esse cabeçalho.

### UI

- `microfrontend`: prefira `federated` quando houver Module Federation real;
- `iframe`: use `embedded` ou `external` conforme a experiência desejada.

---

## 17. Exemplo completo — microfrontend

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "description": "Dashboard operacional de LMPs",
  "category": "operacional",
  "version": "1.3.0",
  "icon": "bar-chart-3",
  "type": "microfrontend",
  "basePath": "/dashboard-lmps",
  "entry": "/apps/dashboard-lmps/remoteEntry.js",
  "healthcheck": "/apps/dashboard-lmps/health",
  "dependencies": [],
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "module": "dashboard-lmps"
    },
    {
      "code": "dashboard-lmps.read",
      "name": "Visualizar Dashboard LMPs",
      "module": "dashboard-lmps"
    }
  ],
  "routes": [
    {
      "path": "/dashboard-lmps",
      "label": "Dashboard LMPs",
      "permission": "dashboard-lmps.access",
      "showInMenu": true,
      "order": 10,
      "menuGroup": "Operacional"
    }
  ],
  "backend": {
    "required": false,
    "validateJwt": false,
    "serviceName": "dashboard-lmps-api",
    "baseUrl": "/apps/dashboard-lmps/api"
  },
  "ui": {
    "renderMode": "federated"
  },
  "metadata": {
    "owner": "Equipe DELPI"
  }
}
```

---

## 18. Exemplo completo — iframe

```json
{
  "schemaVersion": "1.0.0",
  "id": "portal-bi",
  "name": "Portal BI",
  "version": "1.0.0",
  "type": "iframe",
  "basePath": "/portal-bi",
  "entry": "https://bi.delpi.com.br/app",
  "permissions": [
    {
      "code": "portal-bi.access",
      "name": "Acessar Portal BI",
      "module": "portal-bi"
    }
  ],
  "routes": [
    {
      "path": "/portal-bi",
      "label": "Portal BI",
      "permission": "portal-bi.access",
      "showInMenu": true,
      "order": 20,
      "menuGroup": "Analytics"
    }
  ],
  "ui": {
    "renderMode": "embedded"
  }
}
```

---

## 19. Exemplo completo — backend-only

```json
{
  "schemaVersion": "1.0.0",
  "id": "totvs-sync",
  "name": "TOTVS Sync",
  "version": "1.0.0",
  "type": "backend-only",
  "basePath": "/apps/totvs-sync",
  "entry": null,
  "permissions": [
    {
      "code": "totvs-sync.execute",
      "name": "Executar sincronização TOTVS",
      "module": "totvs-sync"
    }
  ],
  "routes": [],
  "backend": {
    "required": true,
    "validateJwt": true,
    "serviceName": "totvs-sync-api",
    "baseUrl": "/apps/totvs-sync",
    "issuer": "https://central.delpi.com.br/auth",
    "audience": "delpi-central",
    "requiredPermissionsHeader": "x-user-permissions"
  },
  "metadata": {
    "owner": "Integrações"
  }
}
```

---

## 20. Checklist oficial para um manifesto válido

Antes de registrar um plugin, valide estes pontos:

### Checklist global

- `schemaVersion` está como `1.0.0`
- `id` está lowercase e compatível com o pattern
- `version` está em SemVer
- `type` é um dos três valores suportados
- `basePath` começa com `/`
- `permissions` tem ao menos um item
- cada permissão tem `code`, `name` e `module`

### Checklist de microfrontend

- existe `entry` global ou `routes[].entry`
- existe ao menos uma rota
- `ui.renderMode`, se informado, é `embedded` ou `federated`

### Checklist de iframe

- existe `entry` global ou `routes[].entry`
- toda entry usada começa com `http://` ou `https://`
- existe ao menos uma rota
- `ui.renderMode`, se informado, é `embedded` ou `external`

### Checklist de backend-only

- `entry` é `null`
- `routes` é `[]`
- `backend` existe
- `backend.required` é `true`
- se `validateJwt=true`, então `issuer` e `audience` existem
- `ui` não foi declarada

---

## 21. Conclusão

O manifesto oficial da DELPI Central precisa ser entendido como um contrato executável, não apenas documental.

A verdade do sistema hoje está no schema e nos validadores atuais. Com isso:

- a versão oficial vigente do contrato é `1.0.0`;
- os tipos suportados continuam sendo `microfrontend`, `iframe` e `backend-only`;
- a validação real combina normalização, schema, strategy e regras de domínio;
- a documentação antiga não deve mais ser usada como referência técnica.

Esta é a nova referência oficial para criação, revisão, validação e registro de manifestos de plugins na DELPI Central.

