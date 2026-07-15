import { useCallback, useEffect, useMemo, useState } from "react";
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
import {
  deleteSetor,
  fetchOptions,
  fetchSetores,
  type OptionsData,
  type Setor,
} from "../../data/api/transformometroApi";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptionsFromItems } from "../../components/ui/selectTypes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { buildConfiguracoesSectionPath } from "../../ui/configuracoes/configuracoesWorkspaceNav";
import { buildSetorPath } from "../../utils/routeParser";
import { TableRowActions } from "../../components/ui/TableRowActions";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { renderTableStatus } from "../../utils/tablePresentation";
import { DS_GHOST_BTN, dsGhostBtn } from "../../components/ghostChrome";
import { DS_FILTERS_ROW } from "../../components/filterChrome";

const C = TM_HELP_TOOLTIPS.columns;
const S = TM_HELP_TOOLTIPS.setores;

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  embedded?: boolean;
};

export function SetoresPage({ getAccessToken, pathname, onNavigate, embedded = false }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<Setor[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filialFilter, setFilialFilter] = useState("");

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchSetores(getAccessToken, filialFilter || undefined),
        fetchOptions(getAccessToken),
      ]);
      setItems(list.items);
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar departamentos");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filialFilter, getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const filialLabels = useMemo(() => {
    const map = new Map((options?.filiais ?? []).map((filial) => [filial.id, filial.label]));
    return map;
  }, [options?.filiais]);

  async function handleDelete(setor: Setor) {
    const confirmed = await confirm({
      title: "Excluir departamento",
      message: `Excluir departamento ${setor.codigo_setor ?? setor.setor_id} — ${setor.nome_setor}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteSetor(setor.setor_id, getAccessToken);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir departamento");
    }
  }

  const columns: DataTableColumn<Setor>[] = [
    {
      key: "codigo_setor",
      header: "Código",
      headerHint: C.codigo,
      sortable: true,
      sortValue: (row) => row.codigo_setor ?? row.setor_id,
      render: (row) => row.codigo_setor ?? row.setor_id,
    },
    {
      key: "nome_setor",
      header: "Departamento",
      headerHint: C.setor,
      sortable: true,
      className: "ds-table__col--wide",
      sortValue: (row) => row.nome_setor,
      render: (row) => <strong>{row.nome_setor}</strong>,
    },
    {
      key: "filiais",
      header: "Unidades",
      headerHint: C.unidades,
      render: (row) =>
        (row.filiais ?? [])
          .map((filialId) => filialLabels.get(filialId) ?? "—")
          .join(", ") || "—",
    },
    {
      key: "status_setor",
      header: "Status",
      headerHint: C.status,
      sortable: true,
      className: "ds-table__col--status",
      render: (row) => renderTableStatus(row.status_setor),
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
            className={DS_GHOST_BTN}
            onClick={(event) => {
              event.stopPropagation();
              onNavigate(buildSetorPath(row.setor_id));
            }}
          >
            Abrir
          </button>
          <button
            type="button"
            className={dsGhostBtn('danger')}
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
        title="Carregando departamentos"
        description="Catálogo de departamentos vinculados às unidades."
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
        Departamentos ativos e vinculados à unidade aparecem no formulário de{" "}
        <button
          type="button"
          className={DS_GHOST_BTN}
          onClick={() => onNavigate(buildConfiguracoesSectionPath("unidades"))}
        >
          Unidades
        </button>
        {" "}e{" "}
        <button
          type="button"
          className={DS_GHOST_BTN}
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
        >
          Processos
        </button>
        .
      </p>

      <DataTableSection
        title="Catálogo de departamentos"
        filters={
          <div className={DS_FILTERS_ROW}>
            <SelectField
              id="tm-setor-list-filial"
              label="Unidade"
              hint={S.filtroUnidade}
              value={filialFilter}
              onChange={setFilialFilter}
              allowEmpty
              emptyLabel="Todas"
              options={mapSelectOptionsFromItems(
                options?.filiais ?? [],
                (filial) => filial.id,
                (filial) => filial.label
              )}
            />
          </div>
        }
        columns={columns}
        rows={items}
        rowKey={(row) => row.setor_id}
        loading={loading}
        refreshing={refreshing}
        hideSearch
        pageSize={15}
        emptyMessage="Nenhum departamento cadastrado. Use Novo departamento para incluir."
        onRowClick={(row) => onNavigate(buildSetorPath(row.setor_id))}
        footer={
          <p className="ds-hint">
            {items.length} registro(s)
            {filialFilter ? ` · filtrados para unidade ${filialLabels.get(filialFilter) ?? filialFilter}` : ""}
          </p>
        }
      />
    </>
  );

  if (embedded) return pageBody;

  return (
    <TransformometroShell>
      <PageHeader
        title="Departamentos"
        subtitle="Cadastro de departamentos e vínculo com unidades — usado nos processos"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.setores}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="ds-primary-btn"
            onClick={() => onNavigate(buildSetorPath(CATALOG_CREATE.setor))}
          >
            <Plus size={16} />
            Novo departamento
          </button>
        }
      />
      {pageBody}
    </TransformometroShell>
  );
}
