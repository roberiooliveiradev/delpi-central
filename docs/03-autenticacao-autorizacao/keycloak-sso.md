# Minha DELPI — Keycloak e SSO

> **Arquivo:** `docs/03-autenticacao-autorizacao/keycloak-sso.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** autenticação SSO com Keycloak, configuração, integração com Portal, Core API e Gateway

---

## 1. Objetivo

Este documento descreve como o **Keycloak** participa da autenticação da Minha DELPI.

Ele explica:

- o papel do Keycloak;
- como o Portal usa SSO;
- como a Core API valida tokens;
- quais variáveis de ambiente são usadas;
- como o Keycloak roda no Docker;
- como separar autenticação Keycloak de autorização RBAC interna;
- pontos de atenção para desenvolvimento e produção.

---

## 2. Papel do Keycloak

O Keycloak é o provedor de identidade da Minha DELPI.

Responsabilidades:

- autenticar usuários;
- gerenciar sessão SSO;
- emitir tokens JWT;
- expor JWKS para validação de assinatura;
- fornecer issuer e audience esperados;
- suportar login/logout do Portal;
- permitir SSO entre aplicações compatíveis.

O Keycloak não é a fonte final de autorização funcional da Minha DELPI.

Regra central:

```text
Keycloak autentica.
Core API autoriza.
```

---

## 3. Separação entre autenticação e autorização

A Minha DELPI separa responsabilidades.

| Responsabilidade | Sistema |
|---|---|
| Login do usuário | Keycloak |
| Emissão de access token | Keycloak |
| Validação de assinatura JWT | Core API / API DELPI |
| Sincronização de usuário local | Core API |
| Cálculo de permissões efetivas | Core API |
| Apps e rotas autorizados | Core API |
| Menu final do usuário | Portal, a partir de `/me/apps` |

O token identifica o usuário.

As permissões finais são resolvidas pelo RBAC interno da Core API.

---

## 4. Serviços Docker envolvidos

Serviços relacionados ao Keycloak:

```text
keycloak-db
keycloak
```

Banco do Keycloak:

```text
keycloak-db
```

Container do Keycloak:

```text
delpi-keycloak
```

Imagem:

```text
quay.io/keycloak/keycloak:24.0
```

---

## 5. Banco do Keycloak

O Keycloak usa PostgreSQL próprio.

Serviço:

```text
keycloak-db
```

Variáveis:

```env
POSTGRES_KC_DB=
POSTGRES_KC_USER=
POSTGRES_KC_PASSWORD=
TZ=
```

Volume:

```text
keycloak_data:/var/lib/postgresql/data
```

Regra:

> A aplicação Minha DELPI não deve acessar diretamente o banco interno do Keycloak. A integração deve acontecer via OIDC/JWT e, quando necessário, Admin API.

---

## 6. Keycloak em desenvolvimento

No Docker Compose de desenvolvimento, o Keycloak usa:

```yaml
command: ["start-dev"]
```

Características:

- modo de desenvolvimento;
- configuração mais permissiva;
- adequado para ambiente local;
- não recomendado para produção.

O container recebe alias de rede:

```yaml
aliases:
  - keycloak
```

Esse alias é importante para resolução interna entre containers.

---

## 7. Keycloak em produção

No Docker Compose de produção, o Keycloak usa:

```yaml
command: ["start"]
```

Em produção, as variáveis de hostname, proxy e HTTPS precisam estar corretamente configuradas.

Variáveis importantes:

```env
KC_HTTP_ENABLED=
KC_HTTP_PORT=
KC_HTTP_RELATIVE_PATH=
KC_HOSTNAME=
KC_HOSTNAME_STRICT=
KC_HOSTNAME_STRICT_HTTPS=
KC_PROXY=
KC_PROXY_HEADERS=
```

Ponto de atenção:

> Configuração incorreta de hostname/proxy pode causar issuer incorreto, redirects inválidos e falhas de validação JWT.

---

## 8. Variáveis administrativas do Keycloak

Variáveis para criação do administrador inicial:

```env
KEYCLOAK_ADMIN=
KEYCLOAK_ADMIN_PASSWORD=
```

Essas credenciais são usadas para acessar o console administrativo do Keycloak.

Cuidados:

- não versionar senhas reais;
- usar valores fortes em produção;
- restringir acesso ao console administrativo;
- rotacionar credenciais quando necessário.

---

## 9. Tema customizado

O Docker Compose monta temas customizados:

```yaml
volumes:
  - ./keycloak/themes:/opt/keycloak/themes:ro
