/**
 * Composição de hero das páginas da Central de Fechamento (doc 50).
 * Layout-only: recebe dados e handlers já resolvidos pela página — não
 * conhece HTTP, regras de negócio, autenticação ou cálculos.
 */
import type { ReactNode } from "react";

import type { PageHeroHighlight } from "@delpi/plugin-ui/index";

import { CfActionButton, CfPageHero } from "./controllershipFinanceUi";

const timeFormatter = new Intl.DateTimeFormat("pt-BR", {
  hour: "2-digit",
  minute: "2-digit",
});

export type ClosingHeroProps = {
  title: ReactNode;
  subtitle: string;
  "aria-label"?: string;
  /** Timestamp real da última consulta concluída; omitido quando nulo. */
  updatedAt: Date | null;
  /** Repete a consulta vigente (mesmos filtros) — nunca valida/submete. */
  onRefresh: () => void;
  refreshing?: boolean;
  /** KPIs reais do payload (PageHero highlights); `loading` por item. */
  highlights?: PageHeroHighlight[];
  /** Mensagem contextual persistente do hero (CfFeedbackMessage). */
  notice?: ReactNode;
  /** Área de filtros (form completo, já montado pela página). */
  filters: ReactNode;
  /** Restaura os defaults e dispara a consulta automática. */
  onClearFilters: () => void;
};

export function ClosingHero({
  title,
  subtitle,
  "aria-label": ariaLabel,
  updatedAt,
  onRefresh,
  refreshing = false,
  highlights,
  notice,
  filters,
  onClearFilters,
}: ClosingHeroProps) {
  return (
    <CfPageHero
      eyebrow="Central de Fechamento"
      title={title}
      description={subtitle}
      aria-label={ariaLabel}
      highlights={highlights}
      actions={
        <>
          {updatedAt ? (
            <span className="cf-hero-updated">
              Atualizado às {timeFormatter.format(updatedAt)}
            </span>
          ) : null}
          <CfActionButton
            variant="ghost"
            type="button"
            onClick={onRefresh}
            disabled={refreshing}
          >
            Atualizar
          </CfActionButton>
        </>
      }
    >
      {notice}
      <div className="cf-hero-filters">{filters}</div>
      <div className="cf-settlements-actions">
        <CfActionButton
          variant="ghost"
          type="button"
          onClick={onClearFilters}
        >
          Limpar filtros
        </CfActionButton>
      </div>
    </CfPageHero>
  );
}
