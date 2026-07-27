import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  ConfirmModalPanel,
  HelpTooltip,
  useConfirmDialogController,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";
import { Eye, Plus, Trash2 } from "lucide-react";

import {
  deleteLmpNonconformity,
  fetchLmpNonconformities,
} from "../api/lmpNonconformityApi";
import { DataTableSection } from "../components/DataTableSection";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../components/dashboardFiltersUi";
import { LmpsNav } from "../components/LmpsNav";
import type { DataTableColumn } from "../components/dataTableUi";
import {
  HostContainedDialog,
  LMPS_CONFIRM_CLASSES,
  StatusBadge,
} from "../components/ncUi";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildNcDetailPath,
  LMPS_ROUTES,
} from "../constants/routes";
import type { LmpNonconformity } from "../types/lmpNonconformity";
import {
  LMP_NC_STATUS_OPTIONS,
  lmpNcStatusLabel,
} from "../types/lmpNonconformity";
import { readLmpsFilters } from "../utils/filterUrl";
import {
  formatDisplayDate,
  formatDisplayDateOnly,
  productsSummary,
} from "../utils/ncFormModel";
import { navigateLmps } from "../utils/navigation";

const NC_HELP = LMPS_HELP_TOOLTIPS.nonconformities;

type Props = {
  pathname: string;
  canWrite?: boolean;
};

function statusVariant(status: string): StatusBadgeVariant {
  if (status === "done") return "success";
  if (status === "in_progress") return "info";
  return "warning";
}

