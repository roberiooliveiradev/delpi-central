import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";

import {
  Activity,
  ChevronDown,
  ChevronUp,
  X,
} from "lucide-react";

import {
  SuppliesActionButton,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { getSuppliersIntegrationStatus } from "./api";
import { SP_HELP } from "../../content/helpTooltips";
import { SUPPLIERS_CONTENT as C } from "./content";
import type { SupplierIntegrationStatus } from "./types";

type BadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

// X4.REST-STATUS.S2 — widget flutuante com máquina de estados única.
type WidgetView = "closed" | "collapsed" | "expanded";

// Último resultado/view compartilhados entre lista e ficha: navegar entre as
// páginas remonta o componente, mas não deve refazer a verificação REST nem
// reabrir um painel que o usuário fechou deliberadamente.
let lastStatus: SupplierIntegrationStatus | null = null;
let lastView: WidgetView = "collapsed";

function overallBadge(overall: string | null): { label: string; variant: BadgeVariant } {
  if (overall === "ready_for_attempt") {
    return { label: C.statusOverallReady, variant: "success" };
  }
  if (overall === "upstream_pending") {
    return { label: C.statusOverallPending, variant: "warning" };
  }
  if (overall === "unavailable") {
    return { label: C.statusOverallUnavailable, variant: "danger" };
  }
  return { label: C.statusStatePending, variant: "neutral" };
}

function environmentLabel(value: string | null): string {
  if (value === "production") return C.statusEnvironmentProduction;
  if (value === "homologation") return C.statusEnvironmentHomologation;
  return C.statusEnvironmentUnknown;
}

function stateBadge(
  value: string | null,
  okLabel: string,
): { label: string; variant: BadgeVariant } {
  if (value === "ok") return { label: okLabel, variant: "success" };
  if (value === "failed") return { label: C.statusStateFailed, variant: "warning" };
  if (value === "missing" || value === "invalid" || value === "unavailable") {
    return { label: C.statusStateUnavailable, variant: "danger" };
  }
  return { label: C.statusStatePending, variant: "neutral" };
}

function gateBadge(value: string | null): { label: string; variant: BadgeVariant } {
  if (value === "enabled") return { label: C.statusStateEnabled, variant: "info" };
  if (value === "disabled") return { label: C.statusStateDisabled, variant: "neutral" };
  return { label: C.statusStatePending, variant: "neutral" };
}

function guardBadge(value: string | null): { label: string; variant: BadgeVariant } {
  if (value === "ok") return { label: C.statusStateVerified, variant: "success" };
  if (value === "mismatch") return { label: C.statusStateMismatch, variant: "danger" };
  if (value === "unverified") return { label: C.statusStateUnverified, variant: "warning" };
  return { label: C.statusStatePending, variant: "neutral" };
}

function authenticationBadge(
  status: SupplierIntegrationStatus | null,
): { label: string; variant: BadgeVariant } {
  if (!status) return { label: C.statusStatePending, variant: "neutral" };
  if (status.authentication === "ok") {
    return { label: C.statusStateValid, variant: "success" };
  }
  if (status.authentication === "failed") {
    const http = status.authentication_http_status;
    return {
      label: http ? `HTTP ${http}` : C.statusStateFailed,
      variant: "danger",
    };
  }
  return { label: C.statusStatePending, variant: "neutral" };
}

function formatCheckedAt(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

type RowProps = {
  label: string;
  badge: { label: string; variant: BadgeVariant };
};

function StatusRow({ label, badge }: RowProps) {
  return (
    <div className="sp-suppliers-status-card__row">
      <span className="sp-suppliers-status-card__row-label">{label}</span>
      <SuppliesStatusBadge label={badge.label} variant={badge.variant} />
    </div>
  );
}

export function SupplierIntegrationStatusCard() {
  const [view, setViewState] = useState<WidgetView>(lastView);
  const [checking, setChecking] = useState(false);
  const [status, setStatusState] = useState<SupplierIntegrationStatus | null>(lastStatus);
  const [failed, setFailed] = useState(false);
  const requestRef = useRef(0);
  const reopenRef = useRef<HTMLButtonElement | null>(null);

  const setView = useCallback((next: WidgetView) => {
    lastView = next;
    setViewState(next);
  }, []);

  const setStatus = useCallback((next: SupplierIntegrationStatus | null) => {
    lastStatus = next;
    setStatusState(next);
  }, []);

  // Ao fechar, o foco não pode ficar em elemento oculto: devolve ao acionador
  // discreto que acabou de aparecer.
  useEffect(() => {
    if (view === "closed") reopenRef.current?.focus();
  }, [view]);

  const runCheck = useCallback(async () => {
    if (checking) return;
    const requestId = ++requestRef.current;
    const controller = new AbortController();
    setChecking(true);
    setFailed(false);
    try {
      const data = await getSuppliersIntegrationStatus(controller.signal);
      if (requestRef.current === requestId) setStatus(data);
    } catch {
      if (requestRef.current === requestId) setFailed(true);
    } finally {
      if (requestRef.current === requestId) setChecking(false);
    }
  }, [checking, setStatus]);

  const summary = status ? overallBadge(status.overall) : null;
  const checkedAt = status ? formatCheckedAt(status.checked_at) : "";
  const expanded = view === "expanded";

  // X4.REST-STATUS.S2.R1 — portal no body: o host federado anima a entrada da
  // rota com `transform` (appHostRouteEnter, fill both), o que transforma o
  // ancestral em containing block e captura o `position: fixed` — o painel
  // passava a ancorar no fim do conteúdo e era cortado fora da viewport.
  // Renderizar via portal restaura a âncora real na viewport.
  let widget: ReactNode;
  if (view === "closed") {
    widget = (
      <button
        ref={reopenRef}
        type="button"
        className="sp-suppliers-status-card__reopen"
        title={C.statusReopenTooltip}
        aria-label={C.statusReopenTooltip}
        onClick={() => setView("collapsed")}
      >
        <Activity size={18} aria-hidden />
      </button>
    );
  } else {
    widget = (
    <section
      className={`sp-suppliers-status-card${
        expanded ? " sp-suppliers-status-card--expanded" : ""
      }`}
      aria-label={C.statusCardTitle}
      onKeyDown={(event) => {
        if (event.key === "Escape" && expanded) setView("collapsed");
      }}
    >
      <div className="sp-suppliers-status-card__head">
        <div className="sp-suppliers-status-card__head-text">
          <span
            className="sp-suppliers-status-card__title"
            title={SP_HELP.suppliersIntegrationStatus}
          >
            <span
              className={`sp-suppliers-status-card__dot${
                summary ? ` sp-suppliers-status-card__dot--${summary.variant}` : ""
              }`}
              aria-hidden
            />
            {C.statusCardTitle}
          </span>
          <span className="sp-suppliers-status-card__summary" aria-live="polite">
            {summary ? (
              <SuppliesStatusBadge label={summary.label} variant={summary.variant} />
            ) : (
              <span className="sp-suppliers-status-card__idle">
                {checking ? C.statusChecking : C.statusNeverChecked}
              </span>
            )}
          </span>
        </div>
        <button
          type="button"
          className="sp-suppliers-status-card__icon-btn"
          aria-expanded={expanded}
          aria-controls="sp-suppliers-status-card-details"
          aria-label={expanded ? C.statusCollapseAction : C.statusExpandAction}
          title={expanded ? C.statusCollapseAction : C.statusExpandAction}
          onClick={() => setView(expanded ? "collapsed" : "expanded")}
        >
          {expanded ? (
            <ChevronDown size={16} aria-hidden />
          ) : (
            <ChevronUp size={16} aria-hidden />
          )}
        </button>
        <button
          type="button"
          className="sp-suppliers-status-card__icon-btn"
          aria-label={C.statusCloseAction}
          title={C.statusCloseAction}
          onClick={() => setView("closed")}
        >
          <X size={16} aria-hidden />
        </button>
      </div>

      {failed ? (
        <p className="sp-suppliers-status-card__error" role="alert">
          {C.statusCheckFailed}
        </p>
      ) : null}

      {expanded ? (
        <div
          id="sp-suppliers-status-card-details"
          className="sp-suppliers-status-card__details"
        >
          <p className="sp-suppliers-status-card__env" aria-live="polite">
            {C.statusEnvironmentLabel}: {environmentLabel(status?.environment ?? null)}
            {checkedAt ? (
              <>
                {" · "}
                {C.statusCheckedAtLabel}: {checkedAt}
              </>
            ) : null}
          </p>
          <StatusRow
            label={C.statusRowConfiguration}
            badge={stateBadge(status?.configuration ?? null, C.statusStateOk)}
          />
          <StatusRow
            label={C.statusRowConnectivity}
            badge={stateBadge(status?.connectivity ?? null, C.statusStateAccessible)}
          />
          <StatusRow
            label={C.statusRowAuthentication}
            badge={authenticationBadge(status)}
          />
          <StatusRow
            label={C.statusRowSuppliersRead}
            badge={stateBadge(status?.suppliers_read ?? null, C.statusStateFunctional)}
          />
          <StatusRow
            label={C.statusRowCreateGate}
            badge={gateBadge(status?.create_gate ?? null)}
          />
          <StatusRow
            label={C.statusRowUpdateGate}
            badge={gateBadge(status?.update_gate ?? null)}
          />
          <StatusRow
            label={C.statusRowWriteGuard}
            badge={guardBadge(status?.write_target_guard ?? null)}
          />
          <StatusRow
            label={C.statusRowWriteValidation}
            badge={{ label: C.statusStateNotTested, variant: "neutral" }}
          />
          <p className="sp-suppliers-status-card__note">
            {C.statusWriteNotProvenNote}
          </p>
          <p className="sp-suppliers-status-card__note">
            {C.statusSqlIndependentNote}
          </p>
          <div className="sp-suppliers-status-card__actions">
            <SuppliesActionButton
              type="button"
              variant="primary"
              disabled={checking}
              onClick={runCheck}
            >
              {checking
                ? C.statusChecking
                : status
                  ? C.statusCheckAgainAction
                  : C.statusCheckAction}
            </SuppliesActionButton>
          </div>
        </div>
      ) : null}
    </section>
    );
  }

  if (typeof document === "undefined") return null;
  // Escopo .dashboard-supplies-portal reaplicado no wrapper do portal: os
  // tokens --sp-* e os seletores do widget dependem dessa classe e ela não
  // existe acima do mount point do MFE no body.
  return createPortal(
    <div className="dashboard-supplies-portal sp-suppliers-status-card-portal">
      {widget}
    </div>,
    document.body,
  );
}
