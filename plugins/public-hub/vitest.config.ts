import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Testes de componente/hook (P3+) usam vitest+jsdom em arquivos *.test.tsx.
// Os testes puros existentes seguem em node:test nos arquivos *.test.ts —
// o glob .tsx evita colisão entre os dois runners.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    include: ["src/**/*.test.tsx"],
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
  },
});
