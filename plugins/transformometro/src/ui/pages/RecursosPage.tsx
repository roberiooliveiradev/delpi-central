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
import {
  deleteRecurso,
  fetchRecursos,
  type RecursoCompartilhado,
} from "../../data/api/transformometroApi";
import { labelBaseCompetencia, labelCriterioRateio, labelEscopoRecurso } from "../../utils/catalogLabels";
import { toDateInputValue } from "../../utils/dateInputs";
import { formatCurrency } from "../../utils/format";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { buildRecursoPath } from "../../utils/routeParser";
import { TableRowActions } from "../../components/ui/TableRowActions";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { renderTableStatus } from "../../utils/tablePresentation";
import { DS_GHOST_BTN, dsGhostBtn } from "../../components/ghostChrome";

const C = TM_HELP_TOOLTIPS.columns;

type Props = Pick<AppProps, "getAccessToken"> & {
  pathname?: string;
  onNavigate: (path: string) => void;
  embedded?: boolean;
};

export function RecursosPage({ getAccessToken, pathname, onNavigate, embedded = false }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<RecursoCompartilhado[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const list = await fetchRecursos(getAccessToken);
      setItems(list.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar recursos");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleDelete(r: RecursoCompartilhado) {
    const confirmed = await confirm({
      title: "Excluir recurso",
      message: `Excluir ${r.codigo_recurso} — ${r.nome_recurso}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteRecurso(r.recurso_compartilhado_id, getAccessToken);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir recurso");
    }
  }

  const columns: DataTableColumn<RecursoCompartilhado>[] = [
    {
      key: "codigo",
      header: "Código",
      headerHint: C.codigo,
      render: (r) => r.codigo_recurso,
      sortable: true,
      sortValue: (r) => r.codigo_recurso,
    },
    {
      key: "nome",
      header: "Nome",
      headerHint: C.nome,
      sortable: true,
      className: "ds-table__col--wide",
      sortValue: (r) => r.nome_recurso,
      render: (r) => (
        <>
          <strong>{r.nome_recurso}</strong>
          {r.fornecedor ? <span className="ds-table__sub"> · {r.fornecedor}</span> : null}
        </>
      ),
    },
    {
      key: "custo",
      header: "Custo/mês vigente",
      headerHint: C.custoMesVigente,
      sortable: true,
      className: "ds-table__col--numeric",
      sortValue: (r) => r.valor_total_recorrente,
      render: (r) => formatCurrency(r.valor_total_recorrente),
    },
    { key: "rateio", header: "Rateio", headerHint: C.rateio, render: (r) => labelCriterioRateio(r.criterio_rateio), sortable: true },
    {
      key: "escopo_recurso",
      header: "Escopo",
      headerHint: C.escopo,
      render: (r) => labelEscopoRecurso(r.escopo_recurso),
      sortable: true,
      sortValue: (r) => r.escopo_recurso ?? "empresa",
    },
    {
      key: "base_competencia",
      header: "Competência",
      headerHint: C.baseCompetencia,
      render: (r) => labelBaseCompetencia(r.base_competencia),
      sortable: true,
      sortValue: (r) => r.base_competencia ?? "mensal_cheio",
    },
    { key: "status", header: "Status", headerHint: C.status, className: "ds-table__col--status", render: (r) => renderTableStatus(r.status_recurso), sortable: true },
    {
      key: "vigencia",
      header: "Vigência do recurso",
      headerHint: C.vigenciaRecurso,
      sortable: true,
      render: (r) => (
        <>
          {toDateInputValue(r.data_inicio_vigencia) || "…"} → {toDateInputValue(r.data_fim_vigencia) || "…"}
        </>
      ),
    },
    {
      key: "acoes",
      header: "Ações",
      headerHint: C.acoes,
      className: "ds-table__actions-col",
      render: (r) => (
        <TableRowActions>
          <button
            type="button"
            className={DS_GHOST_BTN}
            onClick={(event) => {
              event.stopPropagation();
              onNavigate(buildRecursoPath(r.recurso_compartilhado_id));
            }}
          >
            Abrir
          </button>
          <button
            type="button"
            className={dsGhostBtn('danger')}
            onClick={(event) => {
              event.stopPropagation();
              void handleDelete(r);
            }}
          >
            Excluir
          </button>
        </TableRowActions>
      ),
    },
  ];

  const catalogFetchProgress = useTrackedSingleFetchProgress(loading && items.length === 0);
  const catalogLoadingProgress = useLoadingProgress(loading && items.length === 0, catalogFetchProgress);

  if (loading && items.length === 0) {
    const loader = (
      <LoadingActivityCard
        title="Carregando catálogo de recursos"
        description="Licenças, assinaturas e ferramentas compartilhadas."
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
        Recursos cadastrados aqui aparecem ao vincular em{" "}
        <button
          type="button"
          className={DS_GHOST_BTN}
          onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.processos)}
        >
          Processos → revisão → Recursos
        </button>
        . O custo mensal usado nos cálculos vem da tabela de vigências de custo.
      </p>

      <DataTableSection
        columnPreferencesKey="transformometro:RecursosPage:cat-logo-de-recursos:v1"
        title="Catálogo de recursos"
        columns={columns}
        rows={items}
        rowKey={(r) => r.recurso_compartilhado_id}
        loading={loading}
        refreshing={refreshing}
        searchPlaceholder="Código, nome, fornecedor…"
        getSearchText={(r) =>
          [
            r.codigo_recurso,
            r.nome_recurso,
            r.fornecedor,
            r.categoria_recurso,
            labelBaseCompetencia(r.base_competencia),
          ]
            .filter(Boolean)
            .join(" ")
        }
        onRowClick={(r) => onNavigate(buildRecursoPath(r.recurso_compartilhado_id))}
        emptyMessage="Nenhum recurso no catálogo. Cadastre licenças e ferramentas compartilhadas."
      />
    </>
  );

  if (embedded) return pageBody;

  return (
    <TransformometroShell>
      <PageHeader
        title="Recursos compartilhados"
        subtitle="Catálogo global — vincule às revisões em Processos para rateio no dashboard"
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.recursos}
        onNavigate={onNavigate}
        onRefresh={() => void load()}
        refreshing={refreshing}
        actions={
          <button
            type="button"
            className="ds-primary-btn"
            onClick={() => onNavigate(buildRecursoPath(CATALOG_CREATE.recurso))}
          >
            <Plus size={16} />
            Novo recurso
          </button>
        }
      />
      {pageBody}
    </TransformometroShell>
  );
}
