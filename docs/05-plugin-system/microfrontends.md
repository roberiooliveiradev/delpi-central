# Minha DELPI — Microfrontends

> **Arquivo:** `docs/05-plugin-system/microfrontends.md`  
> **Status:** documentação oficial (maio/2026)  

**Nota:** o plugin LMPs em produção no monorepo é **iframe** (`id` `dash-lmps`), não microfrontend. Os exemplos abaixo com `dashboard-lmps` são didáticos para MFE; use `strategic-indicators` como referência real de `remoteEntry.js`.
> **Produto:** Minha DELPI  
> **Escopo:** plugins visuais do tipo `microfrontend`

---

## 1. Objetivo

Este documento descreve como funcionam os plugins do tipo **microfrontend** na Minha DELPI.

Ele explica:

- o que é um microfrontend na plataforma;
- como declarar um manifesto do tipo `microfrontend`;
- como o Portal descobre e carrega o plugin;
- como permissões controlam visibilidade;
- como rotas são registradas;
- quais cuidados devem ser tomados em publicação, gateway e versionamento.

---

## 2. Conceito

Um **microfrontend** é um plugin visual integrado ao Portal da Minha DELPI.

Ele representa uma aplicação frontend independente, publicada separadamente, mas exibida dentro da experiência principal da plataforma.

Na Minha DELPI, um microfrontend é descoberto por manifesto e carregado pelo Portal conforme:

- app ativo;
- rotas registradas;
- permissões do usuário;
- `entryUrl`;
- `renderMode`;
- configuração do gateway.

---

## 3. Diferença entre Portal e microfrontend

O Portal é o shell principal da plataforma.

O microfrontend é um módulo funcional carregado pelo Portal.

| Responsabilidade | Portal | Microfrontend |
|---|---:|---:|
| Login com Keycloak | Sim | Não deve iniciar login próprio |
| Layout principal | Sim | Não |
| Sidebar/menu global | Sim | Não |
| Carregamento de apps | Sim | Não |
| Tela funcional do módulo | Não | Sim |
| Regras de negócio do módulo | Não | Sim, quando frontend |
| Consumo de APIs do módulo | Parcial | Sim |
| Controle global de permissões | Não | Não |

Regra:

> Microfrontends devem ser módulos funcionais. A governança global continua no Portal e na Core API.

---

## 4. Tipo no manifesto

Para declarar um microfrontend, usar:

```json
{
  "type": "microfrontend"
}
```

O manifesto deve seguir `schemaVersion: "1.0.0"`.

---

## 5. Render modes suportados

Para `microfrontend`, os valores aceitos de `ui.renderMode` são:

```text
embedded
federated
```

| Render mode | Uso esperado |
|---|---|
| `embedded` | Carregamento integrado simples pelo Portal |
| `federated` | Carregamento via remote/module federation ou mecanismo equivalente |

Exemplo:

```json
{
  "ui": {
    "renderMode": "federated"
  }
}
```

Se `renderMode` não for informado, a Core API tende a usar `embedded` como padrão ao montar a visão do app.

---

## 6. Entry point

Microfrontends precisam declarar `entry` global no contrato efetivo atual.

Exemplo:

```json
{
  "entry": "/apps/dashboard-lmps/assets/remoteEntry.js"
}
```

O `entry` deve apontar para o recurso publicado do plugin.

Esse recurso deve estar acessível pelo navegador do usuário através do Gateway.

---

## 7. Rotas

Microfrontends devem declarar pelo menos uma rota.

Exemplo:

```json
{
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "icon": "bar-chart3",
      "permission": "dashboard-lmps.access",
      "showInMenu": true,
      "order": 1
    }
  ]
}
```

Regras:

- `routes` é obrigatório;
- deve conter ao menos uma rota;
- cada `path` deve iniciar com `basePath`;
- rotas não podem ser duplicadas;
- `permission` da rota precisa existir em `permissions[].code`;
- `showInMenu` controla se a rota aparece no menu.

---

## 8. Permissões

Microfrontends devem declarar permissões no manifesto.

Exemplo:

```json
{
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "description": "Permite acessar o dashboard de LMPs.",
      "module": "dashboard-lmps"
    }
  ]
}
```

Regra:

```text
permissions[].module = manifest.id
```

