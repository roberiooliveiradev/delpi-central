# 🔐 Tutorial Completo — Configuração do Keycloak (DEV)

## DELPI Central — Versão Atualizada (Gateway /auth)

Este guia recria **do zero** toda a configuração do Keycloak conforme a arquitetura atual da DELPI Central.

⚠️ IMPORTANTE: Nesta versão o Keycloak é exposto exclusivamente via gateway em:

```
http://localhost/auth
```

Não utilizar mais `:8080` externamente para autenticação.   

---

# 🏗 Arquitetura Atual (DEV)

Serviços expostos:

- Portal → [http://localhost](http://localhost)
- Core API → [http://localhost/core-api](http://localhost/core-api)
- Keycloak → [http://localhost/auth](http://localhost/auth)

Issuer oficial do Realm:

```
http://localhost/auth/realms/delpi
```

---

# 📌 1️⃣ Subir o Ambiente

No diretório `infra`:

```bash
docker compose up -d
```

Aguardar todos os containers iniciarem.

---

# 🟢 2️⃣ Acessar Admin Console

Acesse:

```
http://localhost/auth
```

Login inicial:

- User: admin
- Password: admin

---

# 🟢 3️⃣ Criar Realm

1. No canto superior esquerdo → Dropdown de realms
2. Clique em **Create Realm**
3. Nome:

```
delpi
```

Salvar.

⚠️ O nome deve ser exatamente `delpi`.

---

# 🟢 4️⃣ Criar Client (Portal DELPI Central)

Vá em:

```
Clients → Create Client
```

## General Settings

| Campo       | Valor                    |
| ----------- | ------------------------ |
| Client ID   | delpi-central            |
| Name        | DELPI Central            |
| Description | Portal Corporativo DELPI |

Clique em **Next**.

---

## Capability Config

| Opção                 | Valor |
| --------------------- | ----- |
| Client authentication | OFF   |
| Authorization         | OFF   |
| Standard flow         | ON    |
| Direct access grants  | OFF   |
| Implicit flow         | OFF   |

Clique em **Next**.

---

## Login Settings (Configuração Atualizada)

| Campo               | Valor                                                                    |
| ------------------- | ------------------------------------------------------------------------ |
| Root URL            | [http://localhost](http://localhost)                                     |
| Home URL            | [http://localhost](http://localhost)                                     |
| Valid redirect URIs | [http://localhost/](http://localhost/)\*                                 |
|                     | [https://oauth.pstmn.io/v1/callback](https://oauth.pstmn.io/v1/callback) |
| Web origins         | \*                                                                       |

Salvar.

⚠️ A entrada `http://localhost/*` é obrigatória para o login do portal.
⚠️ A entrada do Postman é necessária para testes OAuth.

---

# 🟢 5️⃣ Configurar Audience (Obrigatório)

A Core API valida:

```
KEYCLOAK_AUDIENCE=delpi-central
```

Precisamos incluir essa audience no token.

---

## 5.1 Criar Client Scope

```
Client Scopes → Create client scope
```

| Campo    | Valor          |
| -------- | -------------- |
| Name     | audience-delpi |
| Type     | Default        |
| Protocol | openid-connect |

Salvar.

---

## 5.2 Criar Mapper

Dentro do client scope criado:

```
Mappers → Configure a new mapper
```

| Campo                    | Valor          |
| ------------------------ | -------------- |
| Name                     | audience-delpi |
| Mapper Type              | Audience       |
| Included Client Audience | delpi-central  |
| Add to access token      | ON             |
| Add to ID token          | OFF            |
| Add to userinfo          | OFF            |

Salvar.

---

## 5.3 Vincular ao Client

```
Clients → delpi-central → Client Scopes
```

Adicionar `audience-delpi` como Default Client Scope.

---

# 🟢 6️⃣ Verificar Issuer Oficial

Abra no navegador:

```
http://localhost/auth/realms/delpi/.well-known/openid-configuration
```

O campo `issuer` deve ser exatamente:

```
http://localhost/auth/realms/delpi
```

Se estiver diferente → a configuração está incorreta.

---

# 🟢 7️⃣ Criar Usuário Administrador

```
Users → Add user
```

| Campo          | Valor                                                        |
| -------------- | ------------------------------------------------------------ |
| Username       | rober                                                        |
| Email          | [engenharia6@delpi.com.br](mailto\:engenharia6@delpi.com.br) |
| First name     | Robério                                                      |
| Last name      | Oliveira                                                     |
| Email verified | ON                                                           |

Salvar.

---

## Definir Senha

Aba **Credentials**:

1. Set password
2. Definir senha
3. Temporary = OFF
4. Save

---

# 🟢 8️⃣ Login na Aplicação

Acesse:

```
http://localhost
```

Fluxo esperado:

1. Portal redireciona para
   [http://localhost/auth/realms/delpi/](http://localhost/auth/realms/delpi/)...
2. Usuário realiza login
3. Retorna para o portal autenticado

---

# 🟢 9️⃣ Validar Token

No navegador:

DevTools → Application → Local Storage

Copiar `access_token`.

Validar em [https://jwt.io](https://jwt.io)

O token deve conter:

```json
"iss": "http://localhost/auth/realms/delpi",
"aud": ["account", "delpi-central"],
"azp": "delpi-central"
```

---

# 🟢 🔟 Validar Core API

Testar:

```
http://localhost/core-api/me
```

Deve retornar 200 com dados do usuário.

---

# 🔐 Checklist Final

- [ ] Realm correto (`delpi`)
- [ ] Client ID correto (`delpi-central`)
- [ ] Audience configurada
- [ ] Issuer correto
- [ ] Token contém `aud=delpi-central`
- [ ] Usuário criado
- [ ] Login funcionando
- [ ] `/core-api/me` retornando 200

---

# 🏁 Resultado Esperado

Após este procedimento:

- SSO funcionando via gateway
- JWT válido
- Audience validada
- Core API integrada
- Ambiente DEV estabilizado

DELPI Central — Configuração DEV concluída (versão com /auth).

