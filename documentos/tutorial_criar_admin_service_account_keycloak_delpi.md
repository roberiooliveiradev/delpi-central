# 📘 Tutorial Completo — Criando um Service Account Admin no Keycloak (DELPI Central)

Este guia foi criado para iniciantes. Vamos passo a passo criar um **usuário técnico administrador (Service Account)** para que o Core da DELPI Central possa se comunicar com o Keycloak de forma segura.

---

# 🎯 Objetivo
Criar um client técnico chamado:

```
delpi-core-admin
```

Esse client será usado pelo backend (core-api) para:

- Atualizar usuários
- Sincronizar permissões
- Administrar dados no Keycloak

⚠️ Ele NÃO é um usuário humano.
⚠️ Ele NÃO faz login na interface.
⚠️ Ele é um "robô interno" do sistema.

---

# 🧭 Parte 1 — Acessar o Keycloak

1. Abra o navegador
2. Acesse:

```
http://localhost:8080
```

3. Faça login com:

- Usuário: `admin`
- Senha: `admin`

4. No canto superior esquerdo, selecione o Realm:

```
delpi
```

Se não estiver no realm `delpi`, troque antes de continuar.

---

# 🧱 Parte 2 — Criar o Client Técnico

## 1️⃣ Vá em:

Menu lateral → **Clients**

## 2️⃣ Clique em:

**Create client**

## 3️⃣ Preencha:

- Client ID: `delpi-core-admin`
- Client type: OpenID Connect

Clique em **Next**.

## 4️⃣ Configuração do Client

Na tela seguinte:

- Access type: **Confidential**
- Marque: ✅ Service Accounts Enabled

Clique em **Save**.

Agora o client foi criado.

---

# 🔐 Parte 3 — Obter o Client Secret

1. Dentro do client recém criado
2. Clique na aba **Credentials**
3. Copie o campo:

```
Client Secret
```

⚠️ Guarde esse valor. Ele será usado no `.env` do backend.

---

# 🛡 Parte 4 — Dar Permissões de Administrador

Agora vamos dar poderes administrativos ao service account.

## 1️⃣ Vá na aba:

**Service account roles**

## 2️⃣ Clique em:

**Assign role**

⚠️ Muito importante: No topo do modal, altere o filtro.

Troque de:

```
Filter by realm roles
```

Para:

```
Filter by clients
```

## 3️⃣ No dropdown de clientes, selecione:

```
realm-management
```

Agora aparecerão as roles administrativas.

## 4️⃣ Selecione as seguintes roles:

- manage-users
- view-users
- query-users
- manage-realm

💡 Para simplificar e evitar erros futuros, você pode também marcar:

- realm-admin

## 5️⃣ Clique em:

**Assign**

Pronto. O service account agora é administrador do realm.

---

# ⚙️ Parte 5 — Configurar o Core API

Agora vamos configurar o backend.

Abra o arquivo `.env` do core-api e adicione:

```
KEYCLOAK_ADMIN_CLIENT_ID=delpi-core-admin
KEYCLOAK_ADMIN_CLIENT_SECRET=SEU_SECRET_AQUI
KEYCLOAK_ADMIN_REALM=delpi
KEYCLOAK_ADMIN_URL=http://keycloak:8080
```

Substitua `SEU_SECRET_AQUI` pelo valor copiado na aba Credentials.

---

# 🔄 Parte 6 — Reiniciar o Backend

No terminal, execute:

```
docker compose restart core-api
```

Isso faz o sistema gerar um novo token administrativo.

---

# 🧠 Como Funciona Internamente

Quando o Core precisa atualizar um usuário:

1. Ele solicita um token ao Keycloak usando:
   - grant_type=client_credentials
2. O Keycloak emite um token com as roles administrativas
3. O Core usa esse token para chamar a Admin API

Tudo isso acontece automaticamente.

---

# 🚨 Problemas Comuns

## 403 Forbidden
Significa que as roles não foram atribuídas corretamente.

Verifique se adicionou as roles dentro de:

```
realm-management
```

---

## 401 Unauthorized
Significa que o client secret está errado ou o realm está incorreto.

---

# 🏁 Resultado Final Esperado

Após concluir:

- O Core consegue atualizar usuários
- O RBAC funciona corretamente
- Não ocorre mais erro 403
- Não ocorre mais erro 401

---

# 🎉 Conclusão

Você criou um Service Account administrativo seguro e alinhado com a arquitetura ideal da DELPI Central.

Essa é a forma correta e profissional de integrar backend com Keycloak.

Se desejar, posso criar agora:

- 🔐 Versão simplificada para documentação interna
- 🏢 Versão corporativa formal
- 📊 Fluxograma visual da arquitetura
- 🤖 Versão para onboarding de novos desenvolvedores

Basta me dizer qual formato você prefere.

