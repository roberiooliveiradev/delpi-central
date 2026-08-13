import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  ActionButton,
  BackLink,
  DataTable,
  DocumentReaderToolbar,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import {
  Download,
  FilePlus2,
  PenLine,
  Pencil,
  Trash2,
} from "lucide-react";

import {
  deleteMinute,
  exportFilteredPdfs,
  finalizeMinute,
  getAudit,
  getMinute,
  listMinutes,
  pendingSignatures,
  sendForSignature,
  type MinuteDetail,
  type MinuteListItem,
} from "../api/cecApi";
import { MEETING_TYPE_LABELS, STATUS_LABELS, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import type { CecRoute } from "../hooks/useCecRouterPath";
import { navigateCec } from "../hooks/useCecRouterPath";
import {
  canUnit,
  type ComiteEticaAccess,
  type ComiteEticaUnitCode,
} from "../security/cecAccess";
import { buildMinuteHistoryTimelineItems } from "../utils/minuteHistoryTimelineView";
import {
  ComiteEticaContentCard,
  ComiteEticaPageNotices,
  ComiteEticaFilterInputField,
  ComiteEticaFiltersRow,
  ComiteEticaFilterSelectField,
  ComiteEticaPageHeader,
  ComiteEticaSectionCard,
  ComiteEticaStateBanner,
  ComiteEticaStateBox,
  ComiteEticaTimeline,
} from "../ui/cecUi";
import {
  cecDataTableClassNames,
  cecDataTableLabels,
  cecStatusBadgeClassNames,
} from "../ui/cecUiContracts";
import { CecConfirmModal } from "../ui/CecConfirmModal";
import { CecAppHeader } from "../components/CecAppHeader";
import { MinuteDocumentView } from "../components/MinuteDocumentView";
import { CecMembersPage } from "./CecMembersPage";
import { MinuteEditorPage } from "./MinuteEditorPage";
import { MinuteSignPage } from "./MinuteSignPage";
import { MySignaturePage } from "./MySignaturePage";

type Props = {
  route: CecRoute;
  access: ComiteEticaAccess | null;
  accessLoading: boolean;
  accessError: string | null;
};

type ShellFrameProps = {
  route: CecRoute;
  access: ComiteEticaAccess | null;
  children: ReactNode;
  loading?: boolean;
  lastUpdatedAt?: Date | null;
  onRefresh?: () => void;
  showNewMinute?: boolean;
  className?: string;
};

function CecShellFrame({
  route,
  access,
  children,
  loading,
  lastUpdatedAt,
  onRefresh,
  showNewMinute,
  className,
}: ShellFrameProps) {
  return (
    <div
      className={["dashboard-comite-etica-conduta", "dashboard-page", className]
        .filter(Boolean)
        .join(" ")}
    >
      <div className="cec-app-shell">
        <CecAppHeader
          route={route}
          access={access}
          loading={loading}
          lastUpdatedAt={lastUpdatedAt}
          onRefresh={onRefresh}
          showNewMinute={showNewMinute}
        />
        {children}
      </div>
    </div>
  );
}

function canEditMinute(status: string): boolean {
  return status !== "finalized" && status !== "cancelled";
}

function canDeleteMinute(status: string): boolean {
  return status !== "signed" && status !== "finalized";
}

export function CecAppShell({ route, access, accessLoading, accessError }: Props) {
  const [refreshToken, setRefreshToken] = useState(0);
  const [listLoading, setListLoading] = useState(false);
  const [listUpdatedAt, setListUpdatedAt] = useState<Date | null>(null);
  const bumpRefresh = useCallback(() => setRefreshToken((value) => value + 1), []);

  if (accessLoading) {
    return (
      <div className="dashboard-comite-etica-conduta dashboard-page">
        <ComiteEticaStateBanner>Carregando permissões…</ComiteEticaStateBanner>
      </div>
    );
  }

  if (accessError) {
    return (
      <div className="dashboard-comite-etica-conduta dashboard-page">
        <ComiteEticaStateBanner variant="error">{accessError}</ComiteEticaStateBanner>
      </div>
    );
  }

  if (route.kind === "home") {
    return (
      <CecShellFrame route={route} access={access}>
        <ComiteEticaHomePage access={access} />
      </CecShellFrame>
    );
  }

  if (route.kind === "pending") {
    if (!access?.can_sign) {
      return (
        <CecShellFrame route={route} access={access}>
          <AccessDenied message="Você não tem permissão para assinar atas." />
        </CecShellFrame>
      );
    }
    return (
      <CecShellFrame route={route} access={access} onRefresh={bumpRefresh}>
        <PendingPage refreshToken={refreshToken} />
      </CecShellFrame>
    );
  }

  if (route.kind === "mySignature") {
    if (!access?.can_sign) {
      return (
        <CecShellFrame route={route} access={access}>
          <AccessDenied message="Você não tem permissão para configurar assinatura (comite-etica-conduta.sign)." />
        </CecShellFrame>
      );
    }
    return (
      <CecShellFrame route={route} access={access}>
        <MySignaturePage />
      </CecShellFrame>
    );
  }

  if (
    route.kind === "list" ||
    route.kind === "members" ||
    route.kind === "new" ||
    route.kind === "edit" ||
    route.kind === "detail" ||
    route.kind === "sign"
  ) {
    const unitCode = route.unitCode;
    const requiredAction =
      route.kind === "new" || route.kind === "edit" || route.kind === "members"
        ? "manage"
        : route.kind === "sign"
          ? "sign"
          : "view";

    if (!canUnit(access, unitCode, requiredAction)) {
      return (
        <CecShellFrame route={route} access={access}>
          <AccessDenied
            message={`Sem permissão para esta unidade (${UNIT_LABELS[unitCode]}).`}
          />
        </CecShellFrame>
      );
    }
  }

  if (route.kind === "members") {
    return (
      <CecShellFrame route={route} access={access} onRefresh={bumpRefresh}>
        <CecMembersPage unitCode={route.unitCode} refreshToken={refreshToken} />
      </CecShellFrame>
    );
  }

  if (route.kind === "sign") {
    return (
      <CecShellFrame route={route} access={access}>
        <MinuteSignPage unitCode={route.unitCode} minuteId={route.minuteId} />
      </CecShellFrame>
    );
  }
  if (route.kind === "new" || route.kind === "edit") {
    return (
      <CecShellFrame route={route} access={access}>
        <MinuteEditorPage
          unitCode={route.unitCode}
          minuteId={route.kind === "edit" ? route.minuteId : undefined}
        />
      </CecShellFrame>
    );
  }
  if (route.kind === "detail") {
    return (
      <CecShellFrame route={route} access={access}>
        <MinuteDetailPage
          unitCode={route.unitCode}
          minuteId={route.minuteId}
          access={access}
        />
      </CecShellFrame>
    );
  }
  if (route.kind === "list") {
    return (
      <CecShellFrame
        route={route}
        access={access}
        className="dashboard-comite-etica-conduta--minute-list"
        loading={listLoading}
        lastUpdatedAt={listUpdatedAt}
        onRefresh={bumpRefresh}
        showNewMinute={canUnit(access, route.unitCode, "manage")}
      >
        <MinuteListPage
          unitCode={route.unitCode}
          access={access}
          refreshToken={refreshToken}
          onLoadingChange={setListLoading}
          onLastUpdated={setListUpdatedAt}
        />
      </CecShellFrame>
    );
  }

  return (
    <CecShellFrame route={route} access={access}>
      <ComiteEticaHomePage access={access} />
    </CecShellFrame>
  );
}

function AccessDenied({ message }: { message: string }) {
  return (
    <ComiteEticaStateBox
      variant="error"
      title="Sem acesso"
      message={message}
      action={
        <ActionButton onClick={() => navigateCec("/apps/comite-etica-conduta")}>Voltar ao início</ActionButton>
      }
    />
  );
}

function ComiteEticaHomePage({ access }: { access: ComiteEticaAccess | null }) {
  useEffect(() => {
    navigateCec("/apps/comite-etica-conduta/atas");
  }, []);

  return (
    <ComiteEticaStateBanner>
      {access?.can_view
        ? "Abrindo atas do Comitê de Ética e Conduta…"
        : "Sem permissão para visualizar o Comitê."}
    </ComiteEticaStateBanner>
  );
}

function MinuteListPage({
  unitCode,
  access,
  refreshToken = 0,
  onLoadingChange,
  onLastUpdated,
}: {
  unitCode: ComiteEticaUnitCode;
  access: ComiteEticaAccess | null;
  refreshToken?: number;
  onLoadingChange?: (loading: boolean) => void;
  onLastUpdated?: (date: Date | null) => void;
}) {
  const canManage = canUnit(access, unitCode, "manage");
  const [items, setItems] = useState<MinuteListItem[]>([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<MinuteListItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    (signal?: AbortSignal) => {
      setLoading(true);
      onLoadingChange?.(true);
      return listMinutes(
        { unit_code: unitCode, status: status || undefined, q: q || undefined },
        signal,
      )
        .then((data) => {
          if (signal?.aborted) return;
          setItems(
            [...data.items].sort((left, right) => {
              const byDate = right.meeting_date.localeCompare(left.meeting_date);
              if (byDate !== 0) return byDate;
              return String(right.updated_at || "").localeCompare(String(left.updated_at || ""));
            }),
          );
          setError(null);
          onLastUpdated?.(new Date());
        })
        .catch((err) => {
          if (signal?.aborted || (err instanceof DOMException && err.name === "AbortError")) {
            return;
          }
          setError(err instanceof Error ? err.message : "Erro ao listar.");
        })
        .finally(() => {
          if (!signal?.aborted) {
            setLoading(false);
            onLoadingChange?.(false);
          }
        });
    },
    [unitCode, status, q, onLoadingChange, onLastUpdated],
  );

  // Status aplica na hora; busca com debounce para não disparar a cada tecla.
  useEffect(() => {
    const controller = new AbortController();
    const delayMs = q ? 300 : 0;
    const timer = window.setTimeout(() => {
      void load(controller.signal);
    }, delayMs);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [load, q, refreshToken]);

  const downloadFilteredPdfs = async () => {
    if (items.length === 0 || exporting) return;
    setExporting(true);
    setError(null);
    try {
      const blob = await exportFilteredPdfs({
        unit_code: unitCode,
        status: status || undefined,
        q: q || undefined,
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `atas-comite-etica-conduta-${unitCode}.zip`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao baixar PDFs filtrados.");
    } finally {
      setExporting(false);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteMinute(deleteTarget.id);
      setDeleteTarget(null);
      void load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir ata.");
    } finally {
      setDeleting(false);
    }
  };

  const columns = useMemo<DataTableColumn<MinuteListItem>[]>(
    () => [
      {
        key: "title",
        header: "Título",
        mobileLabel: "Título",
        render: (item) => item.title,
      },
      {
        key: "meeting_date",
        header: "Data",
        mobileLabel: "Data",
        render: (item) => item.meeting_date,
      },
      {
        key: "meeting_type",
        header: "Tipo",
        mobileLabel: "Tipo",
        render: (item) => MEETING_TYPE_LABELS[item.meeting_type] || item.meeting_type,
      },
      {
        key: "status",
        header: "Status",
        mobileLabel: "Status",
        render: (item) => (
          <StatusBadge
            classNames={cecStatusBadgeClassNames}
            label={STATUS_LABELS[item.status] || item.status}
            variant={item.status === "finalized" ? "success" : "neutral"}
          />
        ),
      },
      {
        key: "signatures",
        header: "Assinaturas",
        mobileLabel: "Assinaturas",
        render: (item) => {
          const done = item.signatures_done ?? 0;
          const pending = item.signatures_pending ?? 0;
          const total = done + pending;
          return total > 0 ? `${done}/${total}` : "—";
        },
      },
      ...(canManage
        ? [
            {
              key: "actions",
              header: "Ações",
              mobileLabel: "Ações",
              interactive: true,
              render: (item: MinuteListItem) => (
                <div className="cec-members-actions">
                  {canEditMinute(item.status) ? (
                    <ActionButton
                      variant="ghost"
                      onClick={() =>
                        navigateCec(`/apps/comite-etica-conduta/atas/${item.id}/edit`)
                      }
                    >
                      <Pencil size={14} /> Editar
                    </ActionButton>
                  ) : null}
                  {canDeleteMinute(item.status) ? (
                    <ActionButton variant="ghost" onClick={() => setDeleteTarget(item)}>
                      <Trash2 size={14} /> Excluir
                    </ActionButton>
                  ) : null}
                  {!canEditMinute(item.status) && !canDeleteMinute(item.status) ? "—" : null}
                </div>
              ),
            } satisfies DataTableColumn<MinuteListItem>,
          ]
        : []),
    ],
    [canManage, unitCode],
  );

  return (
    <div className="cec-page-stack cec-page-stack--minute-list">
      <ComiteEticaContentCard className="cec-minute-list-card">
        <ComiteEticaFiltersRow
          as="div"
          trailing={
            <ActionButton
              disabled={loading || exporting || items.length === 0}
              onClick={() => void downloadFilteredPdfs()}
            >
              <Download size={16} />{" "}
              {exporting ? "Gerando ZIP…" : "Baixar PDFs filtrados"}
            </ActionButton>
          }
        >
          <ComiteEticaFilterSelectField
            id="comite-etica-conduta-filter-status"
            label="Status"
            hint={helpTooltips.listFilters}
            value={status}
            onChange={setStatus}
            placeholderOption="Todos"
            options={Object.entries(STATUS_LABELS).map(([value, label]) => ({
              value,
              label,
            }))}
          />
          <ComiteEticaFilterInputField
            id="comite-etica-conduta-filter-query"
            label="Busca"
            type="search"
            value={q}
            onChange={setQ}
            placeholder="Título ou número"
          />
        </ComiteEticaFiltersRow>

        <ComiteEticaPageNotices error={error} onDismissError={() => setError(null)} />

        {!error && !loading && items.length === 0 ? (
          <ComiteEticaStateBox
            variant="empty"
            title="Nenhuma ata encontrada"
            message="Nenhuma ata encontrada para os filtros atuais."
            action={
              canManage ? (
                <ActionButton
                  variant="primary"
                  onClick={() => navigateCec(`/apps/comite-etica-conduta/atas/new`)}
                >
                  <FilePlus2 size={16} /> Criar primeira ata
                </ActionButton>
              ) : undefined
            }
          />
        ) : !error ? (
          <DataTable
            columns={columns}
            rows={items}
            rowKey={(item) => item.id}
            loading={loading}
            onRowClick={(item) =>
              navigateCec(`/apps/comite-etica-conduta/atas/${item.id}`)
            }
            rowClickRole="button"
            layout="embedded"
            classNames={cecDataTableClassNames}
            labels={cecDataTableLabels}
          />
        ) : null}
      </ComiteEticaContentCard>

      <CecConfirmModal
        open={Boolean(deleteTarget)}
        title="Excluir ata"
        message={
          deleteTarget
            ? `Excluir a ata ${deleteTarget.minute_number} — ${deleteTarget.title}? O registro será removido da listagem, mas a auditoria será preservada.`
            : ""
        }
        confirmLabel="Excluir ata"
        busy={deleting}
        variant="danger"
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}

function MinuteDetailPage({
  unitCode,
  minuteId,
  access,
}: {
  unitCode: ComiteEticaUnitCode;
  minuteId: string;
  access: ComiteEticaAccess | null;
}) {
  const canManage = canUnit(access, unitCode, "manage");
  const canSign = canUnit(access, unitCode, "sign");
  const [detail, setDetail] = useState<MinuteDetail | null>(null);
  const [audit, setAudit] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const reload = () => {
    getMinute(minuteId)
      .then(setDetail)
      .catch((err) => setError(err instanceof Error ? err.message : "Erro"));
    getAudit(minuteId)
      .then((data) => setAudit(data.items))
      .catch(() => setAudit([]));
  };

  useEffect(() => {
    reload();
  }, [minuteId]);

  const minute = detail?.minute;
  const status = String(minute?.status || "");

  const confirmDelete = async () => {
    setBusy(true);
    setError(null);
    try {
      await deleteMinute(minuteId);
      navigateCec(`/apps/comite-etica-conduta`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir ata.");
    } finally {
      setBusy(false);
      setDeleteOpen(false);
    }
  };

  return (
    <div className="cec-page-stack">
      <ComiteEticaPageHeader
        nav={
          <BackLink
            variant="prominent"
            onClick={() => navigateCec(`/apps/comite-etica-conduta`)}
          >
            Voltar
          </BackLink>
        }
        title={String(minute?.title || "Ata")}
        subtitle={`${String(minute?.minute_number || "")} · ${STATUS_LABELS[status] || status}`}
        actions={
          <>
            {canManage && canEditMinute(status) && (
              <ActionButton
                disabled={busy}
                onClick={() =>
                  navigateCec(`/apps/comite-etica-conduta/atas/${minuteId}/edit`)
                }
              >
                <Pencil size={16} /> Editar
              </ActionButton>
            )}
            {canManage && canDeleteMinute(status) && (
              <ActionButton variant="ghost" disabled={busy} onClick={() => setDeleteOpen(true)}>
                <Trash2 size={16} /> Excluir
              </ActionButton>
            )}
            {canManage && (status === "draft" || status === "in_review") && (
              <ActionButton
                variant="primary"
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  sendForSignature(minuteId)
                    .then(() => reload())
                    .catch((err) => setError(err instanceof Error ? err.message : "Erro"))
                    .finally(() => setBusy(false));
                }}
              >
                Enviar para assinatura
              </ActionButton>
            )}
            {canSign && detail?.viewer?.can_sign_now && (
              <ActionButton
                variant="primary"
                onClick={() =>
                  navigateCec(`/apps/comite-etica-conduta/atas/${minuteId}/sign`)
                }
              >
                <PenLine size={16} /> Assinar
              </ActionButton>
            )}
            {canManage && status === "signed" && (
              <ActionButton
                variant="primary"
                disabled={busy}
                onClick={() => {
                  setBusy(true);
                  finalizeMinute(minuteId)
                    .then(() => reload())
                    .catch((err) => setError(err instanceof Error ? err.message : "Erro"))
                    .finally(() => setBusy(false));
                }}
              >
                Finalizar
              </ActionButton>
            )}
          </>
        }
      />

      <ComiteEticaPageNotices error={error} onDismissError={() => setError(null)} />

      <CecConfirmModal
        open={deleteOpen}
        title="Excluir ata"
        message={`Excluir a ata ${String(minute?.minute_number || "")} — ${String(minute?.title || "")}? O registro será removido da listagem, mas a auditoria será preservada.`}
        confirmLabel="Excluir ata"
        busy={busy}
        variant="danger"
        onConfirm={() => void confirmDelete()}
        onCancel={() => setDeleteOpen(false)}
      />

      {detail ? (
        <MinuteDocumentView
          detail={detail}
          toolbar={
            <DocumentReaderToolbar
              printTitle={String(minute?.title || minute?.minute_number || "Ata Comitê")}
            />
          }
        />
      ) : (
        <ComiteEticaStateBox variant="loading" message="Carregando modo de leitura…" />
      )}

      <ComiteEticaSectionCard title="Histórico da ata">
        <ComiteEticaTimeline
          layout="tree"
          aria-label="Histórico de versões e auditoria da ata"
          items={buildMinuteHistoryTimelineItems(detail?.versions || [], audit)}
          emptyMessage="Nenhum evento registrado."
        />
      </ComiteEticaSectionCard>
    </div>
  );
}

function PendingPage({ refreshToken = 0 }: { refreshToken?: number }) {
  const [items, setItems] = useState<MinuteListItem[]>([]);
  useEffect(() => {
    pendingSignatures().then((data) => setItems(data.items)).catch(() => setItems([]));
  }, [refreshToken]);
  return (
    <div className="cec-page-stack">
      <ComiteEticaSectionCard title="Assinaturas pendentes">
        <p className="cec-muted" style={{ margin: "0 0 12px" }}>
          Atas que aguardam sua assinatura
        </p>
        {items.length === 0 ? (
          <ComiteEticaStateBox
            variant="empty"
            title="Nenhuma pendência"
            message="Não há atas aguardando sua assinatura."
            action={
              <ActionButton onClick={() => navigateCec("/apps/comite-etica-conduta/minha-assinatura")}>
                <PenLine size={16} /> Configurar minha assinatura
              </ActionButton>
            }
          />
        ) : (
          <ul className="cec-list">
            {items.map((item) => (
              <li key={item.id}>
                <ActionButton
                  variant="link"
                  onClick={() =>
                    navigateCec(`/apps/comite-etica-conduta/atas/${item.id}/sign`)
                  }
                >
                  {item.minute_number} — {item.title}
                </ActionButton>
              </li>
            ))}
          </ul>
        )}
      </ComiteEticaSectionCard>
    </div>
  );
}