```

Uso:

- customizar tela de login;
- aplicar identidade visual da Minha DELPI;
- manter login integrado à experiência da plataforma.

Cuidados:

- validar compatibilidade do tema com Keycloak 24;
- evitar customizações que quebrem upgrade;
- testar login/logout após alterações.

---

## 10. Configuração do Portal

O Portal usa variáveis Vite para inicializar o client Keycloak.

```env
VITE_KC_URL=
VITE_KC_REALM=
VITE_KC_CLIENT_ID=
VITE_KC_REDIRECT_URI=
```

Descrição:

| Variável | Uso |
|---|---|
| `VITE_KC_URL` | URL pública do Keycloak para o navegador |
| `VITE_KC_REALM` | Realm usado pela Minha DELPI |
| `VITE_KC_CLIENT_ID` | Client público do Portal |
| `VITE_KC_REDIRECT_URI` | Redirect URI após autenticação |

Como variáveis `VITE_*` são embutidas no build, não devem conter segredos.

---

## 11. Client do Portal

O client do Portal no Keycloak deve ser público.

Configuração esperada:

```text
Client type: public
Standard flow: enabled
Valid redirect URIs: URL(s) do Portal
Web origins: URL(s) do Portal
```

O Portal não deve possuir client secret.

Regra:

> Aplicações frontend públicas não devem armazenar segredos.

---

## 12. Redirect URI

O redirect URI precisa bater com o valor usado pelo Portal.

Exemplo conceitual local:

```text
http://localhost/*
```

ou valor específico:

```text
http://localhost/
```

A variável do Portal:

```env
VITE_KC_REDIRECT_URI=
```

precisa estar compatível com as configurações do client no Keycloak.

Erro comum quando divergente:

```text
Invalid redirect_uri
```

---

## 13. Web Origins

O client do Portal deve permitir a origem usada pelo navegador.

Exemplo local:

```text
http://localhost
```

ou:

```text
+
```

conforme política adotada.

Em produção, restringir para domínios reais.

---

## 14. Realm

O realm é o domínio de autenticação da Minha DELPI.

Variáveis relacionadas:

```env
VITE_KC_REALM=
KEYCLOAK_REALM=
KEYCLOAK_ADMIN_REALM=
```

O realm usado pelo Portal, Core API e API DELPI deve ser consistente.

---

## 15. Issuer

O issuer esperado pela Core API vem de:

```env
KEYCLOAK_ISSUER=
```

Ele deve ser igual ao claim `iss` do token.

Exemplo conceitual:

```text
http://localhost/auth/realms/delpi
```

ou, dependendo da configuração de path/hostname:

```text
http://localhost/realms/delpi
```

Ponto de atenção:

> A URL exata depende de `KC_HTTP_RELATIVE_PATH`, hostname e proxy. Sempre comparar com o `iss` real do token.

---

## 16. JWKS

A Core API valida assinatura JWT usando JWKS.

Variável:

```env
KEYCLOAK_JWKS_URL=
```

Exemplo conceitual:

```text
http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs
```

ou URL equivalente conforme relative path.

Regra:

> A URL de JWKS precisa ser acessível de dentro do container da Core API.

A URL pública do navegador pode ser diferente da URL interna entre containers.

---

## 17. Audience

A audience esperada vem de:

```env
KEYCLOAK_AUDIENCE=
```

A Core API valida se o token contém essa audience.

Causa comum de erro:

```text
Token válido no Keycloak, mas sem aud esperado pela Core API.
```

Solução típica:

- configurar audience mapper no client;
- ajustar `KEYCLOAK_AUDIENCE` para o valor correto;
- validar o token decodificado.

---

## 18. Claims necessárias

A Core API espera claims para criar/sincronizar usuário local.

Claims principais:

```text
sub
email
name
iss
aud
exp
```

Regras:

- `sub` deve ser UUID válido;
- `email` deve estar presente;
- `name` deve estar presente ou possuir fallback;
- `iss` deve bater com `KEYCLOAK_ISSUER`;
- `aud` deve conter `KEYCLOAK_AUDIENCE`;
- `exp` não pode estar expirado.

---

## 19. Usuário local na Core API

Após validar o token, a Core API sincroniza o usuário.

Fluxo:

```text
JWT validado
  ↓
Extrai sub/email/name
  ↓
Busca users.email
  ↓
Se não existe, cria users com id=sub
  ↓
Atualiza last_login_at
  ↓
Resolve roles/groups/permissions
```

O Keycloak autentica.

A tabela `users` representa o usuário local na plataforma.

---

## 20. Roles do Keycloak versus RBAC interno

Mesmo que o Keycloak possua roles, a Minha DELPI usa RBAC interno na Core API para autorização da plataforma.

Regra atual:

```text
Roles/permissões efetivas da Minha DELPI vêm do banco Core.
```

O token não deve ser usado como fonte final de autorização de apps e rotas.

Motivo:

- apps/plugins são registrados dinamicamente;
- permissões vivem no banco da Core API;
- grupos/roles internos podem ser administrados pela plataforma;
- overrides individuais são internos;
- superadmin é flag local.

---

## 21. Admin API do Keycloak

A Core API possui variáveis para integração administrativa com Keycloak:

```env
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=
```

Uso esperado:

- operações administrativas futuras;
- sincronização avançada;
- consulta/criação de usuários, se implementada;
- integração controlada com Keycloak Admin API.

Cuidados:

- client secret deve ser segredo de backend;
- nunca expor no Portal;
- restringir permissões do service account;
- usar HTTPS em produção.

---

## 22. SSO com aplicações iframe

Aplicações iframe podem usar o mesmo Keycloak para SSO.

Cenário recomendado:

```text
Portal autentica no Keycloak
  ↓
