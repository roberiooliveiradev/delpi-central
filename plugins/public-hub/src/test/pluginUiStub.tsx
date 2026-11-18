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

// Exports do kit de formulário usados pela página da Pesquisa (P6).
// No-ops como os demais — o teste de integração usa o kit real por
// caminho de código-fonte (§14.10.4).
export function GuidedQuestionnaire() {
  return null;
}

export function QuestionnaireThemeScope({ children }: { children?: ReactNode }) {
  return children ?? null;
}

export function FormPageLayout({ children }: { children?: ReactNode }) {
  return children ?? null;
}

export function FormResultPanel() {
  return null;
}

export function FormLogo() {
  return null;
}

export function FormButton() {
  return null;
}
