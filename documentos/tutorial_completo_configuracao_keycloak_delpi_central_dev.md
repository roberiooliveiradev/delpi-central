# 🔐 Tutorial Completo — Configuração do Keycloak (DEV)
## DELPI Central

Este guia recria **do zero** toda a configuração do Keycloak conforme a `.env` atual da Core API.

Ambiente:
- Docker
- Keycloak 24
- Realm: `delpi`
- Client: `delpi-central`

---

# 📌 1️⃣ Subir o Ambiente

No diretório `infra`:

```bash
docker compose up -d
```

Acesse o Keycloak:

```
http://localhost:8080
```

Login inicial:

- User: `admin`
- Password: `admin`

---

# 🟢 2️⃣ Criar Realm

1. No canto superior esquerdo → Clique no dropdown
2. Clique em **Create Realm**
3. Nome do Realm:

```
delpi
```

Salvar.

⚠️ O nome deve ser exatamente `delpi` para bater com:

```
KEYCLOAK_ISSUER=http://localhost/realms/delpi
```

---

# 🟢 3️⃣ Criar Client (Aplicação DELPI Central)

Vá em:

```
Clients → Create Client
```

## Configuração

### General Settings

| Campo | Valor |
|--------|--------|
| Client ID | delpi-central |
| Name | DELPI Central |
| Description | Portal Corporativo DELPI |

Clique em **Next**.

---

### Capability Config

| Opção | Valor |
|--------|--------|
| Client authentication | OFF |
| Authorization | OFF |
| Standard flow | ON |
| Direct access grants | OFF |
| Implicit flow | OFF |

Clique em **Next**.

---

### Login Settings

| Campo | Valor |
|--------|--------|
| Root URL | http://localhost |
| Home URL | http://localhost |
| Valid redirect URIs | http://localhost/* |
| Web origins | * |

Salvar.

---

# 🟢 4️⃣ Configurar Audience (Obrigatório)

A Core API valida:

```
KEYCLOAK_AUDIENCE=delpi-central
```

Precisamos incluir essa audience no token.

---

## 4.1 Criar Client Scope

Vá em:

```
Client Scopes → Create client scope
```

| Campo | Valor |
|--------|--------|
| Name | audience-delpi |
| Type | Default |
| Protocol | openid-connect |

Salvar.

---

## 4.2 Criar Mapper dentro do Client Scope

Dentro de `audience-delpi`:

```
Mappers → Configure a new mapper
```

Configuração:

| Campo | Valor |
|--------|--------|
| Name | audience-delpi |
| Mapper Type | Audience |
| Included Client Audience | delpi-central |
| Add to access token | ON |
| Add to ID token | OFF |
| Add to userinfo | OFF |

Salvar.

---

## 4.3 Vincular Client Scope ao Client

Vá em:

```
Clients → delpi-central → Client Scopes
```

Em **Assigned Default Client Scopes**:

Clique em **Add client scope**

Selecione:

```
audience-delpi
```

Adicionar.

---

# 🟢 5️⃣ Verificar Issuer

O token deve conter:

```
"iss": "http://localhost/realms/delpi"
```

Isso já estará correto se:

- Realm = delpi
- Acesso via http://localhost:8080

---

# 🟢 6️⃣ Criar Usuário Administrador

Vá em:

```
Users → Add user
```

## Dados:

| Campo | Valor |
|--------|--------|
| Username | rober |
| Email | engenharia6@delpi.com.br |
| First name | Robério |
| Last name | Oliveira |
| Email verified | ON |

Salvar.

---

## Definir senha

Aba **Credentials**:

1. Set password
2. Defina senha
3. Temporary = OFF
4. Save

---

# 🟢 7️⃣ Testar Token

Faça login no Portal.

Abra DevTools → Application → Local Storage

Copie o `access_token`.

Cole em:

https://jwt.io

O token deve conter:

```json
"iss": "http://localhost/realms/delpi",
"aud": ["account", "delpi-central"],
"azp": "delpi-central"
```

Se isso estiver correto → a Core API aceitará.

---

# 🟢 8️⃣ Validar Core API

Teste:

```
http://localhost/core-api/me
```

Deve retornar JSON com dados do usuário.

---

# 🔐 Checklist Final de Segurança

- [ ] Realm correto (`delpi`)
- [ ] Client ID correto (`delpi-central`)
- [ ] Audience configurada
- [ ] Issuer correto
- [ ] Token contém `aud=delpi-central`
- [ ] Usuário criado
- [ ] Login funcionando
- [ ] `/core-api/me` retornando 200

---

# 🏁 Resultado Esperado

Após esse procedimento:

- SSO funcionando
- JWT válido
- Audience validada
- Core API integrada
- Base pronta para RBAC

---

Tutorial válido para ambiente de desenvolvimento local.

DELPI Central — Configuração DEV concluída.