Iframe aponta para aplicação que também usa o mesmo realm
  ↓
Aplicação iframe reconhece sessão SSO
```

Cuidados:

- cookies SameSite/Secure;
- domínio e HTTPS;
- headers de iframe;
- redirect URIs da aplicação integrada;
- evitar token em query string.

---

## 23. Gateway e Keycloak

O Gateway expõe o Keycloak ao navegador e aos serviços.

Pontos importantes:

- a URL pública precisa bater com hostname/issuer;
- proxy headers precisam estar corretos;
- relative path deve estar coerente;
- redirects devem usar URL pública correta.

Variáveis relacionadas:

```env
KC_PROXY=
KC_PROXY_HEADERS=
KC_HOSTNAME=
KC_HTTP_RELATIVE_PATH=
```

---

## 24. Desenvolvimento local

Fluxo local típico:

```text
Gateway expõe http://localhost
Portal acessa Keycloak via VITE_KC_URL
Core API valida token via KEYCLOAK_JWKS_URL
Keycloak usa start-dev
```

Checklist local:

- Keycloak sobe sem erro;
- realm existe;
- client do Portal existe;
- redirect URI está correto;
- token contém email/name;
- Core API acessa JWKS;
- issuer/audience batem;
- `/me` funciona após login.

---

## 25. Produção

Em produção:

- usar `start`, não `start-dev`;
- configurar hostname real;
- usar HTTPS;
- configurar proxy corretamente;
- restringir redirect URIs;
- restringir web origins;
- proteger console administrativo;
- usar senhas fortes;
- persistir banco do Keycloak;
- monitorar saúde do Keycloak.

---

## 26. Erros comuns

### 26.1 `Invalid redirect_uri`

Causa:

```text
URL do Portal não está cadastrada no client.
```

Correção:

- ajustar Valid Redirect URIs;
- ajustar `VITE_KC_REDIRECT_URI`;
- verificar Gateway/hostname.

---

### 26.2 Core API retorna `invalid_token`

Causas:

- `KEYCLOAK_JWKS_URL` errado;
- `KEYCLOAK_ISSUER` divergente;
- `KEYCLOAK_AUDIENCE` ausente no token;
- token expirado;
- container não acessa JWKS;
- relative path diferente.

---

### 26.3 Token sem email

Causa:

```text
Mapper de email ausente ou client scope incorreto.
```

Correção:

- incluir client scope apropriado;
- configurar mapper de email;
- validar token decodificado.

---

### 26.4 Token sem audience esperada

Causa:

```text
Audience mapper não configurado.
```

Correção:

- criar mapper de audience;
- ajustar client ID/audience;
- alinhar `KEYCLOAK_AUDIENCE`.

---

### 26.5 Issuer diferente entre navegador e container

Causa:

```text
Hostname/proxy/relative path inconsistentes.
```

Correção:

- configurar `KC_HOSTNAME`;
- configurar proxy headers;
- garantir URL pública estável;
- ajustar `KEYCLOAK_ISSUER` para o issuer real.

---

## 27. Checklist de configuração do Keycloak

- [ ] Realm da Minha DELPI criado.
- [ ] Client público do Portal criado.
- [ ] Standard Flow habilitado.
- [ ] Redirect URIs configurados.
- [ ] Web Origins configurados.
- [ ] Token contém `sub` UUID.
- [ ] Token contém `email`.
- [ ] Token contém `name`.
- [ ] Audience esperada está no token.
- [ ] Issuer do token bate com `KEYCLOAK_ISSUER`.
- [ ] JWKS URL acessível pela Core API.
- [ ] API DELPI usa mesmas referências de issuer/audience quando necessário.
- [ ] Admin client configurado apenas no backend, se usado.

---

## 28. Boas práticas

1. Não usar roles do Keycloak como autorização final da plataforma.
2. Não colocar client secret no Portal.
3. Usar client público para frontend.
4. Validar issuer e audience no backend.
5. Usar JWKS para validar assinatura.
6. Garantir claims necessárias no access token.
7. Restringir redirect URIs em produção.
8. Usar HTTPS em produção.
9. Evitar token em query string.
10. Documentar qualquer mapper customizado.

---

## 29. Pontos de atenção

1. Keycloak 24 usa configurações de hostname/proxy sensíveis.
2. `start-dev` é apenas para desenvolvimento.
3. JWKS interno pode usar hostname diferente da URL pública.
4. Issuer precisa bater exatamente com o token.
5. Audience ausente causa 401.
6. `sub` precisa ser UUID na Core API atual.
7. Portal usa variáveis `VITE_*`, sem segredos.
8. Core API possui variáveis de Admin API que não devem ir para o frontend.
9. Aplicações iframe precisam de SSO próprio ou estratégia segura.
10. RBAC final é interno da Core API.

---

## 30. Documentos relacionados

```text
docs/03-autenticacao-autorizacao/jwt.md
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/06-portal-frontend/autenticacao-frontend.md
docs/02-infraestrutura/docker-compose.md
docs/02-infraestrutura/gateway-nginx.md
```

