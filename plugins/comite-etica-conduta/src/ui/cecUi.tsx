import {
  createContentCard,
  createDashboardEmptyState,
  createDashboardFormActions,
  createDashboardFiltersKit,
  createDashboardLoadingState,
  createDashboardNavigationCard,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardStateBanner,
  createFloatingNoticeStack,
  createStateBoxPanel,
  createTimeline,
  emptyStateCardBemClasses,
  formActionsBemClasses,
  loadingStateCardBemClasses,
  navigationCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  stateBannerBemClasses,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

const PREFIX = "comite-etica-conduta";

export const ComiteEticaPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(PREFIX),
  labels: {
    refresh: "Atualizar",
    refreshing: "Atualizando…",
  },
});

export const ComiteEticaSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: {
    titleHelpAriaLabel: (title) => `Ajuda: ${title}`,
  },
});

export const ComiteEticaContentCard = createContentCard(PREFIX, { titleLevel: 2 });

export const ComiteEticaFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(PREFIX),
});

export const ComiteEticaNavigationCard = createDashboardNavigationCard({
  classNames: navigationCardBemClasses(PREFIX),
});

const cecFiltersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: {
    filtersAriaLabel: "Filtros de atas",
  },
  portalScopeClassName: "dashboard-comite-etica-conduta",
});

export const ComiteEticaFiltersRow = cecFiltersKit.FiltersRow;
export const ComiteEticaFilterInputField = cecFiltersKit.FilterInputField;
export const ComiteEticaFilterSelectField = cecFiltersKit.FilterSelectField;

export const ComiteEticaStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PREFIX),
});

export const ComiteEticaFloatingNotices = createFloatingNoticeStack({
  prefix: PREFIX,
  portalScopeClassName: "dashboard-comite-etica-conduta",
});

/** Cards flutuantes para erro/sucesso correntes da página (dismiss limpa o estado). */
export function ComiteEticaPageNotices({
  error,
  success,
  onDismissError,
  onDismissSuccess,
}: {
  error?: string | null;
  success?: string | null;
  onDismissError?: () => void;
  onDismissSuccess?: () => void;
}) {
  return (
    <ComiteEticaFloatingNotices
      items={[
        ...(error
          ? [{ id: "page-error", message: error, variant: "error" as const }]
          : []),
        ...(success
          ? [{ id: "page-success", message: success, variant: "success" as const }]
          : []),
      ]}
      onDismiss={(id) => {
        if (id === "page-error") onDismissError?.();
        else onDismissSuccess?.();
      }}
    />
  );
}

export const ComiteEticaEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(PREFIX),
  defaultMessage: "Nenhum item encontrado.",
});

export const ComiteEticaLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(PREFIX),
  defaultMessage: "Carregando…",
});

export const ComiteEticaTimeline = createTimeline({ prefix: PREFIX });

export const ComiteEticaStateBox = createStateBoxPanel({
  prefix: PREFIX,
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <FileQuestion size={22} />;
    return <Loader2 size={22} />;
  },
});
