/**
 * Tipagem mínima do jsdom para o comparador de round-trip (e2e/rt-compare.ts),
 * usado por testes adapter-level e pelo runner Playwright.
 *
 * Não instalar @types/jsdom: ele altera a resolução de tipos do
 * tsconfig.node.json (vite.config.ts) via `/// <reference types="vitest/config" />`
 * e quebra o typecheck dos plugins federation — efeito colateral verificado.
 * Este shim declara apenas o que o comparador usa.
 */
declare module "jsdom" {
  export class JSDOM {
    constructor(html?: string);
    readonly window: {
      DOMParser: typeof DOMParser;
    };
  }
}
