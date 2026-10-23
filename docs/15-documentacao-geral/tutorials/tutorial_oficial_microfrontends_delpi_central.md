# 📦 Tutorial Oficial — Criação de Plugins Microfrontend na DELPI Central

> Documento técnico oficial para criação, configuração, build, proxy e integração de plugins microfrontend federados na arquitetura da DELPI Central.

---

# 🧠 Visão Geral da Arquitetura

A DELPI Central utiliza:

- **React + Vite**
- **Module Federation via `@originjs/vite-plugin-federation`**
- **Gateway NGINX como reverse proxy**
- **Containerização via Docker**
- **Manifesto JSON para registro dinâmico do plugin**
- **Portal host carregando o plugin via `entryUrl` retornado pela Core**

O plugin microfrontend é carregado dinamicamente através de:

```text
/apps/<plugin>/assets/remoteEntry.js
```

E montado no host via:

```ts
mount(el, props)
```

---

# ✅ Padrão Oficial Atual

## Regra principal

O padrão oficial vigente da DELPI Central para plugins federados é:

- o **arquivo físico gerado** pelo Vite Federation é `remoteEntry.js`
- a **URL pública consumida pelo portal** é:

```text
/apps/<plugin>/assets/remoteEntry.js
```

- o gateway deve tratar **esse arquivo específico** como exceção de cache
- os demais assets em `/assets/*` continuam podendo usar cache longo

## Consequência prática

O manifesto do plugin e o payload entregue pela Core para o portal devem apontar para:

```text
/apps/<plugin>/assets/remoteEntry.js
```

Esse é o padrão que o portal realmente consome hoje.

---

# 🏗️ Estrutura Padrão do Plugin

```text
test-microfrontend/
 ├─ src/
 │   ├─ App.tsx
 │   ├─ bootstrap.tsx
 │   ├─ main.tsx
 │   └─ index.css
 ├─ vite.config.ts
 ├─ package.json
 ├─ Dockerfile
 └─ delpi.manifest.json
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
      shared: ["react", "react-dom"],
    }),
  ],

  base: "/apps/test-microfrontend/",

  build: {
    target: "esnext",
    modulePreload: false,
    cssCodeSplit: false,
  },
});
```

## Regras obrigatórias

- `filename` deve ser `remoteEntry.js`
- `exposes` deve apontar para `./src/bootstrap.tsx`
- `base` deve usar o path público real do plugin:

```ts
base: "/apps/<plugin>/"
```

## Exemplo real

Para o plugin `dashboard-lmps`:

```ts
base: "/apps/dashboard-lmps/"
```

---

# 🧩 Arquivos Obrigatórios

## 1️⃣ `main.tsx`

```ts
import("./bootstrap");
```

Esse arquivo impede execução automática inadequada quando o bundle é usado como remote.

---

## 2️⃣ `bootstrap.tsx`

```ts
import ReactDOM from "react-dom/client";
import App from "./App";

const roots = new WeakMap<HTMLElement, ReactDOM.Root>();

export function mount(el: HTMLElement, props: any = {}) {
  let root = roots.get(el);

  if (!root) {
    root = ReactDOM.createRoot(el);
    roots.set(el, root);
  }

  root.render(<App {...props} />);
}

export function unmount(el?: HTMLElement) {
  if (!el) return;

  const root = roots.get(el);
  if (!root) return;

  root.unmount();
  roots.delete(el);
}
```

## Regras obrigatórias

- exportar `mount(el, props)`
- exportar `unmount(el)`
- o host deve poder montar e desmontar o plugin sem efeitos colaterais globais

---

## 3️⃣ `App.tsx`

```tsx
export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  return <div>Plugin carregado</div>;
}
```

## Regra importante

O componente raiz deve aceitar `props` do host quando necessário, por exemplo:

- `getAccessToken`
- configurações de contexto
- callbacks do host

---

# 📝 Manifesto do Plugin

