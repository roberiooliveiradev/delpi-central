import { useEffect, useState } from "react";
import {
  FieldLabel,
  NativeSelectControl,
  NativeTextControl,
  StatusBadge,
  statusBadgeBemClasses,
} from "@delpi/plugin-ui/index";
import { Building2, FilePlus2, PenLine, RefreshCw } from "lucide-react";

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
import {
  canUnit,
  readableUnits,
  type CipaAccess,
  type CipaUnitCode,
} from "../security/cipaAccess";
import { MinuteEditorPage } from "./MinuteEditorPage";
import { MinuteSignPage } from "./MinuteSignPage";
import { MySignaturePage } from "./MySignaturePage";

const badgeClasses = statusBadgeBemClasses("cipa");

type Props = {
  route: CipaRoute;
  access: CipaAccess | null;
  accessLoading: boolean;
  accessError: string | null;
};

export function CipaAppShell({ route, access, accessLoading, accessError }: Props) {
  if (accessLoading) {
    return (
      <div className="dashboard-cipa dashboard-page">
        <p className="cipa-state">Carregando permissões…</p>
      </div>
    );
  }

  if (accessError) {
    return (
      <div className="dashboard-cipa dashboard-page">
        <p className="cipa-error">{accessError}</p>
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
    route.kind === "new" ||
    route.kind === "edit" ||
    route.kind === "detail" ||
    route.kind === "sign"
  ) {
    const unitCode = route.unitCode;
    const requiredAction =
      route.kind === "new" || route.kind === "edit"
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
    <section className="cipa-card">
      <h1>Sem acesso</h1>
      <p className="cipa-state">{message}</p>
      <button type="button" className="cipa-btn" onClick={() => navigateCipa("/apps/cipa")}>
        Voltar ao início
      </button>
    </section>
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
    return <p className="cipa-state">Redirecionando para {singleUnit.label}…</p>;
  }

  return (
    <div className="cipa-page-stack">
      <header className="cipa-header">
        <div>
          <h1>CIPA</h1>
          <p>Escolha a unidade ou acesse suas pendências de assinatura.</p>
        </div>
      </header>

      {units.length > 0 ? (
        <section className="cipa-card">
          <h2>Unidades</h2>
          <div className="cipa-unit-grid">
            {units.map((unit) => (
              <button
                key={unit.id}
                type="button"
                className="cipa-unit-card"
                onClick={() => navigateCipa(`/apps/cipa/filial-${unit.id}`)}
              >
                <Building2 size={22} />
                <span className="cipa-unit-card__title">{unit.label}</span>
                <span className="cipa-unit-card__meta">Filial {unit.id}</span>
              </button>
            ))}
          </div>
        </section>
      ) : (
        <section className="cipa-card">
          <p className="cipa-state">
            Nenhuma unidade disponível. Solicite <code>cipa.view</code> ou{" "}
            <code>cipa.manage</code> combinado com <code>cipa.unit.filial-01</code> /{" "}
            <code>cipa.unit.filial-02</code>.
          </p>
        </section>
      )}

      {access?.can_sign ? (
        <section className="cipa-card">
          <h2>Assinaturas</h2>
          <div className="cipa-home-actions">
            <button
              type="button"
              className="cipa-btn cipa-btn--primary"
              onClick={() => navigateCipa("/apps/cipa/pending")}
            >
              <PenLine size={16} /> Ver pendências
            </button>
            <button
              type="button"
              className="cipa-btn"
              onClick={() => navigateCipa("/apps/cipa/my-signature")}
            >
              <PenLine size={16} /> Minha assinatura
            </button>
          </div>
        </section>
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

  return (
    <div className="cipa-page-stack">
      <header className="cipa-header">
        <div>
          <button type="button" className="cipa-link" onClick={() => navigateCipa("/apps/cipa")}>
            ← Unidades
          </button>
          <h1>CIPA — {UNIT_LABELS[unitCode]}</h1>
          <p>Atas de reunião da unidade</p>
        </div>
        <div className="cipa-header__actions">
          <button type="button" className="cipa-btn cipa-btn--ghost" onClick={() => load()}>
            <RefreshCw size={16} /> Atualizar
          </button>
          {canSign ? (
            <button
              type="button"
              className="cipa-btn"
              onClick={() => navigateCipa("/apps/cipa/my-signature")}
            >
              <PenLine size={16} /> Minha assinatura
            </button>
          ) : null}
          {canManage ? (
            <button
              type="button"
              className="cipa-btn cipa-btn--primary"
              onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/new`)}
            >
              <FilePlus2 size={16} /> Nova ata
            </button>
          ) : null}
        </div>
      </header>

      <section className="cipa-card">
        <div className="cipa-filters">
          <div className="cipa-field">
            <FieldLabel
              label="Status"
              hint={helpTooltips.listFilters}
              htmlFor="cipa-filter-status"
              className="cipa-field__label"
            />
            <NativeSelectControl
              id="cipa-filter-status"
              value={status}
              onChange={setStatus}
              placeholderOption="Todos"
              options={Object.entries(STATUS_LABELS).map(([value, label]) => ({
                value,
                label,
              }))}
            />
          </div>
          <div className="cipa-field cipa-field--grow">
            <FieldLabel
              label="Busca"
              htmlFor="cipa-filter-query"
              className="cipa-field__label"
            />
            <NativeTextControl
              id="cipa-filter-query"
              value={q}
              onChange={setQ}
              onKeyDown={(e) => {
                if (e.key === "Enter") load();
              }}
              placeholder="Título ou número"
            />
          </div>
          <button type="button" className="cipa-btn cipa-filters__submit" onClick={() => load()}>
            Buscar
          </button>
        </div>

        {error ? <p className="cipa-error">{error}</p> : null}
        {loading ? (
          <p className="cipa-state">Carregando…</p>
        ) : !error && items.length === 0 ? (
          <div className="cipa-empty-state">
            <p className="cipa-state">Nenhuma ata encontrada para os filtros atuais.</p>
            {canManage ? (
              <button
                type="button"
                className="cipa-btn cipa-btn--primary"
                onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/new`)}
              >
                <FilePlus2 size={16} /> Criar primeira ata
              </button>
            ) : null}
          </div>
        ) : !error ? (
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
        ) : null}
      </section>
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
          {canManage && (status === "draft" || status === "in_review") && (
            <button
              type="button"
              className="cipa-btn"
              onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}/edit`)}
            >
              Editar
            </button>
          )}
          {canManage && (status === "draft" || status === "in_review") && (
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
          {canSign && (status === "awaiting_signatures" || status === "partially_signed") && (
            <button
              type="button"
              className="cipa-btn cipa-btn--primary"
              onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}/sign`)}
            >
              <PenLine size={16} /> Assinar
            </button>
          )}
          {canManage && status === "signed" && (
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
          <button type="button" className="cipa-link" onClick={() => navigateCipa("/apps/cipa")}>
            ← Início
          </button>
          <h1>Assinaturas pendentes</h1>
          <p>Atas que aguardam sua assinatura</p>
        </div>
        <div className="cipa-header__actions">
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            onClick={() => navigateCipa("/apps/cipa/my-signature")}
          >
            <PenLine size={16} /> Minha assinatura
          </button>
        </div>
      </header>
      <section className="cipa-card">
        {items.length === 0 ? (
          <div className="cipa-empty-state">
            <p className="cipa-state">Nenhuma pendência.</p>
            <button
              type="button"
              className="cipa-btn"
              onClick={() => navigateCipa("/apps/cipa/my-signature")}
            >
              <PenLine size={16} /> Configurar minha assinatura
            </button>
          </div>
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
