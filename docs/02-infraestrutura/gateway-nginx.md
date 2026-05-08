# Minha DELPI — Gateway Nginx

> **Arquivo:** `docs/02-infraestrutura/gateway-nginx.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** papel do Gateway, roteamento por path, integração com Docker Compose e pontos de configuração do Nginx

---

## 1. Objetivo

Este documento descreve o papel do **Gateway Nginx** na Minha DELPI.

O Gateway é o ponto único de entrada HTTP da plataforma. Ele recebe as requisições do navegador e encaminha para os serviços internos corretos, como Portal, Core API, Keycloak, API DELPI e plugins.

---

## 2. Papel do Gateway

O Gateway centraliza a entrada da aplicação.

Responsabilidades:

- expor a plataforma na porta HTTP pública;
- rotear o Portal;
- rotear a Core API;
- rotear o Keycloak;
- rotear a API DELPI;
- rotear plugins/microfrontends;
- manter nomes internos dos containers fora do navegador;
- padronizar headers e proxy;
- permitir evolução para HTTPS, rate limit e headers de segurança.

---

## 3. Serviço Docker

Serviço:

```text
gateway
```

Container:

```text
delpi-gateway
```

Porta exposta:

```yaml
ports:
  - "80:80"
```

O Gateway participa da rede:

```text
delpi-network
```

---

## 4. Build em desenvolvimento e produção

Desenvolvimento:

```yaml
build:
  context: ../gateway
  dockerfile: Dockerfile.dev
```

Produção:

```yaml
build:
  context: ../gateway
  dockerfile: Dockerfile.prod
```

Em desenvolvimento, o Compose monta explicitamente:

```yaml
volumes:
  - ../gateway/nginx.dev.conf:/etc/nginx/nginx.conf
