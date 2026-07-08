import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";

import type { AppProps } from "../../App";
import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { CATALOG_CREATE } from "../../constants/catalogRoutes";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { buildConfiguracoesSectionPath } from "../../ui/configuracoes/configuracoesWorkspaceNav";
import {
  deleteFilial,
  fetchFiliais,
  fetchOptions,
  type Filial,
  type OptionsData,
} from "../../data/api/transformometroApi";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { HelpTooltip } from "@delpi/plugin-ui";
import { TableRowActions } from "../../components/ui/TableRowActions";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { renderTableStatus } from "../../utils/tablePresentation";
import { buildFilialPath } from "../../utils/routeParser";

const C = TM_HELP_TOOLTIPS.columns;
const F = TM_HELP_TOOLTIPS.filiais;

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  embedded?: boolean;
};

export function FiliaisPage({ getAccessToken, pathname, onNavigate, embedded = false }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<Filial[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [includeInactive, setIncludeInactive] = useState(true);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchFiliais(getAccessToken, includeInactive),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar unidades");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, includeInactive]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleDelete(filial: Filial) {
    const confirmed = await confirm({
      title: "Excluir unidade",
      message: `Excluir unidade ${filial.codigo_filial ?? filial.filial_id} — ${filial.nome_filial}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) {
      return;
    }
    setError(null);
    try {
      await deleteFilial(filial.filial_id, getAccessToken);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir unidade");
    }
  }

  const columns: DataTableColumn<Filial>[] = [
    {
      key: "codigo_filial",
      header: "Código",
      headerHint: C.codigoTotvs,
      sortable: true,
      sortValue: (row) => row.codigo_filial ?? row.filial_id,
      render: (row) => row.codigo_filial ?? row.filial_id,
    },
    {
      key: "nome_filial",
      header: "Unidade",
      headerHint: C.unidade,
      sortable: true,
      className: "ds-table__col--wide",
      sortValue: (row) => row.nome_filial,
      render: (row) => <strong>{row.nome_filial}</strong>,
    },
    {
      key: "status_filial",
      header: "Status",
      headerHint: C.status,
      sortable: true,
      className: "ds-table__col--status",
      render: (row) => renderTableStatus(row.status_filial),
    },
    {
      key: "acoes",
      header: "Ações",
      headerHint: C.acoes,
      className: "ds-table__actions-col",
      render: (row) => (
        <TableRowActions>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={(event) => {
              event.stopPropagation();
              onNavigate(buildFilialPath(row.filial_id));
            }}
          >
            Abrir
          </button>
          <button
            type="button"
            className="ds-ghost-btn ds-ghost-btn--danger"
            onClick={(event) => {
              event.stopPropagation();
              void handleDelete(row);
            }}
          >
            Excluir
          </button>
        </TableRowActions>
      ),
    },
  ];

  const catalogFetchProgress = useTrackedSingleFetchProgress(loading && !options);
  const catalogLoadingProgress = useLoadingProgress(loading && !options, catalogFetchProgress);

  if (loading && !options) {
    const loader = (
      <LoadingActivityCard
        title="Carregando unidades"
        description="Catálogo de unidades operacionais."
        progressPercent={catalogLoadingProgress}
      />
    );
    if (embedded) return loader;
    return <TransformometroShell>{loader}</TransformometroShell>;
  }

  const pageBody = (
    <>
      <StatusAlerts
        error={error}
        loading={loading}
        hasData={items.length > 0}
        onRetry={() => void load()}
      />

      <p className="ds-hint">
        Unidades ativas aparecem nos formulários de{" "}
        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => onNavigate(buildConfiguracoesSectionPath("departamentos"))}
        >
          Departamentos
        </button>{" "}
        e{" "}
        <button
          type="button"
          className="ds-ghost-btn"
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
        >
          Processos
        </button>
        .
      </p>

      <DataTableSection
        title="Catálogo de unidades"
        filters={
          <label className="ds-check-label">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            <span className="tm-field__label">
              Incluir unidades inativas
              <HelpTooltip content={F.incluirInativas} ariaLabel="Ajuda: Incluir unidades inativas" />
            </span>
          </label>
        }
        columns={columns}
        rows={items}
        rowKey={(row) => row.filial_id}
        loading={loading}
        refreshing={refreshing}
        hideSearch
        pageSize={15}
        emptyMessage="Nenhuma unidade cadastrada. Use Nova unidade para incluir."
        onRowClick={(row) => onNavigate(buildFilialPath(row.filial_id))}
        footer={<p className="ds-hint">{items.length} registro(s)</p>}
      />
    </>
  );

  if (embedded) return pageBody;

  return (
    <TransformometroShell>
      <PageHeader
        title="Unidades"
        subtitle="Cadastro de unidades — base para instâncias, departamentos e escopo do dashboard"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.filiais}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="ds-primary-btn"
            onClick={() => onNavigate(buildFilialPath(CATALOG_CREATE.filial))}
          >
            <Plus size={16} />
            Nova unidade
          </button>
        }
      />
      {pageBody}
    </TransformometroShell>
  );
}
