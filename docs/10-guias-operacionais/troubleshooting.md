# Minha DELPI — Guia Operacional: Troubleshooting

> **Arquivo:** `docs/10-guias-operacionais/troubleshooting.md`  
> **Status:** documentação oficial  
> **Produto:** Minha DELPI  
> **Escopo:** diagnóstico operacional de problemas comuns no ambiente local

---

## 1. Objetivo

Este guia reúne procedimentos de diagnóstico para problemas comuns na Minha DELPI.

Ele cobre:

- Docker Compose;
- Gateway;
- Portal;
- Core API;
- Keycloak;
- bancos;
- JWT;
- RBAC;
- plugins;
- API DELPI.

---

## 2. Comando inicial de diagnóstico

A partir da pasta `infra`:

```bash
docker compose -f docker-compose.dev.yml ps
```

Verifique se os serviços esperados estão `Up`.

Depois, ver logs gerais:

```bash
docker compose -f docker-compose.dev.yml logs -f
```

---

## 3. Gateway não responde

Sintoma:

```text
http://localhost não abre
```

Verificar:

```bash
docker compose -f docker-compose.dev.yml logs -f gateway
```

Causas comuns:

- porta 80 ocupada;
- Gateway não subiu;
- erro em `nginx.dev.conf`;
- serviço upstream indisponível;
- rede Docker indisponível.

Verificar porta 80:

```bash
sudo lsof -i :80
```

---

## 4. Core API não responde

Teste:

```bash
curl http://localhost/core-api/health
```

Se falhar, verificar:

```bash
docker compose -f docker-compose.dev.yml logs -f core-api
```

Causas comuns:

- erro de variáveis de ambiente;
- banco indisponível;
- migrations pendentes;
- import quebrado;
- dependência Python ausente;
- `FLASK_APP` incorreto;
- seed falhando.

---

## 5. Banco Core sem tabelas

Sintoma:

```text
relation users does not exist
```

ou erro semelhante.

Solução:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
```

Validar tabelas:

```bash
docker exec -it delpi-postgres-core psql -U <usuario> -d <database>
\dt
```

---

## 6. Keycloak não abre

Acessar:

```text
http://localhost/auth
```

Ver logs:

```bash
docker compose -f docker-compose.dev.yml logs -f keycloak
docker compose -f docker-compose.dev.yml logs -f keycloak-db
```

Causas comuns:

- banco do Keycloak indisponível;
- credenciais `POSTGRES_KC_*` incorretas;
- `KC_DB_URL` incorreto;
- hostname/proxy mal configurado;
- volume corrompido.

---

## 7. Portal não autentica

Sintomas:

- redirect loop;
- `Invalid redirect_uri`;
- tela branca após login;
- retorno sem sessão.

Verificar:

```env
VITE_KC_URL
VITE_KC_REALM
VITE_KC_CLIENT_ID
VITE_KC_REDIRECT_URI
```

No Keycloak:

- Valid Redirect URIs;
- Web Origins;
- client público;
- standard flow;
- realm correto.

---

## 8. Core API retorna 401

Sintomas:

```text
invalid_token
unauthorized
```

Verificar:

- header `Authorization: Bearer <token>`;
- token expirado;
- `KEYCLOAK_JWKS_URL`;
- `KEYCLOAK_ISSUER`;
- `KEYCLOAK_AUDIENCE`;
- claim `aud`;
- claim `iss`;
- claim `email`;
- `sub` é UUID válido;
- Core API consegue acessar JWKS pelo hostname interno.

---

## 9. Core API retorna 403

Sintoma:

```text
forbidden
```

Significa:

```text
usuário autenticado, mas sem permissão
```

Verificar:

- usuário existe na Core API;
- usuário possui role;
- role possui permission;
- usuário pertence a grupo;
- grupo possui role;
- override individual não removeu permissão;
- cache RBAC foi invalidado;
- superadmin está correto;
- decorator exige permission correta.

---

## 10. `/me/apps` não retorna plugin

Verificar:

- plugin está registrado;
- `apps.active=true`;
- rota está ativa;
- rota possui permission correta;
- usuário possui permission;
- app tem pelo menos uma rota autorizada;
- manifesto foi registrado com sucesso;
- Gateway serve o plugin;
- Portal recarregou `/me/apps`.

---

## 11. Plugin aparece, mas não carrega

Verificar diretamente:

```text
http://localhost/apps/<plugin>/assets/remoteEntry.js
```

Resultado esperado:

```text
JavaScript
```

Se retornar HTML, 404 ou erro do Gateway:

- verificar Nginx;
- verificar build do plugin;
- verificar base path do Vite;
- verificar Dockerfile do plugin;
- verificar assets;
- verificar path no manifesto.

---

## 12. Problema com Module Federation

Sintomas:

- erro ao carregar remote;
- `mount is not a function`;
- tela branca;
- erro de chunk.

Verificar:

- plugin exporta `mount`;
- plugin exporta `unmount`;
- `remoteEntry.js` está acessível;
- dependências compartilhadas estão corretas;
- base pública é `/apps/<plugin>/`;
- build foi recriado.

---

## 13. API DELPI não responde

Ver logs:

```bash
docker compose -f docker-compose.dev.yml logs -f api-delpi
```

Verificar:

- variáveis `TOTVS_DB_*`;
- variáveis `PLUGINS_DB_*`;
- variáveis `PORTAL_RH_DB_*`;
- `API_DELPI_PORT`;
- conexão com `postgres-plugins`;
- conexão com TOTVS externo;
- JWT/Keycloak.

---

## 14. Postgres Plugins não conecta

Verificar:

```bash
docker compose -f docker-compose.dev.yml logs -f postgres-plugins
```

Em dev:

```text
localhost:5433
```

No container:

```text
postgres-plugins:5432
```

Verificar:

- `PLUGINS_DB_NAME`;
- `PLUGINS_DB_USER`;
- `PLUGINS_DB_PASSWORD`;
- volume `postgres_plugins_data`;
- `plugins-init.sql`.

---

## 15. Reset completo local

Se o ambiente estiver inconsistente e for aceitável apagar dados:

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up --build -d
```

