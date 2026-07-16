import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  BackLink,
  DataTable,
  printDocumentReader,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import {
  Building2,
  Download,
  FilePlus2,
  PenLine,
  Pencil,
  Printer,
  RefreshCw,
  Trash2,
  Users,
} from "lucide-react";

import {
  deleteMinute,
  exportPdf,
  finalizeMinute,
  getAudit,
  getMinute,
  listMinutes,
  pendingSignatures,
  sendForSignature,
  type MinuteDetail,
  type MinuteListItem,
} from "../api/cipaApi";
import { MEETING_TYPE_LABELS, STATUS_LABELS, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import type { CipaRoute } from "../hooks/useCipaRouterPath";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import {
  canUnit,
  readableUnits,
  type CipaAccess,
  type CipaUnitCode,
} from "../security/cipaAccess";
import {
  CipaContentCard,
  CipaFilterInputField,
  CipaFiltersRow,
  CipaFilterSelectField,
  CipaNavigationCard,
  CipaPageHeader,
  CipaSectionCard,
  CipaStateBanner,
  CipaStateBox,
} from "../ui/cipaUi";
import {
  cipaDataTableClassNames,
  cipaDataTableLabels,
  cipaStatusBadgeClassNames,
} from "../ui/cipaUiContracts";
import { CipaConfirmModal } from "../ui/CipaConfirmModal";
import { CipaMembersPage } from "./CipaMembersPage";
import { MinuteEditorPage } from "./MinuteEditorPage";
import { MinuteDocumentView } from "../components/MinuteDocumentView";
import { MinuteSignPage } from "./MinuteSignPage";
import { MySignaturePage } from "./MySignaturePage";

type Props = {
  route: CipaRoute;
  access: CipaAccess | null;
  accessLoading: boolean;
  accessError: string | null;
};

function canEditMinute(status: string): boolean {
  return status !== "finalized" && status !== "cancelled";
}

function canDeleteMinute(status: string): boolean {
  return status !== "signed" && status !== "finalized";
}

export function CipaAppShell({ route, access, accessLoading, accessError }: Props) {
  if (accessLoading) {
    return (
      <div className="dashboard-cipa dashboard-page">
        <CipaStateBanner>Carregando permissões…</CipaStateBanner>
      </div>
    );
  }

  if (accessError) {
    return (
      <div className="dashboard-cipa dashboard-page">
        <CipaStateBanner variant="error">{accessError}</CipaStateBanner>
      </div>
    );
  }

  if (route.kind === "home") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <CipaHomePage access={access} />
      </div>
    );
  }

  if (route.kind === "pending") {
    if (!access?.can_sign) {
      return (
        <div className="dashboard-cipa dashboard-page">
          <AccessDenied message="Você não tem permissão para assinar atas." />
        </div>
      );
    }
    return (
      <div className="dashboard-cipa dashboard-page">
        <PendingPage />
      </div>
    );
  }

  if (route.kind === "mySignature") {
    if (!access?.can_sign) {
      return (
        <div className="dashboard-cipa dashboard-page">
          <AccessDenied message="Você não tem permissão para configurar assinatura (cipa.sign)." />
        </div>
      );
    }
    return (
      <div className="dashboard-cipa dashboard-page">
        <MySignaturePage />
      </div>
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
        <div className="dashboard-cipa dashboard-page">
          <AccessDenied
            message={`Sem permissão para esta unidade (${UNIT_LABELS[unitCode]}).`}
          />
        </div>
      );
    }
  }

  if (route.kind === "members") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <CipaMembersPage unitCode={route.unitCode} />
      </div>
    );
  }

  if (route.kind === "sign") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <MinuteSignPage unitCode={route.unitCode} minuteId={route.minuteId} />
      </div>
    );
  }
  if (route.kind === "new" || route.kind === "edit") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <MinuteEditorPage
          unitCode={route.unitCode}
          minuteId={route.kind === "edit" ? route.minuteId : undefined}
        />
      </div>
    );
  }
  if (route.kind === "detail") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <MinuteDetailPage
          unitCode={route.unitCode}
          minuteId={route.minuteId}
          access={access}
        />
      </div>
    );
  }
  if (route.kind === "list") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <MinuteListPage unitCode={route.unitCode} access={access} />
      </div>
    );
  }

  return (
    <div className="dashboard-cipa dashboard-page">
      <CipaHomePage access={access} />
    </div>
  );
}

function AccessDenied({ message }: { message: string }) {
  return (
    <CipaStateBox
      variant="error"
      title="Sem acesso"
      message={message}
      action={
        <ActionButton onClick={() => navigateCipa("/apps/cipa")}>Voltar ao início</ActionButton>
      }
    />
  );
}

