import {
  createDashboardDataTableKit,
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
} from "@delpi/plugin-ui/index";
import { useEffect, useRef, useState } from "react";

import {
  CommercialLoadingCard,
  CommercialPagination,
  UI_PREFIX,
  cmDataTableLabels,
} from "./commercialUi";

const DEFAULT_TABLE_PAGE_SIZE = 20;

type RequestProgress = { completed: number; total: number };

function useTrackedSingleFetchProgress(fetching: boolean): RequestProgress {
  const [progress, setProgress] = useState<RequestProgress>({ completed: 0, total: 0 });
  const startedAt = useRef<number | null>(null);

  useEffect(() => {
    if (!fetching) {
      startedAt.current = null;
      setProgress({ completed: 0, total: 0 });
      return;
    }
    startedAt.current = Date.now();
    setProgress({ completed: 0, total: 1 });
    const timer = window.setInterval(() => {
      setProgress({ completed: 0, total: 1 });
    }, 400);
    return () => window.clearInterval(timer);
  }, [fetching]);

  return progress;
}

function useLoadingProgress(active: boolean, _progress: RequestProgress): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (!active) {
      setValue(0);
      return;
    }
    setValue(12);
    const timer = window.setInterval(() => {
      setValue((current) => Math.min(90, current + 8));
    }, 350);
    return () => window.clearInterval(timer);
  }, [active]);
  return value;
}

function jumpPageErrorMessage(reason: string, totalPages: number): string {
  switch (reason) {
    case "empty":
      return "Informe uma página.";
    case "invalid":
      return "Página inválida.";
    case "below_min":
      return "A página mínima é 1.";
    case "above_max":
      return `A página máxima é ${totalPages}.`;
    default:
      return "";
  }
}

const paginationKit = createDashboardPaginationKit({
  prefix: UI_PREFIX,
  labels: {
    navigationAriaLabel: "Paginação da tabela",
    pagesAriaLabel: "Páginas",
    previous: "Anterior",
    next: "Próxima",
    info: ({ rangeStart, rangeEnd, total, page, totalPages }) =>
      `Exibindo ${rangeStart}–${rangeEnd} de ${total} · Página ${page} de ${totalPages}`,
    jumpLabel: "Ir para",
    jumpInputAriaLabel: "Ir para página",
    jumpError: jumpPageErrorMessage,
  },
  tablePageSizeLabels: {
    label: "Itens por página",
    selectAriaLabel: "Quantidade de itens por página",
  },
});

const sectionLabels = {
  ...cmDataTableLabels,
  searchPlaceholder: "Buscar na tabela…",
  searchAriaLabel: "Filtrar registros da tabela",
  searchHelpAriaLabel: "Ajuda: busca na tabela",
  recordsCount: (total: number) => `${total.toLocaleString("pt-BR")} registro(s)`,
  refreshLoadingTitle: "Atualizando tabela",
  refreshLoadingDescription:
    "Mantendo os dados visíveis enquanto a consulta é aplicada.",
  initialLoadingTitle: "Carregando registros",
  initialLoadingDescription: "Aguarde enquanto os dados da tabela são obtidos.",
  titleHelpAriaLabel: (title: string) => `Ajuda: ${title}`,
};

const kit = createDashboardDataTableKit({
  prefix: UI_PREFIX,
  labels: sectionLabels,
  LoadingActivityCard: CommercialLoadingCard,
  Pagination: CommercialPagination,
  TablePageSizeSelect: paginationKit.TablePageSizeSelect,
  tablePageSizeOptions: TABLE_PAGE_SIZE_OPTIONS,
  useLoadingProgress,
  useTrackedSingleFetchProgress,
  defaultPageSize: DEFAULT_TABLE_PAGE_SIZE,
});

export const CommercialDataTableSection = kit.DataTableSection;
export { TABLE_PAGE_SIZE_OPTIONS };

export type {
  DashboardDataTableSectionProps as CommercialDataTableSectionProps,
  DataTableColumn,
} from "@delpi/plugin-ui/index";
