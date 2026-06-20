# Minha DELPI — Banco de Dados do Keycloak

> **Arquivo:** `docs/09-banco-de-dados/keycloak-db.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** banco PostgreSQL interno do Keycloak e regras de isolamento

---

## 1. Objetivo

Este documento descreve o banco **`keycloak-db`** da Minha DELPI.

O `keycloak-db` é o banco PostgreSQL usado exclusivamente pelo Keycloak para armazenar seus dados internos de identidade, realm, clients, sessões e configurações.

---

## 2. Princípio central

Regra obrigatória:

> A aplicação Minha DELPI não deve acessar diretamente o banco `keycloak-db`.

Toda interação com autenticação deve acontecer por meio de:

- OIDC;
- JWT;
- JWKS;
- endpoints do Keycloak;
- Admin API do Keycloak quando necessário.

---

## 3. Serviço Docker

Serviço:

```text
keycloak-db
```

Container:

```text
delpi-keycloak-db
```

Imagem:

```text
postgres:15
```

Volume persistente:

```text
keycloak_data
```

---

## 4. Variáveis do banco

O serviço `keycloak-db` usa:

```env
POSTGRES_KC_DB=
POSTGRES_KC_USER=
POSTGRES_KC_PASSWORD=
TZ=
```

No Compose:

```yaml
POSTGRES_DB: ${POSTGRES_KC_DB}
POSTGRES_USER: ${POSTGRES_KC_USER}
POSTGRES_PASSWORD: ${POSTGRES_KC_PASSWORD}
TZ: ${TZ}
```

---

## 5. Consumidor principal

O consumidor do `keycloak-db` é exclusivamente o serviço:

```text
keycloak
```

O Keycloak se conecta ao banco usando:

```yaml
KC_DB: postgres
KC_DB_URL: jdbc:postgresql://keycloak-db:5432/${POSTGRES_KC_DB}
KC_DB_USERNAME: ${POSTGRES_KC_USER}
KC_DB_PASSWORD: ${POSTGRES_KC_PASSWORD}
```

---

## 6. O que o Keycloak armazena

O banco do Keycloak armazena dados internos como:

- realms;
- clients;
- client scopes;
- users do Keycloak;
- credenciais;
- roles internas do Keycloak;
- sessões;
- chaves;
- mappers;
- configurações OIDC;
- eventos internos, conforme configuração.

Essas tabelas são gerenciadas pelo próprio Keycloak.

---

## 7. O que não pertence ao `keycloak-db`

Não devem ser armazenados nem manipulados pela aplicação nesse banco:

- RBAC interno da Minha DELPI;
- roles da plataforma;
- grupos da plataforma;
- permissões da plataforma;
- apps;
- rotas;
- manifestos;
- favoritos;
- notificações;
- dados de plugins;
- dados operacionais;
- dados TOTVS.

Esses dados pertencem ao `postgres-core`, ao `postgres-plugins` ou a sistemas externos.

---

## 8. Keycloak autentica, Core API autoriza

A separação oficial é:

```text
Keycloak → autenticação
Core API → autorização funcional
```

O Keycloak emite tokens JWT.

A Core API:

- valida o token;
- sincroniza usuário local;
- calcula permissões efetivas;
- filtra apps e rotas;
- aplica decorators de autorização.

As roles do Keycloak não são a fonte final de autorização da Minha DELPI.

---

## 9. Relação com usuário local

A Core API cria ou atualiza um usuário local em:

```text
postgres-core.users
```

a partir das claims do JWT.

Fluxo:

```text
Keycloak autentica
  ↓
Keycloak emite JWT
  ↓
Core API valida JWT
  ↓
Core API lê sub/email/name
  ↓
