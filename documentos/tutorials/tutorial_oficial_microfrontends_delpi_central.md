# 📦 Tutorial Oficial — Criação de Microfrontends na DELPI Central

> Documento técnico oficial para criação, configuração e integração de microfrontends federados na arquitetura da DELPI Central.

---

# 🧠 Visão Geral da Arquitetura

A DELPI Central utiliza:

- **React + Vite**
- **Module Federation via @originjs/vite-plugin-federation**
- **Gateway NGINX como reverse proxy**
- **Containerização via Docker**
- **Manifesto JSON para registro dinâmico do plugin**

O microfrontend é carregado dinamicamente através de:

```
remoteEntry.js
```

E montado no host via:

```
mount(el, props)
```

---

# 🏗️ Estrutura Padrão do Microfrontend

```
test-microfrontend/
 ├─ src/
 │   ├─ App.tsx
 │   ├─ bootstrap.tsx
 │   ├─ main.tsx
 │   └─ index.css (evitar CSS global)
 ├─ vite.config.ts
 ├─ package.json
 ├─ Dockerfile
```

---

# ⚙️ Configuração do Vite (OBRIGATÓRIA)

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "test-microfrontend",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom", "react-router-dom"],
    }),
  ],

  // ⚠️ REGRA IMPORTANTE
  base: "/",

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
```

## 🔥 REGRA CRÍTICA

Nunca use:

```
base: "/apps/nome-do-app/"
```

Isso quebra o carregamento via gateway.

---

# 🧩 Arquivos Obrigatórios

## 1️⃣ main.tsx

```ts
import("./bootstrap");
```

Ele impede execução automática quando usado como remote.

---

## 2️⃣ bootstrap.tsx

```ts
import ReactDOM from "react-dom/client";
import App from "./App";

let root: ReactDOM.Root | null = null;

export function mount(el: HTMLElement, props: any) {
  root = ReactDOM.createRoot(el);
  root.render(<App {...props} />);
}

export function unmount() {
  root?.unmount();
  root = null;
}
```

---

## 3️⃣ App.tsx

```tsx
function App() {
  return <h2>Olá mundo!</h2>;
}

export default App;
```

---

# 🚫 Regras Importantes de CSS

Microfrontends NÃO podem:

- Estilizar `body`
- Estilizar `html`
- Resetar CSS global
- Alterar layout do host

Recomendado:

```
Usar classes locais ou CSS Modules
```

---

# 🐳 Dockerfile (Modo Produção - Preview)

```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 5175
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5175"]
```

---

# 🔁 docker-compose

```yaml
test-microfrontend:
  build: ../test-microfrontend
  container_name: delpi-test-microfrontend
  ports:
    - "5175:5175"
  networks:
    - delpi-network
```

---

# 🌐 Configuração do Gateway (NGINX)

```nginx
location = /apps/test-microfrontend/remoteEntry.js {
  proxy_pass http://test-microfrontend:5175/assets/remoteEntry.js;
}

location ^~ /apps/test-microfrontend/ {
  proxy_pass http://test-microfrontend:5175/;

  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection $connection_upgrade;
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;

  proxy_read_timeout 86400;
}
```

---

# 📝 Manifesto do Plugin

Exemplo:

```json
{
  "schemaVersion": "1.0.0",
  "id": "test-microfrontend",
  "name": "Teste Microfrontend",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/test-microfrontend",
  "entry": "/apps/test-microfrontend/remoteEntry.js",
  "ui": {
    "renderMode": "federated"
  },
  "permissions": [
    {
      "code": "test-microfrontend.access",
      "name": "Acesso",
      "module": "test-microfrontend"
    }
  ],
  "routes": [
    {
      "path": "/test-microfrontend",
      "label": "Dashboard",
      "permission": "test-microfrontend.access",
      "icon": "layout-dashboard",
      "order": 1,
      "showInMenu": true
    }
  ]
}
```

---

# 🔍 Testes Essenciais

### 1️⃣ Deve retornar JS

```
http://localhost/apps/test-microfrontend/remoteEntry.js
```

### 2️⃣ Não deve retornar HTML

Se retornar HTML → problema no proxy.

---

# 🚨 Erros Comuns e Causas

| Erro | Causa |
|------|-------|
| Failed to fetch dynamically imported module | base incorreto |
| Container federado não encontrado | scope incorreto |
| Página da central desconfigurada | CSS global vazando |
| remoteEntry retorna HTML | proxy errado |

---

# 📌 Checklist Final

- [ ] base: "/"
- [ ] exposes aponta para bootstrap
- [ ] main.tsx importa bootstrap dinamicamente
- [ ] Sem CSS global
- [ ] Proxy mapeando remoteEntry para /assets
- [ ] Manifest entry correto

---

# 🏁 Conclusão

Seguindo este padrão, qualquer novo plugin microfrontend poderá ser criado e integrado à DELPI Central de forma previsível, estável e escalável.

Este documento deve ser utilizado como referência oficial para todos os próximos plugins.