function CipaHomePage({ access }: { access: CipaAccess | null }) {
  const units = readableUnits(access);
  const singleUnit = units.length === 1 ? units[0] : null;

  useEffect(() => {
    if (singleUnit) {
      navigateCipa(`/apps/cipa/filial-${singleUnit.id}`);
    }
  }, [singleUnit]);

  if (singleUnit) {
    return <CipaStateBanner>Redirecionando para {singleUnit.label}…</CipaStateBanner>;
  }

  return (
    <div className="cipa-page-stack">
      <CipaPageHeader title="CIPA" subtitle="Escolha a unidade ou acesse suas pendências de assinatura." />

      {units.length > 0 ? (
        <CipaSectionCard title="Unidades">
          <div className="cipa-unit-grid">
            {units.map((unit) => (
              <CipaNavigationCard
                key={unit.id}
                icon={<Building2 size={22} />}
                title={unit.label}
                meta={`Filial ${unit.id}`}
                onClick={() => navigateCipa(`/apps/cipa/filial-${unit.id}`)}
              />
            ))}
          </div>
        </CipaSectionCard>
      ) : (
        <CipaContentCard>
          <CipaStateBanner>
            Nenhuma unidade disponível. Solicite <code>cipa.view</code> ou{" "}
            <code>cipa.manage</code> combinado com <code>cipa.unit.filial-01</code> /{" "}
            <code>cipa.unit.filial-02</code>.
          </CipaStateBanner>
        </CipaContentCard>
      )}

      {access?.can_sign ? (
        <CipaSectionCard title="Assinaturas">
          <div className="cipa-home-actions">
            <ActionButton variant="primary" onClick={() => navigateCipa("/apps/cipa/pending")}>
              <PenLine size={16} /> Ver pendências
            </ActionButton>
            <ActionButton onClick={() => navigateCipa("/apps/cipa/my-signature")}>
              <PenLine size={16} /> Minha assinatura
            </ActionButton>
          </div>
        </CipaSectionCard>
      ) : null}
    </div>
  );
}

