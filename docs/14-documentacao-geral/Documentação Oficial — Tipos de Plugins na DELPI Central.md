# 📦 Documentação Oficial — Tipos de Plugins na DELPI Central

> Documento técnico oficial que descreve detalhadamente TODOS os tipos de plugins suportados pela DELPI Central, suas arquiteturas, fluxos de execução, configurações e quando utilizar cada um.

---

# 🧠 Visão Geral da Arquitetura da DELPI Central

A DELPI Central foi projetada como uma plataforma extensível baseada em plugins.

Cada plugin é registrado via **manifesto JSON** e pode operar em diferentes modos de execução.

A arquitetura é composta por:

- React + Vite (Portal Host)
- Module Federation (para plugins federados)
- Iframe embedding (para plugins isolados)
- Backend proxy (para serviços backend-only)
- Gateway NGINX
- Docker

---

# 🧩 Tipos Oficiais de Plugins

A plataforma suporta atualmente 3 categorias principais:

| Tipo | type | ui.renderMode | Como é carregado |
|------|------|---------------|------------------|
| Microfrontend Federado | microfrontend | federated | Module Federation |
| Microfrontend Embedded | microfrontend | embedded | Iframe interno |
| Iframe Externo | iframe | embedded / external | Iframe |
| Backend Only | backend-only | — | Apenas serviço backend |

---

# 1️⃣ Microfrontend Federado

## 📌 Conceito

Plugin frontend carregado dinamicamente via Module Federation.

O código é injetado no DOM da Central e compartilha runtime com o host.

---

## 🏗️ Arquitetura

```
Portal Host
   ↓
Carrega remoteEntry.js
   ↓
Container Federation
   ↓
mount(el, props)
```

---

## ⚙️ Requisitos Técnicos

- Vite + @originjs/vite-plugin-federation
- Arquivo bootstrap.tsx exportando mount/unmount
- main.tsx importando bootstrap dinamicamente
- base: "/"

---

## 📄 Exemplo de Manifesto

```json
{
  "type": "microfrontend",
  "basePath": "/crm",
  "entry": "/apps/crm/remoteEntry.js",
  "ui": { "renderMode": "federated" }
}
```

---

## 🔐 Comunicação

Props diretas:

- token
- pathname
- basePath
- search

---

## ✅ Vantagens

- Melhor performance
- Compartilha React
- Integração profunda
- Menor custo de carregamento

---

## ❌ Desvantagens

- CSS pode vazar
- Maior complexidade
- Dependência de versão compatível

---

# 2️⃣ Microfrontend Embedded

## 📌 Conceito

Aplicação frontend isolada carregada via iframe interno.

Não compartilha runtime com o host.

---

## 🏗️ Arquitetura

```
Portal
   ↓
<iframe src="/apps/app-x/">
   ↓
Aplicação standalone
```

---

## 📄 Manifesto

```json
{
  "type": "microfrontend",
  "entry": "/apps/crm/",
  "ui": { "renderMode": "embedded" }
}
```

---

## 🔐 Comunicação

Via postMessage:

Central envia:

```js
postMessage({ type: "DELPI_AUTH", token })
```

Iframe pode solicitar refresh:

```js
postMessage({ type: "DELPI_REFRESH_REQUEST" })
```

---

## ✅ Vantagens

- Isolamento total de CSS
- Pode usar qualquer versão de React
- Ideal para sistemas já existentes
- Deploy independente

---

## ❌ Desvantagens

- Comunicação mais complexa
- Performance inicial levemente inferior
- Não compartilha design system automaticamente

---

# 3️⃣ Iframe Plugin (Aplicação Externa)

## 📌 Conceito

Plugin que aponta para uma URL externa.

Pode ser aberto:

- embedded (iframe interno)
- external (nova aba)

---

## 📄 Manifesto

```json
{
  "type": "iframe",
  "entry": "https://sistema-externo.com",
  "ui": { "renderMode": "external" }
}
```

---

## 🎯 Uso Ideal

- Sistemas SaaS
- Portais externos
- Ferramentas terceiras

---

# 4️⃣ Backend-Only Plugin

## 📌 Conceito

Plugin que registra apenas um serviço backend.

Sem interface frontend.

---

## 📄 Manifesto

```json
{
  "type": "backend-only",
  "backend": {
    "serviceName": "api-delpi",
    "baseUrl": "/apps/api-delpi",
    "validateJwt": true
  }
}
```

---

## 🏗️ Fluxo

```
Portal
   ↓
Gateway
   ↓
Serviço Backend
```

---

## 🎯 Uso Ideal

- APIs internas
- Integrações com ERP
- Serviços para agentes GPT

---

# 🧠 Comparação Estratégica

| Característica | Federated | Embedded | Iframe | Backend-only |
|---------------|------------|-----------|---------|---------------|
| UI Integrada | ✔ | ✔ | ✔ | ✖ |
| Compartilha React | ✔ | ✖ | ✖ | ✖ |
| Isolamento Total | ✖ | ✔ | ✔ | ✔ |
| Comunicação Direta | ✔ | Via postMessage | Limitada | API |
| Ideal para | Plugins internos | Sistemas independentes | SaaS | Serviços |

---

# 🔒 Segurança

Todos os plugins respeitam:

- RBAC da Central
- Validação JWT
- Controle por permission codes

---

# 📌 Boas Práticas Oficiais

- Nunca usar CSS global em federated
- Sempre usar base: "/" em federated
- Sempre validar JWT em backend-only
- Nunca expor serviços diretamente fora do gateway
- Versionar plugins usando SemVer

---

# 🏁 Conclusão

A DELPI Central permite múltiplas estratégias de extensão, cada uma adequada a diferentes cenários técnicos e organizacionais.

A escolha correta do tipo de plugin impacta diretamente:

- Performance
- Escalabilidade
- Manutenção
- Segurança

Este documento deve ser utilizado como referência oficial para decisões arquiteturais futuras.