Core API cria ou atualiza users no postgres-core
```

O usuário local da plataforma não deve ser lido diretamente do banco do Keycloak.

---

## 10. Admin API

A Core API possui variáveis para integração administrativa com Keycloak:

```env
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=
```

Essa integração, quando usada, deve ocorrer pela Admin API, não por queries diretas no `keycloak-db`.

Cuidados:

- não expor client secret ao frontend;
- usar service account com menor privilégio;
- usar HTTPS em produção;
- auditar uso administrativo.

---

## 11. Persistência

O volume:

```text
keycloak_data
```

preserva dados do banco entre reinicializações.

Se o volume for removido, o Keycloak perde seu estado local:

- realms;
- clients;
- usuários;
- mappers;
- configurações;
- sessões.

A remoção de volume deve ser tratada como operação destrutiva.

---

## 12. Reset em desenvolvimento

Em desenvolvimento, pode ser necessário resetar o Keycloak.

Comando destrutivo típico:

```bash
docker compose -f docker-compose.dev.yml down -v
```

Atenção:

> Esse comando remove todos os volumes da stack, incluindo `keycloak_data`, `postgres_core_data` e `postgres_plugins_data`.

Depois do reset, será necessário recriar/configurar o Keycloak.

---

## 13. Backup em produção

Em produção, o `keycloak-db` deve fazer parte da política de backup.

Recomendações:

- backup regular do volume/banco;
- teste periódico de restore;
- backup antes de upgrades de Keycloak;
- backup antes de alterar realm/client crítico;
- manter documentação da configuração mínima do realm.

---

## 14. Upgrade do Keycloak

O Keycloak gerencia internamente seu schema.

Ao atualizar versão:

- ler notas oficiais da versão;
- fazer backup do banco;
- testar upgrade em homologação;
- validar login;
- validar emissão de token;
- validar JWKS;
- validar issuer;
- validar audience;
- validar logout;
- validar Gateway/proxy.

---

## 15. Relação com Gateway e hostname

O banco em si não define issuer, mas a configuração persistida e o runtime do Keycloak influenciam tokens e URLs.

Variáveis relevantes do serviço Keycloak:

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

Configuração incorreta pode causar:

- issuer divergente;
- redirect inválido;
- token rejeitado pela Core API;
- falha em JWKS;
- login/logout inconsistente.

---

## 16. Troubleshooting

### 16.1 Keycloak não sobe

Verificar:

- `keycloak-db` está de pé;
- credenciais `POSTGRES_KC_*`;
- `KC_DB_URL`;
- volume `keycloak_data`;
- logs do container `delpi-keycloak-db`;
- logs do container `keycloak`.

---

### 16.2 Login funciona, mas Core API rejeita token

Verificar:

- `KEYCLOAK_ISSUER`;
- `KEYCLOAK_JWKS_URL`;
- `KEYCLOAK_AUDIENCE`;
- claim `aud`;
- claim `iss`;
- acesso da Core API ao JWKS;
- hostname/relative path do Keycloak.

---

### 16.3 Perda de realm/client após reset

Causa provável:

```text
volume keycloak_data removido
```

Ação:

- restaurar backup;
- ou reconfigurar realm/client;
- ou reexecutar procedimento oficial de configuração.

---

## 17. Boas práticas

1. Não acessar `keycloak-db` diretamente pela aplicação.
2. Usar OIDC/JWT para autenticação.
3. Usar Admin API quando for necessário administrar Keycloak.
4. Fazer backup antes de upgrades.
5. Não remover volume em produção.
6. Proteger credenciais `POSTGRES_KC_*`.
7. Proteger credenciais administrativas.
8. Validar issuer/audience após mudanças de hostname.
9. Manter documentação do realm/client.
10. Separar autenticação Keycloak de autorização da Core API.

---

## 18. Pontos de atenção

1. O `keycloak-db` é exclusivo do Keycloak.
2. Não persistir RBAC da plataforma nesse banco.
3. Não consultar tabelas internas do Keycloak a partir da Core API.
4. O schema interno é gerenciado pelo Keycloak.
5. Upgrade exige backup.
6. Reset de volume apaga realm/client/users.
7. Core API usa JWT/JWKS, não queries no banco.
8. Roles do Keycloak não substituem permissions da plataforma.
9. Hostname/proxy impactam tokens e redirects.
10. Produção deve usar `start`, não `start-dev`.

---

## 19. Documentos relacionados

```text
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/03-autenticacao-autorizacao/jwt.md
docs/09-banco-de-dados/core-db.md
docs/02-infraestrutura/docker-compose.md
docs/10-guias-operacionais/configurar-keycloak.md
```
