# 📦 Guia Oficial Atualizado — Microfrontends na DELPI Central

> Documento técnico definitivo para criação, build e integração de microfrontends federados na arquitetura da DELPI Central.
>
> ⚠️ Este guia substitui versões anteriores e corrige problemas reais enfrentados durante integração.

---

# 🧠 1. Entendendo a Arquitetura (Para Iniciantes)

A DELPI Central funciona como um **Host (Portal)** que carrega aplicações externas chamadas **Microfrontends**.

Arquitetura simplificada:

Portal (Host React)
↓
Gateway (NGINX)
↓
Microfrontend (Build Estático via NGINX)
↓
APIs

O microfrontend é carregado dinamicamente através de:

```
remoteEntry.js
```

E montado via função:

```
mount(el, props)
```

⚠️ IMPORTANTE: Microfrontend NÃO é uma aplicação React normal rodando com `vite dev`.
Ele precisa ser buildado e servido como arquivos estáticos.

---

# 🏗️ 2. Estrutura Padrão do Plugin

```
dashboard-delpi/
 ├─ src/
 │   ├─ App.tsx
 │   ├─ bootstrap.tsx
 │   ├─ main.tsx
 │   └─ styles.css (evitar CSS global)
 ├─ vite.config.ts
 ├─ package.json
 ├─ Dockerfile
```

---

# ⚙️ 3. Configuração Correta do Vite

## vite.config.ts

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import federation from "@originjs/vite-plugin-federation";

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: "dashboard-delpi",
      filename: "remoteEntry.js",
      exposes: {
        "./App": "./src/bootstrap.tsx",
      },
      shared: ["react", "react-dom"],
    }),
  ],

  // 🔥 REGRA CRÍTICA
  base: "/",

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
```

---

# 🚨 ERRO COMUM #1 — base incorreto

❌ Nunca use:

```
base: "/apps/nome-do-plugin/"
```

Isso quebra o carregamento via gateway.

---

# 📁 4. Arquivos Obrigatórios

## 4.1 main.tsx

```ts
import("./bootstrap");
```

Isso impede execução automática quando usado como remote.

---

## 4.2 bootstrap.tsx

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

## 4.3 App.tsx

```tsx
function App() {
  return <h1>Meu Dashboard</h1>;
}

export default App;
```

---

# 🐳 5. Dockerfile CORRETO (PRODUÇÃO)

⚠️ Este foi o maior problema enfrentado.

NÃO use vite preview.
NÃO use volumes.

Use multi-stage build:

```dockerfile
# =========================
# BUILD
# =========================
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# =========================
# SERVE
# =========================
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

# 🚨 ERRO COMUM #2 — Usar vite preview

❌ Errado:

```
CMD ["npm", "run", "preview"]
```

Isso NÃO gera arquivos físicos acessíveis ao federation.

---

# 🧩 6. docker-compose CORRETO

```yaml
dashboard-delpi:
  build:
    context: ../plugins/dashboard-delpi
  container_name: delpi-dashboard-delpi
  ports:
    - "5176:80"
  networks:
    - delpi-network
```

❌ NÃO usar volumes em produção federada.

---

# 🌐 7. Configuração do Gateway (NGINX)

⚠️ Simplifique.

```nginx
location ^~ /apps/dashboard-delpi/ {
  proxy_pass http://dashboard-delpi:80/;
}
```

❌ NÃO criar regra específica para remoteEntry.
❌ NÃO mapear manualmente /assets.

---

# 📦 8. Manifesto do Plugin

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-delpi",
  "name": "Dashboard DELPI",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/dashboard-delpi",
  "entry": "/apps/dashboard-delpi/assets/remoteEntry.js",
  "ui": {
    "renderMode": "federated"
  },
  "permissions": [
    {
      "code": "dashboard-delpi.access",
      "name": "Acesso ao Dashboard",
      "module": "dashboard-delpi"
    }
  ],
  "routes": [
    {
      "path": "/dashboard-delpi",
      "label": "Dashboard",
      "permission": "dashboard-delpi.access",
      "icon": "layout-dashboard",
      "order": 1,
      "showInMenu": true
    }
  ]
}
```

---

# 🧪 9. Testes Obrigatórios Antes de Registrar

### 1️⃣ Teste direto do remoteEntry

Abra:

```
http://localhost/apps/dashboard-delpi/assets/remoteEntry.js
```

✔ Deve retornar JS.

❌ Se retornar HTML → problema no proxy.

---

### 2️⃣ Verificar dist dentro do container

```
docker exec -it delpi-dashboard-delpi sh
ls /usr/share/nginx/html
```

Deve existir pasta assets com remoteEntry.js.

---

# 🚨 Principais Problemas Enfrentados (E Como Evitar)

| Problema | Causa | Solução |
|----------|--------|----------|
| remoteEntry não carrega | dist inexistente | usar multi-stage build |
| Failed to fetch dynamically imported module | vite preview | usar nginx estático |
| remoteEntry retorna HTML | proxy errado | usar location geral |
| Erro de porta | container em 80, gateway em 5176 | alinhar portas |
| Federation quebra | base incorreto | usar base: "/" |

---

# 📌 Checklist Final Obrigatório

- [ ] base: "/"
- [ ] Expose aponta para bootstrap
- [ ] main.tsx importa bootstrap dinamicamente
- [ ] Docker multi-stage
- [ ] Sem volumes
- [ ] Gateway simples
- [ ] entry do manifesto aponta para /assets/remoteEntry.js

---

# 🏁 Conclusão

Seguindo este guia:

✔ O microfrontend será carregado corretamente
✔ Federation funcionará em produção
✔ O gateway não retornará HTML indevido
✔ O container terá dist físico
✔ A arquitetura ficará estável e escalável

Este documento passa a ser o padrão oficial para criação de plugins na DELPI Central.

