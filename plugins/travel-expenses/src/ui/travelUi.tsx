import {
  attachmentPreviewStripBemClasses,
  createContentCard,
  createDashboardAttachmentPreviewStrip,
  createDashboardEmptyState,
  createDashboardFileDropzone,
  createDashboardFiltersKit,
  createDashboardFormActions,
  createDashboardFormGrid,
  createDashboardLoadingState,
  createDashboardNavigationCard,
  createDashboardPageHeader,
  createDashboardSectionCard,
  createDashboardStateBanner,
  createDashboardStatusBadge,
  createFloatingNoticeStack,
  createHostContainedDrawerShell,
  createStateBoxPanel,
  createTimeline,
  emptyStateCardBemClasses,
  fileDropzoneBemClasses,
  formActionsBemClasses,
  formGridBemClasses,
  kpiCardBemClasses,
  loadingStateCardBemClasses,
  navigationCardBemClasses,
  pageHeaderTitleRowBemClasses,
  sectionCardPacBemClasses,
  stateBannerBemClasses,
  type StateBoxVariant,
} from "@delpi/plugin-ui/index";
import { AlertTriangle, FileQuestion, Loader2 } from "lucide-react";

const PREFIX = "te";

export const TravelPageHeader = createDashboardPageHeader({
  layout: "titleRow",
  classNames: pageHeaderTitleRowBemClasses(PREFIX),
  labels: { refresh: "Atualizar", refreshing: "Atualizando…" },
});

export const TravelSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PREFIX),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});

export const TravelContentCard = createContentCard(PREFIX, { titleLevel: 2 });

export const TravelFormGrid = createDashboardFormGrid({
  classNames: formGridBemClasses(PREFIX),
});

export const TravelStatusBadge = createDashboardStatusBadge({ prefix: PREFIX });

export const TravelNavigationCard = createDashboardNavigationCard({
  classNames: navigationCardBemClasses(PREFIX),
});

export const TravelAttachmentStrip = createDashboardAttachmentPreviewStrip({
  classNames: attachmentPreviewStripBemClasses(PREFIX),
  labels: {
    empty: "Nenhum cupom anexado.",
    openAriaLabel: (fileName) => `Abrir ${fileName}`,
    removeAriaLabel: (fileName) => `Remover ${fileName}`,
  },
});

export const TravelFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(PREFIX),
});

export const travelKpiClassNames = kpiCardBemClasses(PREFIX);
export const travelKpiLabels = { goalPrefix: "Meta", iddScorePrefix: "IDD", badgesStatus: "Status" };

const filtersKit = createDashboardFiltersKit({
  prefix: PREFIX,
  labels: { filtersAriaLabel: "Filtros de prestações" },
  portalScopeClassName: "dashboard-travel-expenses",
});

export const TravelFiltersRow = filtersKit.FiltersRow;
export const TravelFilterInputField = filtersKit.FilterInputField;
export const TravelFilterSelectField = filtersKit.FilterSelectField;

export const TravelStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PREFIX),
});

export const TravelFloatingNotices = createFloatingNoticeStack({
  prefix: PREFIX,
  portalScopeClassName: "dashboard-travel-expenses",
});

export function TravelPageNotices({
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
    <TravelFloatingNotices
      items={[
        ...(error ? [{ id: "page-error", message: error, variant: "error" as const }] : []),
        ...(success ? [{ id: "page-success", message: success, variant: "success" as const }] : []),
      ]}
      onDismiss={(id) => {
        if (id === "page-error") onDismissError?.();
        else onDismissSuccess?.();
      }}
    />
  );
}

export const TravelEmptyState = createDashboardEmptyState({
  classNames: emptyStateCardBemClasses(PREFIX),
  defaultMessage: "Nenhuma prestação encontrada.",
});

export const TravelLoadingState = createDashboardLoadingState({
  classNames: loadingStateCardBemClasses(PREFIX),
  defaultMessage: "Carregando…",
});

export const TravelTimeline = createTimeline({ prefix: PREFIX });

export const TravelStateBox = createStateBoxPanel({
  prefix: PREFIX,
  renderIcon: (variant: StateBoxVariant) => {
    if (variant === "error") return <AlertTriangle size={22} />;
    if (variant === "empty") return <FileQuestion size={22} />;
    return <Loader2 size={22} />;
  },
});

export const TravelFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(PREFIX),
  labels: {
    title: "Solte o cupom aqui",
    hint: "JPEG, PNG, WebP ou PDF",
  },
});

export const TravelDrawer = createHostContainedDrawerShell({
  prefix: PREFIX,
  portalScopeClassName: "dashboard-travel-expenses",
});