function MinuteListPage({
  unitCode,
  access,
}: {
  unitCode: CipaUnitCode;
  access: CipaAccess | null;
}) {
  const canManage = canUnit(access, unitCode, "manage");
  const canSign = Boolean(access?.can_sign);
  const [items, setItems] = useState<MinuteListItem[]>([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<MinuteListItem | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    listMinutes(
      { unit_code: unitCode, status: status || undefined, q: q || undefined },
      controller.signal,
    )
      .then((data) => {
        setItems(data.items);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erro ao listar."))
      .finally(() => setLoading(false));
    return () => controller.abort();
  };

  useEffect(() => load(), [unitCode, status]);

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteMinute(deleteTarget.id);
      setDeleteTarget(null);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir ata.");
    } finally {
      setDeleting(false);
    }
  };

  const columns = useMemo<DataTableColumn<MinuteListItem>[]>(
    () => [
      {
        key: "minute_number",
        header: "Nº",
        mobileLabel: "Nº",
        render: (item) => item.minute_number,
      },
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
            classNames={cipaStatusBadgeClassNames}
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
                <div className="cipa-members-actions">
                  {canEditMinute(item.status) ? (
                    <ActionButton
                      variant="ghost"
                      onClick={() =>
                        navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${item.id}/edit`)
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
    <div className="cipa-page-stack">
      <CipaPageHeader
        nav={<BackLink onClick={() => navigateCipa("/apps/cipa")}>Unidades</BackLink>}
        title={`CIPA — ${UNIT_LABELS[unitCode]}`}
        subtitle="Atas de reunião da unidade"
        actions={
          <>
            <ActionButton variant="ghost" onClick={() => load()}>
              <RefreshCw size={16} /> Atualizar
            </ActionButton>
            {canSign ? (
              <ActionButton onClick={() => navigateCipa("/apps/cipa/my-signature")}>
                <PenLine size={16} /> Minha assinatura
              </ActionButton>
            ) : null}
            {canManage ? (
              <>
                <ActionButton
                  onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/members`)}
                >
                  <Users size={16} /> Membros e cargos
                </ActionButton>
                <ActionButton
                  variant="primary"
                  onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/new`)}
                >
                  <FilePlus2 size={16} /> Nova ata
                </ActionButton>
              </>
            ) : null}
          </>
        }
      />

      <CipaContentCard>
        <CipaFiltersRow
          as="div"
          trailing={<ActionButton onClick={() => load()}>Buscar</ActionButton>}
        >
          <CipaFilterSelectField
            id="cipa-filter-status"
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
          <CipaFilterInputField
            id="cipa-filter-query"
            label="Busca"
            type="search"
            value={q}
            onChange={setQ}
            placeholder="Título ou número"
          />
        </CipaFiltersRow>

        {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}

        {!error && !loading && items.length === 0 ? (
          <CipaStateBox
            variant="empty"
            title="Nenhuma ata encontrada"
            message="Nenhuma ata encontrada para os filtros atuais."
            action={
              canManage ? (
                <ActionButton
                  variant="primary"
                  onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/new`)}
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
              navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${item.id}`)
            }
            rowClickRole="button"
            layout="embedded"
            classNames={cipaDataTableClassNames}
            labels={cipaDataTableLabels}
          />
        ) : null}
      </CipaContentCard>

      <CipaConfirmModal
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
  unitCode: CipaUnitCode;
  minuteId: string;
  access: CipaAccess | null;
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

  const downloadPdf = async () => {
    setBusy(true);
    setError(null);
    try {
      const blob = await exportPdf(minuteId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `ata-cipa-${String(minute?.minute_number || minuteId).replace("/", "-")}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.setTimeout(() => URL.revokeObjectURL(url), 1_000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao baixar PDF");
    } finally {
      setBusy(false);
    }
  };

  const confirmDelete = async () => {
    setBusy(true);
    setError(null);
    try {
      await deleteMinute(minuteId);
      navigateCipa(`/apps/cipa/filial-${unitCode}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir ata.");
    } finally {
      setBusy(false);
      setDeleteOpen(false);
    }
  };

  return (
    <div className="cipa-page-stack">
      <CipaPageHeader
        nav={
          <BackLink onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}`)}>
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
                  navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}/edit`)
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
            {canSign &&
              (status === "awaiting_signatures" || status === "partially_signed") && (
                <ActionButton
                  variant="primary"
                  onClick={() =>
                    navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}/sign`)
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

      {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}

      <CipaConfirmModal
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
            <>
              <ActionButton onClick={printDocumentReader}>
                <Printer size={16} /> Imprimir
              </ActionButton>
              <ActionButton
                variant="primary"
                disabled={busy}
                onClick={() => void downloadPdf()}
              >
                <Download size={16} /> {busy ? "Gerando…" : "Baixar PDF"}
              </ActionButton>
            </>
          }
        />
      ) : (
        <CipaStateBox variant="loading" message="Carregando modo de leitura…" />
      )}

      <CipaSectionCard title="Versões">
        <ul className="cipa-list">
          {(detail?.versions || []).map((version) => (
            <li key={String(version.id)}>
              v{String(version.version_number)} · {String(version.created_at)} ·{" "}
              {String(version.change_reason || "")}
            </li>
          ))}
        </ul>
      </CipaSectionCard>

      <CipaSectionCard title="Auditoria">
        <ul className="cipa-list">
          {audit.map((item) => (
            <li key={String(item.id)}>
              {String(item.action)} · {String(item.created_at)}
            </li>
          ))}
        </ul>
      </CipaSectionCard>
    </div>
  );
}

function PendingPage() {
  const [items, setItems] = useState<MinuteListItem[]>([]);
  useEffect(() => {
    pendingSignatures().then((data) => setItems(data.items)).catch(() => setItems([]));
  }, []);
  return (
    <div className="cipa-page-stack">
      <CipaPageHeader
        nav={<BackLink onClick={() => navigateCipa("/apps/cipa")}>Início</BackLink>}
        title="Assinaturas pendentes"
        subtitle="Atas que aguardam sua assinatura"
        actions={
          <ActionButton
            variant="primary"
            onClick={() => navigateCipa("/apps/cipa/my-signature")}
          >
            <PenLine size={16} /> Minha assinatura
          </ActionButton>
        }
      />
      <CipaContentCard>
        {items.length === 0 ? (
          <CipaStateBox
            variant="empty"
            title="Nenhuma pendência"
            message="Não há atas aguardando sua assinatura."
            action={
              <ActionButton onClick={() => navigateCipa("/apps/cipa/my-signature")}>
                <PenLine size={16} /> Configurar minha assinatura
              </ActionButton>
            }
          />
        ) : (
          <ul className="cipa-list">
            {items.map((item) => (
              <li key={item.id}>
                <ActionButton
                  variant="link"
                  onClick={() =>
                    navigateCipa(`/apps/cipa/filial-${item.unit_code}/minutes/${item.id}/sign`)
                  }
                >
                  {item.minute_number} — {item.title}
                </ActionButton>
              </li>
            ))}
          </ul>
        )}
      </CipaContentCard>
    </div>
  );
}