Permissões declaradas são criadas na tabela `permissions` durante o registro do plugin.

Depois, administradores podem associá-las a roles e grupos.

---

## 9. Como o Portal descobre microfrontends

O Portal não possui uma lista fixa definitiva de microfrontends.

Fluxo:

```text
Portal autentica usuário
  ↓
Portal chama /me/apps
  ↓
Core API lista apps ativos
  ↓
Core API carrega rotas e manifesto
  ↓
Core API filtra por permissões
  ↓
Portal recebe apps autorizados
  ↓
Portal monta menu e rotas
```

O Portal recebe dados como:

```json
{
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "basePath": "/apps/dashboard-lmps",
  "icon": "bar-chart3",
  "type": "microfrontend",
  "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "renderMode": "federated",
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "permission": "dashboard-lmps.access",
      "label": "Dashboard LMPs",
      "showInMenu": true,
      "order": 1,
      "entry": null
    }
  ]
}
```

---

## 10. Autorização

A autorização de microfrontends é feita pela Core API.

Regra:

- superadmin recebe todos os apps;
- usuário comum recebe apenas rotas sem permissão ou rotas cuja permissão esteja em suas permissões efetivas;
- app sem rota autorizada não é retornado para o usuário.

Portanto, um microfrontend aparece no Portal apenas se o usuário puder acessar pelo menos uma rota dele.

---

## 11. Relação entre rota e menu

Cada rota pode controlar sua exibição no menu por:

```json
{
  "showInMenu": true,
  "order": 1
}
```

Campos usados pelo Portal:

| Campo | Uso |
|---|---|
| `label` | Texto exibido no menu |
| `icon` | Ícone visual |
| `showInMenu` | Se aparece no menu |
| `order` | Ordenação |
| `path` | Caminho de navegação |
| `permission` | Controle de acesso |

Uma rota pode existir e não aparecer no menu se:

```json
{
  "showInMenu": false
}
```

---

## 12. Publicação via Gateway

O microfrontend precisa estar acessível pelo Gateway.

Exemplo:

```text
/apps/dashboard-lmps
/apps/dashboard-lmps/assets/remoteEntry.js
```

A configuração do Gateway deve encaminhar esse path para o container do plugin correspondente.

Exemplo conceitual:

```text
/apps/dashboard-lmps/* → delpi-dashboard-lmps
```

A configuração exata deve ser documentada em:

```text
docs/02-infraestrutura/gateway-nginx.md
```

---

## 13. Serviços atuais de microfrontend

A stack atual possui serviços de plugins visuais como:

```text
strategic-indicators
dashboard-lmps
```

Cada um possui build próprio e é publicado como serviço separado no Docker Compose.

---

## 14. Estrutura esperada de um microfrontend

Estrutura típica:

```text
plugins/
  dashboard-lmps/
    Dockerfile
    package.json
    src/
    public/
    vite.config.*
    manifest.json
```

O nome e conteúdo exato podem variar por plugin, mas cada plugin deve possuir:

- build próprio;
- Dockerfile;
- entry publicado;
- manifesto correspondente;
- integração com APIs necessárias;
- compatibilidade com o path definido em `basePath`.

---

## 15. Exemplo completo de manifesto microfrontend

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "description": "Painel de acompanhamento de LMPs.",
  "category": "Dashboards",
  "version": "1.0.0",
  "icon": "bar-chart3",
  "type": "microfrontend",
  "basePath": "/apps/dashboard-lmps",
  "entry": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "dashboard-lmps.access",
      "name": "Acessar Dashboard LMPs",
      "description": "Permite acessar o dashboard de LMPs.",
      "module": "dashboard-lmps"
    }
  ],
  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "icon": "bar-chart3",
      "permission": "dashboard-lmps.access",
      "showInMenu": true,
      "order": 1,
      "menuGroup": "Dashboards"
    }
  ],
  "ui": {
    "renderMode": "federated"
  },
  "metadata": {
    "owner": "DELPI",
    "area": "Operações"
  }
}
```

---

## 16. Registro do microfrontend

O registro é feito pela Core API:

```http
POST /admin/apps/register
```

Com permissão:

```text
apps.manage
```

Fluxo:

```text
Manifesto enviado
  ↓
