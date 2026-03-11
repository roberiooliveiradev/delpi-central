# Tutorial Completo — Autenticação SSO GLPI com Keycloak via SAML

Este guia descreve passo a passo como configurar **Single Sign‑On (SSO)** entre o **GLPI** e o **Keycloak** utilizando o plugin **samlsso**.

O tutorial documenta exatamente a configuração que funcionou no ambiente da plataforma DELPI.

---

# Arquitetura da solução

Fluxo de autenticação:

1. Usuário acessa GLPI
2. GLPI redireciona para Keycloak
3. Usuário autentica no Keycloak
4. Keycloak retorna resposta SAML
5. GLPI valida a resposta
6. Usuário entra no sistema

```
Usuário
   ↓
GLPI (Service Provider)
   ↓ SAML
Keycloak (Identity Provider)
   ↓ SAML Response
GLPI
   ↓
Usuário autenticado
```

---

# Requisitos

Antes de iniciar confirme:

- GLPI instalado e funcionando
- Keycloak instalado
- HTTPS configurado
- Plugin **samlsso** disponível no marketplace do GLPI
- Usuários cadastrados no Keycloak

Exemplo do ambiente usado:

GLPI

```
https://helpdesk.centraldelpi.com.br
```

Keycloak

```
https://centraldelpi.com.br/auth
```

---

# Etapa 1 — Instalar plugin samlsso

No GLPI:

1. Acesse

```
Configurar
Plugins
Marketplace
```

2. Procure por:

```
samlsso
```

3. Clique em:

```
Instalar
```

4. Depois clique em:

```
Ativar
```

Após isso aparecerá o menu:

```
Configurar
SAML SSO
```

---

# Etapa 2 — Criar configuração SAML no GLPI

Abra:

```
Configurar
SAML SSO
Adicionar
```

## Aba General

Preencha:

Friendly name

```
Keycloak
```

Is Active

```
ON
```

Debug

```
OFF
```

---

# Etapa 3 — Configurar Service Provider (GLPI)

O plugin gera automaticamente os dados do Service Provider.

Use os seguintes valores:

Entity ID

```
https://helpdesk.centraldelpi.com.br/
```

ACS URL

```
https://helpdesk.centraldelpi.com.br/marketplace/samlsso/front/acs/1
```

SLO URL

```
https://helpdesk.centraldelpi.com.br/marketplace/samlsso/front/logout/1
```

Esses dados serão usados no Keycloak.

O GLPI também gera automaticamente:

- SP CERTIFICATE
- SP PRIVATE KEY

Não altere esses campos.

---

# Etapa 4 — Criar Client SAML no Keycloak

No Keycloak:

```
Clients
Create Client
```

Escolha:

```
Client type: SAML
```

## General settings

Client ID

```
https://helpdesk.centraldelpi.com.br/
```

Name

```
GLPI Helpdesk
```

---

# Etapa 5 — Access Settings

Root URL

```
https://helpdesk.centraldelpi.com.br/
```

Home URL

```
https://helpdesk.centraldelpi.com.br/
```

Valid Redirect URIs

```
https://helpdesk.centraldelpi.com.br/marketplace/samlsso/front/acs/1
```

Valid Post Logout Redirect URIs

```
https://helpdesk.centraldelpi.com.br/marketplace/samlsso/front/logout/1
```

Master SAML Processing URL

```
https://helpdesk.centraldelpi.com.br/marketplace/samlsso/front/acs/1
```

Salvar.

---

# Etapa 6 — Configuração SAML Capabilities

Name ID format

```
email
```

Force POST binding

```
ON
```

Include AuthnStatement

```
ON
```

Outras opções

```
OFF
```

---

# Etapa 7 — Signature and Encryption

Sign documents

```
ON
```

Sign assertions

```
ON
```

Signature algorithm

```
RSA_SHA256
```

SAML signature key name

```
NONE
```

Canonicalization

```
EXCLUSIVE
```

---

# Etapa 8 — Obter Metadata do Keycloak

No realm do Keycloak obtenha:

Entity ID

```
https://centraldelpi.com.br/auth/realms/delpi
```

SSO URL

```
https://centraldelpi.com.br/auth/realms/delpi/protocol/saml
```

SLO URL

```
https://centraldelpi.com.br/auth/realms/delpi/protocol/saml
```

Certificado X509

Copie do metadata XML.

---

# Etapa 9 — Configurar Identity Provider no GLPI

No GLPI preencha:

ENTITY ID

```
https://centraldelpi.com.br/auth/realms/delpi
```

SSO URL

```
https://centraldelpi.com.br/auth/realms/delpi/protocol/saml
```

SLO URL

```
https://centraldelpi.com.br/auth/realms/delpi/protocol/saml
```

X509 Certificate

```
Certificado copiado do Keycloak
```

REQ AUTHN CONTEXT

```
none
```

AUTHN COMPARISON

```
Exact
```

Salvar.

---

# Etapa 10 — Corrigir erro de atributos duplicados

Erro encontrado durante configuração:

```
OneLogin\Saml2\ValidationError
Found an Attribute element with duplicated Name
```

Causa:

O Keycloak envia atributos duplicados via **Client Scopes**.

Principal responsável:

```
role_list
```

## Solução

No Keycloak:

```
Clients
GLPI Client
Client Scopes
```

Remover ou mudar para NONE:

```
role_list
```

---

# Etapa 11 — Remover mappers duplicados

No Keycloak:

```
Client Scopes
<client>-dedicated
Mappers
```

Remover mappers:

```
username
email
```

Deixe o scope dedicado **sem mappers**.

Isso evita duplicação de atributos SAML.

---

# Etapa 12 — Testar autenticação

Acesse:

```
https://helpdesk.centraldelpi.com.br
```

Clique em:

```
Login via Keycloak
```

Fluxo esperado:

```
GLPI
↓
Keycloak
↓
Login
↓
Redirecionamento SAML
↓
GLPI
↓
Usuário autenticado
```

---

# Resultado final

O usuário consegue acessar o GLPI usando a autenticação do Keycloak.

Benefícios:

- Login único
- Integração com identidade corporativa
- Centralização de usuários
- Segurança via SAML

---

# Próximas melhorias recomendadas

Configurar:

- criação automática de usuários
- sincronização de grupos
- logout único
- controle de perfis GLPI

---

# Fim do tutorial

