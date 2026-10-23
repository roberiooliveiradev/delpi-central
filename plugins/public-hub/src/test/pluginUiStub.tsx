/**
 * Stub de teste para o remote `@delpi/plugin-ui` (Module Federation).
 * Em vitest não existe remote — os componentes viram no-ops porque os
 * testes de production-control não dependem da renderização interna deles.
 */
import type { ReactNode } from "react";

export function ConfigurableSeriesChart() {
  return null;
}

export function LucideIconByName() {
  return null;
}

export function ScreenLoading({ children }: { children?: ReactNode }) {
  return children ?? null;
}
