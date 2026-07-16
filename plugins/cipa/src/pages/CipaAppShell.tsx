import { useEffect, useState } from "react";
import { HelpTooltip, StatusBadge, statusBadgeBemClasses } from "@delpi/plugin-ui/index";
import { FilePlus2, PenLine, RefreshCw } from "lucide-react";

import {
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
import { MinuteEditorPage } from "./MinuteEditorPage";
import { MinuteSignPage } from "./MinuteSignPage";

const badgeClasses = statusBadgeBemClasses("cipa");

type Props = { route: CipaRoute };

export function CipaAppShell({ route }: Props) {
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
        <MinuteDetailPage unitCode={route.unitCode} minuteId={route.minuteId} />
      </div>
    );
  }
  if (route.kind === "pending") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <PendingPage />
      </div>
    );
  }
  if (route.kind === "list") {
    return (
      <div className="dashboard-cipa dashboard-page">
        <MinuteListPage unitCode={route.unitCode} />
      </div>
    );
  }
  return (
    <div className="dashboard-cipa dashboard-page">
      <p className="cipa-state">Selecione uma unidade no menu (Filial 01 ou 02).</p>
    </div>
  );
}

function MinuteListPage({ unitCode }: { unitCode: "01" | "02" }) {
  const [items, setItems] = useState<MinuteListItem[]>([]);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    listMinutes(
      { unit_code: unitCode, status: status || undefined, q: q || undefined },
      controller.signal,
    )
      .then((data) => setItems(data.items))
      .catch((err) => setError(err instanceof Error ? err.message : "Erro ao listar."))
      .finally(() => setLoading(false));
    return () => controller.abort();
  };

  useEffect(() => load(), [unitCode, status]);

  return (
    <div className="cipa-page-stack">
      <header className="cipa-header">
        <div>
          <h1>CIPA — {UNIT_LABELS[unitCode]}</h1>
          <p>Atas de reunião da unidade</p>
        </div>
        <div className="cipa-header__actions">
          <button type="button" className="cipa-btn cipa-btn--ghost" onClick={() => load()}>
            <RefreshCw size={16} /> Atualizar
          </button>
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/new`)}
          >
            <FilePlus2 size={16} /> Nova ata
          </button>
        </div>
      </header>

      <section className="cipa-card">
        <div className="cipa-filters">
          <label>
            Status
            <HelpTooltip content={helpTooltips.listFilters} />
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Todos</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Busca
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") load();
              }}
              placeholder="Título ou número"
            />
          </label>
          <button type="button" className="cipa-btn" onClick={() => load()}>
            Buscar
          </button>
        </div>

        {error && <p className="cipa-error">{error}</p>}
        {loading ? (
          <p className="cipa-state">Carregando…</p>
        ) : items.length === 0 ? (
          <p className="cipa-state">Nenhuma ata encontrada.</p>
        ) : (
          <div className="cipa-table-wrap">
            <table className="cipa-table">
              <thead>
                <tr>
                  <th>Nº</th>
                  <th>Título</th>
                  <th>Data</th>
                  <th>Tipo</th>
                  <th>Status</th>
                  <th>Assinaturas</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() =>
                      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${item.id}`)
                    }
                  >
                    <td>{item.minute_number}</td>
                    <td>{item.title}</td>
                    <td>{item.meeting_date}</td>
                    <td>{MEETING_TYPE_LABELS[item.meeting_type] || item.meeting_type}</td>
                    <td>
                      <StatusBadge
                        classNames={badgeClasses}
                        label={STATUS_LABELS[item.status] || item.status}
                        variant={item.status === "finalized" ? "success" : "neutral"}
                      />
                    </td>
                    <td>
                      {item.signatures_done ?? 0}/
                      {(item.signatures_done ?? 0) + (item.signatures_pending ?? 0) || "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function MinuteDetailPage({
  unitCode,
  minuteId,
}: {
  unitCode: "01" | "02";
  minuteId: string;
}) {
  const [detail, setDetail] = useState<MinuteDetail | null>(null);
  const [audit, setAudit] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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

  return (
    <div className="cipa-page-stack">
      <header className="cipa-header">
        <div>
          <button
            type="button"
            className="cipa-link"
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}`)}
          >
            ← Voltar
          </button>
          <h1>{String(minute?.title || "Ata")}</h1>
          <p>
            {String(minute?.minute_number || "")} · {STATUS_LABELS[status] || status}
          </p>
        </div>
        <div className="cipa-header__actions">
          {(status === "draft" || status === "in_review") && (
            <button
              type="button"
              className="cipa-btn"
              onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}/edit`)}
            >
              Editar
            </button>
          )}
          {(status === "draft" || status === "in_review") && (
            <button
              type="button"
              className="cipa-btn cipa-btn--primary"
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
            </button>
          )}
          {(status === "awaiting_signatures" || status === "partially_signed") && (
            <button
              type="button"
              className="cipa-btn cipa-btn--primary"
              onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}/sign`)}
            >
              <PenLine size={16} /> Assinar
            </button>
          )}
          {status === "signed" && (
            <button
              type="button"
              className="cipa-btn cipa-btn--primary"
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
            </button>
          )}
        </div>
      </header>

      {error && <p className="cipa-error">{error}</p>}

      <section className="cipa-card">
        <h2>Conteúdo</h2>
        <div
          className="cipa-prose"
          dangerouslySetInnerHTML={{
            __html: String(detail?.version?.body_html || "<p>Sem conteúdo.</p>"),
          }}
        />
      </section>

      <section className="cipa-card">
        <h2>Signatários</h2>
        <ul className="cipa-list">
          {(detail?.signers || []).map((signer) => (
            <li key={String(signer.id)}>
              {String(signer.display_name)} — {String(signer.status)}
            </li>
          ))}
        </ul>
      </section>

      <section className="cipa-card">
        <h2>Versões</h2>
        <ul className="cipa-list">
          {(detail?.versions || []).map((version) => (
            <li key={String(version.id)}>
              v{String(version.version_number)} · {String(version.created_at)} ·{" "}
              {String(version.change_reason || "")}
            </li>
          ))}
        </ul>
      </section>

      <section className="cipa-card">
        <h2>Auditoria</h2>
        <ul className="cipa-list">
          {audit.map((item) => (
            <li key={String(item.id)}>
              {String(item.action)} · {String(item.created_at)}
            </li>
          ))}
        </ul>
      </section>
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
      <header className="cipa-header">
        <div>
          <h1>Assinaturas pendentes</h1>
          <p>Atas que aguardam sua assinatura</p>
        </div>
      </header>
      <section className="cipa-card">
        {items.length === 0 ? (
          <p className="cipa-state">Nenhuma pendência.</p>
        ) : (
          <ul className="cipa-list">
            {items.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  className="cipa-link"
                  onClick={() =>
                    navigateCipa(`/apps/cipa/filial-${item.unit_code}/minutes/${item.id}/sign`)
                  }
                >
                  {item.minute_number} — {item.title}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
