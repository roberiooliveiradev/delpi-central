# Minha DELPI — Visão Geral da API DELPI

> **Arquivo:** `docs/07-api-delpi/visao-geral-api-delpi.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** visão técnica e arquitetural da API DELPI

---

## 1. Objetivo

Este documento descreve o papel da **API DELPI** dentro da arquitetura da Minha DELPI.

A API DELPI é o backend operacional da plataforma. Ela é separada da Core API e deve ser usada para integrações, consultas de negócio, dados operacionais e módulos de domínio.

Este documento apresenta a visão geral. A documentação detalhada de rotas e módulos da API DELPI deve ser escrita após análise dos arquivos reais desse serviço.

---

## 2. Papel da API DELPI

A API DELPI atende responsabilidades de negócio e integração.

Responsabilidades típicas:

- consultar bases operacionais;
- integrar com TOTVS;
- expor rotas de domínio;
- atender plugins e microfrontends;
- persistir dados de módulos no banco de plugins quando aplicável;
- concentrar regras operacionais que não pertencem à governança central da plataforma.

A API DELPI não é responsável por governar usuários, roles, permissões, apps, rotas ou manifestos da plataforma.

Essa governança pertence à Core API.

---

## 3. Separação entre Core API e API DELPI

A separação é uma decisão arquitetural fundamental.

```text
Core API  → governança da plataforma
API DELPI → dados e regras operacionais de negócio
```

| Responsabilidade | Core API | API DELPI |
|---|---:|---:|
| Validar JWT | Sim | Sim, quando endpoint protegido |
| Sincronizar usuário local da plataforma | Sim | Não |
| Gerenciar RBAC | Sim | Não |
| Gerenciar apps/plugins | Sim | Não |
| Registrar manifestos | Sim | Não |
| Expor dados operacionais | Não | Sim |
| Integrar com TOTVS | Não | Sim |
| Atender plugins de domínio | Parcial, governança | Sim, dados/regras |
| Persistir dados de domínio | Não | Sim |

---

## 4. Serviço Docker

Serviço:

```text
api-delpi
```

Container:

```text
delpi-api-delpi
```

Build:

```yaml
build:
  context: ..
  dockerfile: api-delpi/Dockerfile
```

Em desenvolvimento, o código é montado como volume:

```yaml
volumes:
  - ../api-delpi:/app
```

A API DELPI fica na mesma rede Docker dos demais serviços:

```text
delpi-network
```

---

## 5. Dependências no Docker Compose

A API DELPI depende de:

```yaml
depends_on:
  - keycloak
  - postgres-plugins