Exemplo:

```json
{
  "schemaVersion": "1.0.0",
  "id": "dashboard-lmps",
  "name": "Dashboard LMPs",
  "description": "Dashboard analítico de LMPs",
  "icon": "bar-chart3-icon",
  "version": "1.0.0",
  "type": "microfrontend",

  "basePath": "/apps/dashboard-lmps",
  "entry": "/apps/dashboard-lmps/assets/remoteEntry.js",

  "permissions": [
    {
      "code": "dashboard-lmps.view",
      "name": "Acesso ao dashboard LMPs",
      "description": "Permite acessar o dashboard",
      "module": "dashboard-lmps"
    }
  ],

  "routes": [
    {
      "path": "/apps/dashboard-lmps",
      "label": "Dashboard LMPs",
      "permission": "dashboard-lmps.view",
      "icon": "bar-chart3-icon",
      "order": 1,
      "showInMenu": true
    }
  ],

  "ui": {
    "renderMode": "federated"
  }
}
```

## Regras importantes

- `type` deve ser `microfrontend`
- `basePath` deve refletir o path público do plugin
- `entry` deve apontar para:

```text
/apps/<plugin>/assets/remoteEntry.js
```

- `routes[].path` deve estar alinhado com o path público do plugin

---

# 🔍 Testes Essenciais

## 1️⃣ O remote entry deve retornar JavaScript

```text
http://localhost/apps/test-microfrontend/assets/remoteEntry.js
```

## 2️⃣ Não pode retornar HTML

Se retornar HTML, o proxy está errado.

## 3️⃣ O cache do remote entry deve ser de no-store

Teste:

```bash
curl -I http://localhost/apps/test-microfrontend/assets/remoteEntry.js
```

Esperado:

```text
Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0
```

## 4️⃣ Assets hashados podem ser imutáveis

Teste:

```bash
curl -I http://localhost/apps/test-microfrontend/assets/__federation_expose_App-xxxx.js
```

Esperado:

```text
Cache-Control: public, max-age=31536000, immutable
```

---

# 🚨 Erros Comuns e Causas

| Erro | Causa provável |
|------|----------------|
| Plugin não atualiza após deploy | `assets/remoteEntry.js` cacheado como asset comum |
| Failed to fetch dynamically imported module | `entry` incorreto, proxy incorreto ou asset ausente |
| remoteEntry retorna HTML | fallback/proxy errado |
| Portal continua na versão antiga | `entryUrl` estável com cache incorreto no `remoteEntry.js` |
| CSS do host afetado | vazamento de CSS global do plugin |

---

# 📌 Checklist Final

- [ ] `filename: "remoteEntry.js"`
- [ ] `exposes` aponta para `./src/bootstrap.tsx`
- [ ] `main.tsx` importa `./bootstrap` dinamicamente
- [ ] `base: "/apps/<plugin>/"`
- [ ] manifesto com `entry: "/apps/<plugin>/assets/remoteEntry.js"`
- [ ] gateway trata `assets/remoteEntry.js` sem cache forte
- [ ] gateway trata os demais assets com cache longo
- [ ] sem CSS global vazando para o host
- [ ] `mount(el, props)` e `unmount(el)` funcionando corretamente

---

# 🏁 Conclusão

O padrão oficial atual da DELPI Central para plugins microfrontend federados é:

- `remoteEntry.js` gerado via Vite Federation
- URL pública do entry em `/apps/<plugin>/assets/remoteEntry.js`
- `base` configurado em `/apps/<plugin>/`
- manifesto apontando para `/assets/remoteEntry.js`
- gateway com exceção explícita de cache para `assets/remoteEntry.js`

Este documento passa a substituir versões anteriores que assumiam `entry` público em `/apps/<plugin>/remoteEntry.js` ou `base: "/"` como regra obrigatória.

Ele deve ser utilizado como referência oficial para todos os novos plugins federados da DELPI Central.

