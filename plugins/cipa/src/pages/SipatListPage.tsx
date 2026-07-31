import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  BackLink,
  DataTable,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { Copy, Plus, RefreshCw, Trash2 } from "lucide-react";

import {
  cloneSipatSurvey,
  deleteSipatSurvey,
  listSipatSurveys,
  type SipatSurvey,
} from "../api/cipaApi";
import { SIPAT_STATUS_LABELS, UNIT_LABELS } from "../constants/labels";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import { canUnit, type CipaAccess, type CipaUnitCode } from "../security/cipaAccess";
import { CipaConfirmModal } from "../ui/CipaConfirmModal";
import {
  CipaContentCard,
  CipaPageHeader,
  CipaPageNotices,
  CipaStateBanner,
  CipaStateBox,
} from "../ui/cipaUi";
import {
  cipaDataTableClassNames,
  cipaDataTableLabels,
  cipaStatusBadgeClassNames,
} from "../ui/cipaUiContracts";

type Props = {
  unitCode: CipaUnitCode;
  access: CipaAccess | null;
};

function statusVariant(status: string): "neutral" | "info" | "success" | "warning" | "danger" {
  if (status === "published") return "success";
  if (status === "closed") return "neutral";
  if (status === "draft") return "warning";
  return "info";
}

export function SipatListPage({ unitCode, access }: Props) {
  const [items, setItems] = useState<SipatSurvey[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cloningId, setCloningId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<SipatSurvey | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const canManage = canUnit(access, unitCode, "sipat_manage");

  const totals = useMemo(() => {
    const responses = items.reduce((sum, item) => sum + (item.response_count || 0), 0);
    const published = items.filter((item) => item.status === "published").length;
    return { responses, published, total: items.length };
  }, [items]);

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    listSipatSurveys(unitCode, controller.signal)
      .then((data) => {
        setItems(data.items);
        setError(null);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Erro ao listar pesquisas SIPAT.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  };

  useEffect(() => load(), [unitCode]);

  const cloneSurvey = useCallback(
    async (row: SipatSurvey) => {
      setCloningId(row.id);
      setError(null);
      try {
        const detail = await cloneSipatSurvey(row.id);
        navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/${detail.survey.id}/edit`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao clonar pesquisa.");
      } finally {
        setCloningId(null);
      }
    },
    [unitCode],
  );

  const confirmDelete = async () => {
    if (!deleting) return;
    setDeleteBusy(true);
    setError(null);
    try {
      await deleteSipatSurvey(deleting.id);
      setDeleting(null);
      void load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao excluir pesquisa.");
    } finally {
      setDeleteBusy(false);
    }
  };

  const columns = useMemo(
    () =>
      [
        {
          key: "title",
          header: "Pesquisa",
          mobileLabel: "Pesquisa",
          render: (row) => (
            <div className="cipa-sipat-table-title">
              <strong>{row.title}</strong>
              {row.description ? <span>{row.description}</span> : null}
            </div>
          ),
        },
        {
          key: "status",
          header: "Status",
          mobileLabel: "Status",
          render: (row) => (
            <StatusBadge
              classNames={cipaStatusBadgeClassNames}
              label={SIPAT_STATUS_LABELS[row.status] || row.status}
              variant={statusVariant(row.status)}
            />
          ),
        },
        {
          key: "responses",
          header: "Respostas",
          mobileLabel: "Respostas",
          render: (row) => (
            <span className="cipa-sipat-table-metric">{row.response_count ?? 0}</span>
          ),
        },
        {
          key: "actions",
          header: "Ações",
          mobileLabel: "Ações",
          interactive: true,
          render: (row) => (
            <div className="cipa-members-actions">
              <ActionButton
                onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/${row.id}`)}
              >
                Abrir
              </ActionButton>
              {canManage ? (
                <>
                  <ActionButton
                    variant="ghost"
                    disabled={cloningId === row.id || deleteBusy}
                    onClick={() => void cloneSurvey(row)}
                  >
                    <Copy size={14} /> {cloningId === row.id ? "Clonando…" : "Clonar"}
                  </ActionButton>
                  <ActionButton variant="ghost" onClick={() => setDeleting(row)}>
                    <Trash2 size={14} /> Excluir
                  </ActionButton>
                </>
              ) : null}
            </div>
          ),
        },
      ] satisfies DataTableColumn<SipatSurvey>[],
    [unitCode, canManage, cloningId, cloneSurvey, deleteBusy],
  );

  return (
    <div className="cipa-page-stack cipa-sipat">
      <CipaPageHeader
        nav={
          <BackLink
            variant="prominent"
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}`)}
          >
            Atas
          </BackLink>
        }
        title={`SIPAT — ${UNIT_LABELS[unitCode]}`}
        subtitle="Pesquisas anônimas com link público e QR Code"
        actions={
          <>
            <ActionButton variant="ghost" onClick={() => void load()}>
              <RefreshCw size={16} /> Atualizar
            </ActionButton>
            {canManage ? (
              <ActionButton
                variant="primary"
                onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/new`)}
              >
                <Plus size={16} /> Nova pesquisa
              </ActionButton>
            ) : null}
          </>
        }
      />

      <CipaPageNotices>
        {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}
      </CipaPageNotices>

      {!loading && items.length > 0 ? (
        <section className="cipa-sipat-kpis" aria-label="Resumo">
          <article className="cipa-sipat-kpi">
            <span className="cipa-sipat-kpi__label">Pesquisas</span>
            <strong className="cipa-sipat-kpi__value">{totals.total}</strong>
          </article>
          <article className="cipa-sipat-kpi">
            <span className="cipa-sipat-kpi__label">Publicadas</span>
            <strong className="cipa-sipat-kpi__value">{totals.published}</strong>
          </article>
          <article className="cipa-sipat-kpi">
            <span className="cipa-sipat-kpi__label">Respostas</span>
            <strong className="cipa-sipat-kpi__value">{totals.responses}</strong>
          </article>
        </section>
      ) : null}

      <CipaContentCard>
        {loading ? (
          <CipaStateBox>Carregando pesquisas…</CipaStateBox>
        ) : items.length === 0 ? (
          <CipaStateBox>
            Nenhuma pesquisa SIPAT nesta unidade.
            {canManage ? " Use «Nova pesquisa» ou um template no wizard." : ""}
          </CipaStateBox>
        ) : (
          <DataTable
            rows={items}
            columns={columns}
            rowKey={(row) => row.id}
            layout="embedded"
            classNames={cipaDataTableClassNames}
            labels={cipaDataTableLabels}
          />
        )}
      </CipaContentCard>

      <CipaConfirmModal
        open={Boolean(deleting)}
        title="Excluir pesquisa SIPAT"
        message={
          deleting ? (
            <>
              Excluir <strong>{deleting.title}</strong>? O link público deixa de
              funcionar
              {deleting.response_count
                ? ` e as ${deleting.response_count} resposta${deleting.response_count === 1 ? "" : "s"} deixam de aparecer na lista`
                : ""}
              .
            </>
          ) : (
            ""
          )
        }
        confirmLabel="Excluir"
        busy={deleteBusy}
        variant="danger"
        onConfirm={() => void confirmDelete()}
        onCancel={() => {
          if (!deleteBusy) setDeleting(null);
        }}
      />
    </div>
  );
}