Depois:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
```

E reconfigurar Keycloak.

---

## 16. Logs por serviço

Gateway:

```bash
docker compose -f docker-compose.dev.yml logs -f gateway
```

Portal:

```bash
docker compose -f docker-compose.dev.yml logs -f portal
```

Core API:

```bash
docker compose -f docker-compose.dev.yml logs -f core-api
```

Keycloak:

```bash
docker compose -f docker-compose.dev.yml logs -f keycloak
```

API DELPI:

```bash
docker compose -f docker-compose.dev.yml logs -f api-delpi
```

Postgres Core:

```bash
docker compose -f docker-compose.dev.yml logs -f postgres-core
```

Postgres Plugins:

```bash
docker compose -f docker-compose.dev.yml logs -f postgres-plugins
```

---

## 17. Ordem recomendada de diagnóstico

1. Verificar containers.
2. Verificar Gateway.
3. Verificar health da Core API.
4. Verificar Keycloak.
5. Verificar banco Core.
6. Verificar token/JWT.
7. Verificar RBAC.
8. Verificar `/me`.
9. Verificar `/me/apps`.
10. Verificar plugin/Gateway.
11. Verificar API DELPI.

---

## 18. Checklist rápido

- [ ] Containers estão `Up`.
- [ ] Gateway responde.
- [ ] `/core-api/health` responde.
- [ ] Keycloak responde.
- [ ] Banco Core tem tabelas.
- [ ] Token possui issuer correto.
- [ ] Token possui audience correta.
- [ ] Usuário existe na Core API.
- [ ] Usuário possui permissões.
- [ ] `/me` responde.
- [ ] `/me/apps` responde.
- [ ] Plugin está registrado.
- [ ] `remoteEntry.js` responde.
- [ ] API DELPI conecta nos datasources.

---

## 19. Pontos de atenção

1. `depends_on` não garante prontidão real.
2. Reset com `down -v` apaga bancos.
3. Keycloak precisa ser reconfigurado após reset.
4. Portal não é fonte final de autorização.
5. Core API autoriza apps e rotas.
6. API DELPI deve proteger seus próprios endpoints.
7. Gateway roteia, mas não substitui validação de backend.
8. `remoteEntry.js` deve retornar JavaScript.
9. `VITE_*` exige rebuild em produção.
10. Não diagnosticar frontend antes de validar `/me` e `/me/apps`.

---

## 20. Documentos relacionados

```text
docs/10-guias-operacionais/subir-ambiente-dev.md
docs/10-guias-operacionais/reset-banco-dev.md
docs/10-guias-operacionais/configurar-keycloak.md
docs/10-guias-operacionais/registrar-plugin.md
docs/02-infraestrutura/docker-compose.md
docs/03-autenticacao-autorizacao/jwt.md
```