```

Em produção, a configuração deve estar embutida na imagem construída por `gateway/Dockerfile.prod`.

---

## 5. Dependências do Gateway

O Gateway depende dos serviços que ele precisa rotear.

No Compose atual, dependências principais:

```text
portal
core-api
keycloak
api-delpi
strategic-indicators
dashboard-lmps
```

Observação:

> `dashboard-delpi` existe como serviço, mas não aparece no `depends_on` do Gateway nos Compose fornecidos. Confirmar se ainda existe rota ativa para esse plugin no Nginx ou se ele está legado/inativo.

---

## 6. Roteamento conceitual

A fundação inicial da plataforma estabeleceu o Gateway como entrada única com roteamento conceitual:

```text
/             → Portal
/core-api/*   → Core API
/auth/*       → Keycloak
```

Com a evolução atual, a stack também inclui:

```text
/apps/api-delpi      → API DELPI
/apps/<plugin-id>    → plugins/microfrontends
```

A configuração exata precisa ser validada no arquivo real:

```text
gateway/nginx.dev.conf
gateway/nginx.conf ou equivalente de produção
```

Ponto de atenção:

> O arquivo real de configuração Nginx não está entre os arquivos disponíveis nesta etapa. Este documento descreve o contrato esperado com base no Compose e na arquitetura registrada.

---

## 7. Portal

O Portal é o frontend principal da plataforma.

Rota conceitual:

```text
/ → portal
```

Responsabilidade do Gateway:

- entregar a aplicação React/Vite;
- permitir refresh em rotas frontend;
- encaminhar assets do Portal;
- preservar headers necessários.

Ponto de atenção:

> Para aplicações SPA, o Nginx deve tratar fallback para `index.html` quando a rota pertence ao Portal e não corresponde a um arquivo estático real.

---

## 8. Core API

A Core API é o backend de governança.

Rota conceitual:

```text
/core-api/* → core-api
```

Endpoints expostos por trás desse path incluem:

```text
/core-api/health
/core-api/me
/core-api/me/apps
/core-api/admin/apps
/core-api/admin/rbac
```

Dependendo da configuração Flask/Blueprints, o prefixo `/core-api` pode ser tratado no Gateway, na aplicação ou em ambos. A regra deve ser validada contra o `nginx.conf` real.

---

## 9. Keycloak

O Keycloak é o provedor de identidade.

Rota conceitual:

```text
/auth/* → keycloak
```

O Compose define variáveis de Keycloak relacionadas a path e hostname:

```env
KC_HTTP_RELATIVE_PATH=
KC_HOSTNAME=
KC_PROXY=
KC_PROXY_HEADERS=
```

O serviço `keycloak` recebe alias de rede:

```yaml
aliases:
  - keycloak
```

Esse alias permite que o Gateway resolva o upstream `keycloak` de forma estável dentro da rede Docker.

---

## 10. API DELPI

A API DELPI é o backend operacional.

Base esperada:

```text
/apps/api-delpi
```

Responsabilidades do Gateway:

- rotear chamadas operacionais para o container `api-delpi`;
- preservar headers de autenticação;
- não expor diretamente o host/porta interno da API;
- permitir que plugins e Portal consumam a API por path estável.

---

## 11. Plugins e microfrontends

Plugins atuais na stack:

```text
dashboard-delpi
strategic-indicators
dashboard-lmps
```

Bases conceituais esperadas:

```text
/apps/dashboard-delpi
/apps/strategic-indicators
/apps/dashboard-lmps
```

O manifesto de plugin e a Core API usam `basePath`, `entry` e `routes` para indicar ao Portal como carregar o app. O Gateway precisa servir esses paths para que o Portal consiga carregar os assets.

Exemplo conceitual:

```text
/apps/dashboard-lmps/assets/remoteEntry.js → dashboard-lmps
```

---

## 12. Headers importantes

O Gateway deve preservar headers relevantes.

Headers importantes para backends:

```text
Host
X-Real-IP
X-Forwarded-For
X-Forwarded-Proto
Authorization
```

Especialmente:

```text
Authorization: Bearer <token>
```

Esse header precisa chegar à Core API e à API DELPI para validação JWT.

---

## 13. WebSocket e Socket.IO

A Core API usa Socket.IO para eventos administrativos.

Se o Socket.IO trafegar pelo Gateway, a configuração Nginx deve suportar upgrade de conexão.

Headers típicos:

```nginx
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

Ponto de atenção:

> Confirmar no arquivo real do Nginx qual path/namespace Socket.IO está sendo usado e se o Gateway já possui suporte a WebSocket.

---

## 14. Segurança no Gateway

O Gateway é o local recomendado para aplicar controles transversais.

Controles esperados em produção:

- HTTPS;
- redirect HTTP → HTTPS;
- headers de segurança;
- limite de tamanho de request;
- rate limit;
- CORS restritivo quando aplicável;
- timeout adequado por upstream;
- logs de acesso;
- bloqueio de paths internos;
- proteção para endpoints administrativos, quando aplicável por rede.

Headers úteis:

```text
Strict-Transport-Security
X-Content-Type-Options
Referrer-Policy
Content-Security-Policy
X-Frame-Options
```

A aplicação usa plugins `iframe`, então `X-Frame-Options` e `Content-Security-Policy frame-ancestors` precisam ser pensados com cuidado para não bloquear integrações legítimas.

---

## 15. Timeouts e tamanho de payload

Operações como registro de manifesto, chamadas de API e carregamento de assets podem ser afetadas por timeouts.

Configurações a avaliar no Nginx:

```nginx
client_max_body_size
proxy_connect_timeout
proxy_send_timeout
proxy_read_timeout
```

Recomendação:

- manter limites seguros;
- não permitir payloads arbitrariamente grandes;
- ajustar tamanho máximo de manifesto se necessário;
- monitorar endpoints lentos.

---

## 16. Logs do Gateway

O Compose de produção configura rotação de logs para o serviço `gateway`.

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

Boas práticas:

- não logar tokens;
- não logar secrets;
- preservar IP de origem quando possível;
- usar logs para troubleshooting de 404/502/504;
- centralizar logs em ambiente produtivo.

---

## 17. Erros comuns

### 17.1 502 Bad Gateway

Possíveis causas:

- upstream não está rodando;
- nome do serviço incorreto;
- serviço ainda não está pronto;
- porta interna diferente da configurada;
- container não está na `delpi-network`.

### 17.2 404 em rota de plugin

Possíveis causas:

- plugin não está roteado no Nginx;
- `basePath` do manifesto não bate com path do Gateway;
- build do plugin gerou assets com base path incorreto;
- plugin não está ativo/registrado na Core API;
- Gateway não aponta para o container correto.

### 17.3 Login redireciona errado

Possíveis causas:

- `KC_HOSTNAME` incorreto;
- `KC_HTTP_RELATIVE_PATH` divergente;
- proxy headers incorretos;
- redirect URI do client Keycloak incompatível;
- `VITE_KC_URL` diferente da URL pública real.

### 17.4 Socket.IO não conecta

Possíveis causas:

- falta de headers de upgrade;
- path incorreto;
- token não enviado no handshake;
- timeout/proxy incompatível;
- CORS/origin bloqueado.

---

## 18. Checklist de validação do Gateway

- [ ] `http://localhost/` carrega o Portal em desenvolvimento.
- [ ] `/core-api/health` responde via Gateway.
- [ ] `/auth` abre Keycloak via Gateway.
- [ ] API DELPI responde no path configurado.
- [ ] Plugins carregam assets no path `/apps/<plugin-id>`.
- [ ] Header `Authorization` chega aos backends.
- [ ] Socket.IO funciona se roteado pelo Gateway.
- [ ] Keycloak gera issuer coerente com a URL pública.
- [ ] Não há exposição direta desnecessária de containers internos.
- [ ] Logs do Gateway não expõem tokens/secrets.

---

## 19. Pendências de validação

Para fechar este documento como definitivo, validar os arquivos reais:

```text
gateway/nginx.dev.conf
gateway/nginx.conf
gateway/Dockerfile.dev
gateway/Dockerfile.prod
```

Itens a confirmar:

- paths exatos;
- portas internas dos upstreams;
- suporte a WebSocket/Socket.IO;
- fallback de SPA;
- headers de proxy;
- headers de segurança;
- roteamento de cada plugin;
- roteamento da API DELPI.

---

## 20. Documentos relacionados

```text
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/ambientes-dev-prod.md
docs/02-infraestrutura/variaveis-de-ambiente.md
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/05-plugin-system/microfrontends.md
```