```

Isso indica que a API DELPI:

- usa Keycloak/JWT para autenticação/autorização de endpoints protegidos;
- usa `postgres-plugins` para persistência de módulos/plugins/domínios.

Também possui variáveis para conexão com TOTVS e Portal RH.

---

## 6. Banco de plugins

A API DELPI se conecta ao banco:

```text
postgres-plugins
```

Variáveis:

```env
PLUGINS_DB_HOST=
PLUGINS_DB_PORT=
PLUGINS_DB_NAME=
PLUGINS_DB_USER=
PLUGINS_DB_PASSWORD=
PLUGINS_DB_CONNECT_TIMEOUT=
PLUGINS_DB_SSLMODE=
```

Uso esperado:

- dados de módulos de domínio;
- persistência de plugins operacionais;
- tabelas que não pertencem à governança da Core API;
- cache/materialização de dados operacionais quando necessário.

Regra:

> Dados de governança da plataforma ficam no `postgres-core`. Dados de domínio/plugin ficam no `postgres-plugins` ou em datasource próprio.

---

## 7. Integração com TOTVS

A API DELPI possui variáveis específicas para conexão com TOTVS:

```env
TOTVS_DB_HOST=
TOTVS_DB_PORT=
TOTVS_DB_USER=
TOTVS_DB_PASSWORD=
TOTVS_DB_DATABASE=
```

No container, essas variáveis são mapeadas para os nomes esperados pelo código:

```yaml
DB_HOST: ${TOTVS_DB_HOST}
DB_PORT: ${TOTVS_DB_PORT}
DB_USER: ${TOTVS_DB_USER}
DB_PASSWORD: ${TOTVS_DB_PASSWORD}
DB_DATABASE: ${TOTVS_DB_DATABASE}
```

Isso indica que o código da API DELPI espera variáveis genéricas `DB_*`, mas o Compose usa variáveis `TOTVS_DB_*` como origem.

---

## 8. Integração com Portal RH

A API DELPI também possui variáveis para conexão com banco do Portal RH:

```env
PORTAL_RH_DB_HOST=
PORTAL_RH_DB_PORT=
PORTAL_RH_DB_NAME=
PORTAL_RH_DB_USER=
PORTAL_RH_DB_PASSWORD=
PORTAL_RH_DB_CONNECT_TIMEOUT=
PORTAL_RH_DB_SSLMODE=
```

Essas variáveis indicam suporte a consultas ou integrações com domínio de RH.

A documentação detalhada deve ser criada após análise das rotas reais da API DELPI.

---

## 9. Configuração JWT

A API DELPI recebe variáveis de autenticação JWT/OIDC:

```env
KEYCLOAK_REALM=
KEYCLOAK_AUDIENCE=
KEYCLOAK_JWKS_URL=
KEYCLOAK_ISSUER=
JWT_ALGORITHMS=
JWT_SECRET=
API_DELPI_JWT_SECRET=
```

No Compose:

```yaml
JWT_SECRET: ${API_DELPI_JWT_SECRET}
KEYCLOAK_REALM: ${KEYCLOAK_REALM}
KEYCLOAK_AUDIENCE: ${KEYCLOAK_AUDIENCE}
KEYCLOAK_JWKS_URL: ${KEYCLOAK_JWKS_URL}
KEYCLOAK_ISSUER: ${KEYCLOAK_ISSUER}
JWT_ALGORITHMS: ${JWT_ALGORITHMS}
```

Responsabilidade da API DELPI:

- validar JWT em endpoints protegidos;
- verificar issuer/audience conforme configuração;
- proteger dados operacionais;
- aplicar permissões quando a rota exigir.

---

## 10. Relação com o Portal

O Portal pode consumir a API DELPI diretamente ou por meio de plugins.

Fluxo típico:

```text
Portal ou Plugin
  ↓ Authorization: Bearer <token>
Gateway
  ↓
API DELPI
  ↓
TOTVS / postgres-plugins / outro datasource
```

Exemplos de uso:

- dashboard consome dados da API DELPI;
- plugin consulta indicadores;
- módulo operacional consulta dados TOTVS;
- tela de RH consulta banco Portal RH.

---

## 11. Relação com plugins

Plugins visuais podem usar a API DELPI como backend.

Exemplo:

```text
dashboard-lmps
  ↓
/api-delpi ou /apps/api-delpi
  ↓
consulta dados de LMPs
```

Quando a API DELPI for declarada no Plugin System, ela pode ser representada como plugin `backend-only`.

Isso permite:

- registrar permissões relacionadas à API;
- declarar dependências de plugins visuais;
- impedir unregister de backend usado por plugins dependentes;
- documentar a API dentro da governança da plataforma.

---

## 12. Relação com o Gateway

O Gateway é responsável por expor a API DELPI ao navegador e aos plugins.

No Docker Compose, o gateway depende de:

```yaml
depends_on:
  - api-delpi