export function NonconformitiesPage({ pathname, canWrite = true }: Props) {
  const filterState = readLmpsFilters();
  const [items, setItems] = useState<LmpNonconformity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [saleNumber, setSaleNumber] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [productCode, setProductCode] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [pendingDelete, setPendingDelete] = useState<LmpNonconformity | null>(
    null,
  );
  const { confirm, pending, confirmPending, cancelPending } =
    useConfirmDialogController();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformities({
        status: status || undefined,
        sale_number: saleNumber || undefined,
        customer_name: customerName || undefined,
        product_code: productCode || undefined,
        start_date: dateStart || undefined,
        end_date: dateEnd || undefined,
        page,
        page_size: 50,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar NCs.");
    } finally {
      setLoading(false);
    }
  }, [status, saleNumber, customerName, productCode, dateStart, dateEnd, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const openDetail = (record: LmpNonconformity) => {
    navigateLmps(buildNcDetailPath(record.id));
  };

  const requestDelete = async (record: LmpNonconformity) => {
    setPendingDelete(record);
    const ok = await confirm({
      title: "Excluir não conformidade",
      message: "Excluir esta não conformidade? Esta ação não pode ser desfeita.",
      confirmLabel: "Excluir",
      variant: "danger",
    });
    setPendingDelete(null);
    if (!ok) return;
    try {
      await deleteLmpNonconformity(record.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir.");
    }
  };

  const columns = useMemo<DataTableColumn<LmpNonconformity>[]>(() => {
    const cols: DataTableColumn<LmpNonconformity>[] = [
      {
        key: "registered_at",
        header: "Registro",
        headerHint: NC_HELP.table.registeredAt,
        render: (row) => formatDisplayDate(row.registered_at),
      },
      {
        key: "sale_number",
        header: "OV / LMP",
        headerHint: NC_HELP.table.saleNumber,
        render: (row) => row.sale_number || "—",
      },
      {
        key: "customer_name",
        header: "Cliente",
        headerHint: NC_HELP.table.customer,
        render: (row) => row.customer_name || "—",
      },
      {
        key: "launch_date",
        header: "Lançamento",
        headerHint: NC_HELP.table.launchDate,
        render: (row) => formatDisplayDateOnly(row.launch_date),
      },
      {
        key: "last_revision_date",
        header: "Últ. revisão",
        headerHint: NC_HELP.table.lastRevisionDate,
        render: (row) => formatDisplayDateOnly(row.last_revision_date),
      },
      {
        key: "executed_by",
        header: "Executou",
        headerHint: NC_HELP.table.executedBy,
        render: (row) => row.executed_by || "—",
      },
      {
        key: "released_by",
        header: "Liberou",
        headerHint: NC_HELP.table.releasedBy,
        render: (row) => row.released_by || "—",
      },
      {
        key: "products",
        header: "Produtos",
        headerHint: NC_HELP.table.products,
        render: (row) => productsSummary(row),
      },
      {
        key: "defect_description",
        header: "Problema",
        headerHint: NC_HELP.table.problem,
        render: (row) => {
          const text = (row.defect_description || "").trim();
          if (!text) return "—";
          return text.length > 48 ? `${text.slice(0, 48)}…` : text;
        },
      },
      {
        key: "status",
        header: "Status",
        headerHint: NC_HELP.table.status,
        render: (row) => (
          <StatusBadge
            label={lmpNcStatusLabel(String(row.status))}
            variant={statusVariant(String(row.status))}
          />
        ),
      },
      {
        key: "actions",
        header: "Ações",
        headerHint: NC_HELP.table.actions,
        render: (row) => (
          <div
            className="lmps-nc-actions"
            onClick={(e) => e.stopPropagation()}
            onKeyDown={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              className="lmps-ghost-btn lmps-btn--sm"
              onClick={() => openDetail(row)}
              aria-label="Abrir detalhe"
            >
              <Eye size={14} />
            </button>
            {canWrite ? (
              <button
                type="button"
                className="lmps-ghost-btn lmps-btn--sm"
                onClick={() => void requestDelete(row)}
                aria-label="Excluir"
              >
                <Trash2 size={14} />
              </button>
            ) : null}
          </div>
        ),
      },
    ];
    return cols;
  }, [canWrite]);

  return (
    <div className="dashboard-page dashboard-lmps">
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <div className="lmps-page-header__title-row">
            <h1>Acompanhamento de LMPs</h1>
          </div>
          <span className="lmps-page-subtitle lmps-page-subtitle--with-help">
            Registro de não conformidades de engenharia
            <HelpTooltip
              content={NC_HELP.pageSubtitle}
              ariaLabel="Ajuda: escopo do registro de NCs"
              className="lmps-page-subtitle__help"
            />
          </span>
          <LmpsNav currentPath={pathname} filterState={filterState} />
        </div>
        <div className="lmps-header-actions">
          {canWrite ? (
            <div className="lmps-header-action">
              <ActionButton
                type="button"
                variant="primary"
                onClick={() => navigateLmps(LMPS_ROUTES.nonconformityNew)}
              >
                <Plus size={16} />
                Nova não conformidade
              </ActionButton>
              <HelpTooltip
                content={NC_HELP.newButton}
                ariaLabel="Ajuda: nova não conformidade"
                className="lmps-header-action__help"
              />
            </div>
          ) : null}
        </div>
      </header>

      <FiltersRow>
        <FilterSelectField
          id="lmps-nc-status"
          label="Status"
          hint={NC_HELP.filters.status}
          value={status}
          onChange={(v) => {
            setPage(1);
            setStatus(v);
          }}
          placeholderOption="Todos"
          options={LMP_NC_STATUS_OPTIONS.map((o) => ({
            value: o.value,
            label: o.label,
          }))}
        />
        <FilterInputField
          label="OV / LMP"
          hint={NC_HELP.filters.saleNumber}
          type="text"
          value={saleNumber}
          onChange={(v) => {
            setPage(1);
            setSaleNumber(v);
          }}
        />
        <FilterInputField
          label="Cliente"
          hint={NC_HELP.filters.customer}
          type="text"
          value={customerName}
          onChange={(v) => {
            setPage(1);
            setCustomerName(v);
          }}
        />
        <FilterInputField
          label="Produto"
          hint={NC_HELP.filters.product}
          type="text"
          value={productCode}
          onChange={(v) => {
            setPage(1);
            setProductCode(v);
          }}
        />
        <FilterInputField
          label="Data início"
          hint={NC_HELP.filters.dateStart}
          type="date"
          value={dateStart}
          onChange={(v) => {
            setPage(1);
            setDateStart(v);
          }}
        />
        <FilterInputField
          label="Data fim"
          hint={NC_HELP.filters.dateEnd}
          type="date"
          value={dateEnd}
          onChange={(v) => {
            setPage(1);
            setDateEnd(v);
          }}
        />
      </FiltersRow>

      {error ? (
        <div className="lmps-refreshing-banner" role="alert">
          {error}
        </div>
      ) : null}

      <DataTableSection
        title="Não conformidades"
        titleHint={NC_HELP.table.section}
        searchHint={NC_HELP.table.search}
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={loading}
        emptyMessage="Nenhuma não conformidade encontrada."
        onRowClick={openDetail}
        serverPagination={{
          page,
          pageSize: 50,
          total,
          onPageChange: setPage,
        }}
      />

      <HostContainedDialog
        open={pending !== null}
        onClose={cancelPending}
        title={pending?.title || "Confirmar"}
      >
        <ConfirmModalPanel
          message={
            pending?.message ??
            (pendingDelete
              ? "Excluir esta não conformidade?"
              : "Confirmar ação?")
          }
          confirmLabel={pending?.confirmLabel}
          cancelLabel={pending?.cancelLabel ?? "Cancelar"}
          variant={pending?.variant}
          onConfirm={confirmPending}
          onCancel={cancelPending}
          classNames={LMPS_CONFIRM_CLASSES}
        />
      </HostContainedDialog>
    </div>
  );
}
