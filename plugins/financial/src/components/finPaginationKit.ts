import {
  createDashboardPaginationKit,
  TABLE_PAGE_SIZE_OPTIONS,
  type PageJumpValidationReason,
} from "@delpi/plugin-ui/index";

import { copy } from "../content/copy";

const kit = createDashboardPaginationKit({
  prefix: "fin",
  hints: {
    pageSize: "Define quantos registros a tabela solicita por página.",
    previous: "Volta para a página anterior.",
    next: "Avança para a próxima página.",
    info: "Intervalo de registros exibidos nesta página.",
    jump: "Digite o número da página e pressione Enter.",
  },
  tablePageSizeLabels: {
    label: copy.pagination.pageSizeLabel,
    selectAriaLabel: copy.pagination.pageSizeAria,
  },
  labels: {
    navigationAriaLabel: copy.pagination.navigationAriaLabel,
    pagesAriaLabel: copy.pagination.pagesAriaLabel,
    previous: copy.pagination.previous,
    next: copy.pagination.next,
    info: copy.pagination.info,
    jumpLabel: copy.pagination.jumpLabel,
    jumpInputAriaLabel: copy.pagination.jumpInputAriaLabel,
    jumpError: (reason: PageJumpValidationReason, totalPages: number) =>
      copy.pagination.jumpError(reason, totalPages),
  },
});

export const FinTablePagination = kit.Pagination;
export const FinTablePageSizeSelect = kit.TablePageSizeSelect;
export { TABLE_PAGE_SIZE_OPTIONS };