```

Path conceitual esperado:

```text
/apps/api-delpi
```

A configuração exata depende do Nginx.

Deve ser documentada em:

```text
docs/02-infraestrutura/gateway-nginx.md
```

---

## 13. Ambiente

Variáveis gerais da API DELPI:

```env
PORT=
ENV=
LOG_LEVEL=
TZ=
```

No Compose:

```yaml
PORT: ${API_DELPI_PORT}
ENV: ${API_DELPI_ENV}
LOG_LEVEL: ${LOG_LEVEL}
TZ: ${TZ}
```

Essas variáveis controlam porta interna, modo de execução, logging e timezone.

---

## 14. Segurança

Regras de segurança esperadas:

1. Endpoints protegidos devem validar JWT.
2. JWT deve ser validado contra issuer e audience corretos.
3. Dados operacionais não devem ser expostos sem autenticação.
4. Permissões devem ser aplicadas em endpoints sensíveis.
5. O frontend não deve ser a única barreira de segurança.
6. Tokens não devem ser enviados por query string.
7. Credenciais de banco devem vir de variáveis de ambiente.
8. Logs não devem expor senhas ou tokens.

---

## 15. Diferença entre permissão de plataforma e permissão operacional

A Core API define e resolve permissões da plataforma.

A API DELPI pode validar permissões para endpoints operacionais, mas deve usar os códigos de permissão padronizados.

Exemplo:

```text
dashboard-lmps.access
api-delpi.access
qualidade.relatorios.view
```

Cenário recomendado:

```text
Core API registra permissões via manifesto
  ↓
Administrador atribui permissões a roles/grupos
  ↓
Portal recebe apps autorizados
  ↓
Plugin chama API DELPI com token
  ↓
API DELPI valida token e permissões necessárias
```

---

## 16. O que não pertence à API DELPI

A API DELPI não deve assumir responsabilidades da Core API.

Não pertence à API DELPI:

- cadastrar usuários da plataforma;
- gerenciar roles;
- gerenciar groups;
- gerenciar permissions globais;
- registrar manifestos;
- controlar menu do Portal;
- decidir lista oficial de apps plugáveis;
- gerenciar favoritos do Portal;
- emitir eventos administrativos da plataforma.

---

## 17. O que pertence à API DELPI

Pertence à API DELPI:

- endpoints operacionais;
- consultas de dados corporativos;
- integração TOTVS;
- integração Portal RH;
- regras de domínio de módulos;
- suporte a dashboards e plugins;
- persistência em `postgres-plugins`;
- validação de acesso a recursos operacionais.

---

## 18. Organização futura da documentação

A documentação detalhada da API DELPI deve ser organizada assim:

```text
docs/07-api-delpi/
  visao-geral-api-delpi.md
  integracao-totvs.md
  banco-postgres-plugins.md
  rotas-operacionais.md
  modulos-de-dominio.md
  autenticacao-e-jwt.md
```

Esses documentos devem ser escritos com base no código real da API DELPI.

---

## 19. Checklist para documentar rotas da API DELPI

Quando os arquivos reais da API DELPI forem analisados, cada rota deve ser documentada com:

- método HTTP;
- path;
- controller/handler;
- autenticação exigida;
- permissões exigidas;
- query params;
- body;
- resposta de sucesso;
- respostas de erro;
- datasource usado;
- regra de negócio;
- consumidores conhecidos;
- exemplo de chamada.

Modelo:

```markdown
## GET /alguma-rota

### Objetivo

### Autenticação

### Permissões

### Query params

### Resposta

### Erros

### Datasource

### Observações
```

---

## 20. Pontos de atenção

1. A API DELPI é separada da Core API.
2. A API DELPI consome variáveis TOTVS mapeadas para `DB_*`.
3. A API DELPI também recebe variáveis de `postgres-plugins`.
4. O Compose indica integração com Portal RH.
5. O Gateway deve expor a API DELPI por path estável.
6. A API DELPI deve validar JWT em endpoints protegidos.
7. Permissões devem ser coerentes com o RBAC da Core API.
8. Dados de governança não devem ir para a API DELPI.
9. Dados operacionais não devem ir para a Core API.
10. A documentação de rotas depende da análise do código real da API DELPI.

---

## 21. Documentos relacionados

```text
docs/07-api-delpi/integracao-totvs.md
docs/07-api-delpi/banco-postgres-plugins.md
docs/07-api-delpi/rotas-operacionais.md
docs/07-api-delpi/modulos-de-dominio.md
docs/05-plugin-system/backend-only.md
docs/05-plugin-system/microfrontends.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/02-infraestrutura/docker-compose.md
```