Validação
  ↓
Criação/atualização de app
  ↓
Criação de permissões
  ↓
Criação de rotas
  ↓
Persistência de versão
  ↓
Evento plugin_registered
```

---

## 17. Atualização de microfrontend

Existem dois tipos de atualização.

### 17.1 Atualização não estrutural

Usar:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Para alterar:

- nome;
- descrição;
- ícone;
- label de rota;
- ícone de rota;
- ordem;
- `showInMenu`.

---

### 17.2 Atualização estrutural

Usar:

```http
POST /admin/apps/register
```

Com nova versão.

Para alterar:

- rotas;
- permissões;
- basePath;
- type;
- entry estrutural;
- contrato funcional do plugin.

---

## 18. Rollback de microfrontend

Rollback restaura uma versão anterior registrada.

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

Efeitos:

- restaura `apps.version`;
- restaura `app_manifests`;
- remove e recria permissões;
- remove e recria rotas;
- emite evento `plugin_version_rolled_back`.

Atenção:

> O rollback restaura o contrato registrado, mas os assets antigos do microfrontend precisam continuar disponíveis ou compatíveis com o path/entry restaurado.

---

## 19. Boas práticas para microfrontends

1. Manter `id` estável.
2. Usar `basePath` único sob `/apps/<id>`.
3. Declarar ao menos uma permissão de acesso.
4. Declarar rotas com paths dentro de `basePath`.
5. Manter `entry` acessível pelo Gateway.
6. Não acoplar login próprio no microfrontend.
7. Receber contexto/autenticação do Portal quando possível.
8. Consumir APIs protegidas com token do usuário.
9. Evitar duplicar lógica global de RBAC no frontend.
10. Versionar mudanças estruturais.

---

## 20. Cuidados com assets

Microfrontends publicados devem garantir:

- assets acessíveis pelo path esperado;
- caminhos compatíveis com `basePath`;
- build reproduzível;
- cache compatível com versionamento;
- ausência de dependência de path local de desenvolvimento;
- compatibilidade com gateway.

Problemas comuns:

```text
remoteEntry.js inacessível
assets apontando para /
basePath diferente do path no gateway
CORS ou headers incorretos
build gerado para path errado
```

---

## 21. Integração com APIs

Microfrontends podem consumir:

- Core API;
- API DELPI;
- APIs próprias;
- endpoints externos autorizados.

Regra recomendada:

> APIs de governança devem ser acessadas pela Core API. Dados operacionais devem ser acessados pela API DELPI ou API específica do domínio.

---

## 22. Segurança

Microfrontends não devem assumir que o simples fato de estarem carregados garante autorização final para todas as ações.

Regras:

- frontend controla experiência;
- backend deve validar token;
- backend deve validar permissões quando necessário;
- rotas sensíveis não devem confiar apenas em ocultação de menu;
- permissões devem ser aplicadas no backend correspondente.

---

## 23. Checklist para publicar microfrontend

- [ ] Plugin possui Dockerfile.
- [ ] Build gera assets acessíveis.
- [ ] Gateway roteia `basePath` corretamente.
- [ ] `entry` existe e é acessível pelo navegador.
- [ ] Manifesto usa `type: microfrontend`.
- [ ] `ui.renderMode` é `embedded` ou `federated`.
- [ ] `permissions` está coerente.
- [ ] Rotas começam com `basePath`.
- [ ] Usuários/roles receberam permissões necessárias.
- [ ] `/me/apps` retorna o plugin para usuários autorizados.
- [ ] Portal carrega o plugin sem erro.

---

## 24. Pontos de atenção

1. Microfrontend precisa estar registrado e publicado.
2. Registro na Core API não garante que assets existem no gateway.
3. Gateway precisa rotear o path do plugin.
4. Usuário só vê rotas autorizadas.
5. App sem rota autorizada não aparece.
6. Superadmin vê todos os apps ativos.
7. Alterações estruturais exigem nova versão.
8. Rollback exige que assets antigos ainda sejam compatíveis.
9. Não duplicar autenticação dentro do microfrontend.
10. Backends consumidos pelo microfrontend devem validar JWT.

---

## 25. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/02-infraestrutura/gateway-nginx.md
docs/03-autenticacao-autorizacao/rbac.md
```

