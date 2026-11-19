import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/* Testes de composição dos consumidores reais (ex.: PrcCreatePage de
 * plugins/engineering) importam o kit pelo nome público do pacote —
 * resolvido aqui para a fonte local, sem remote de federação. React
 * também é deduplicado: módulos de outro plugin resolveriam a cópia
 * do próprio node_modules e quebrariam o dispatcher compartilhado. */
const selfIndex = fileURLToPath(new URL("./src/index.ts", import.meta.url));
const selfReact = fileURLToPath(
  new URL("./node_modules/react", import.meta.url),
);
const selfReactDom = fileURLToPath(
  new URL("./node_modules/react-dom", import.meta.url),
);

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: [
      { find: "@delpi/plugin-ui/index", replacement: selfIndex },
      { find: "@delpi/plugin-ui", replacement: selfIndex },
      { find: /^react\/jsx-runtime$/, replacement: `${selfReact}/jsx-runtime.js` },
      { find: /^react\/jsx-dev-runtime$/, replacement: `${selfReact}/jsx-dev-runtime.js` },
      { find: /^react-dom\/client$/, replacement: `${selfReactDom}/client.js` },
      { find: /^react-dom$/, replacement: selfReactDom },
      { find: /^react$/, replacement: selfReact },
    ],
  },
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
