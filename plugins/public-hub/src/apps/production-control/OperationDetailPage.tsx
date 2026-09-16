import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import type { MachineLoadOperation } from "./api";
import { buildPublicProductModelGlbUrl } from "./api";
import {
  BrandBar,
  CopyValueButton,
  DrawingViewer,
  formatDate,
  formatDateTime,
  formatQty,
  formatUnit,
  resolveStatus,
  useDrawingObjectUrl,
  VisualModeTabs,
  type VisualMode,
} from "./cockpitShared";
import { ProductModelViewer } from "./ProductModelViewer";
import {
  usePublicOperationAppointments,
  type PublicOperationAppointmentsState,
} from "./usePublicOperationAppointments";

type Props = {
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  position: number;
  queueSize: number;
  onBack: () => void;
  onPrevious?: () => void;
  onNext?: () => void;
};

/**
 * Detalhe da operação: dados da fila à esquerda; desenho/3D à direita.
 * «Produzida» / «Pendente» usam a soma apontada da operação (mesma fonte do modal).
 */
export function OperationDetailPage({
  token,
  branch,
  operation,
  position,
  queueSize,
  onBack,
  onPrevious,
  onNext,
}: Props) {
  const [fullscreen, setFullscreen] = useState(false);
  const [appointmentsOpen, setAppointmentsOpen] = useState(false);
  const appointments = usePublicOperationAppointments(
    token,
    branch,
    operation.production_order,
    operation.operation_code,
  );
  const status = resolveStatus(operation);
  const paCode = operation.pa_product_code?.trim() || "";
  const productCode = operation.product_code?.trim() || "";
  const has3dModel = Boolean(operation.has_3d_model && productCode);
  const canDraw = Boolean(paCode);
  const displayProductCode = paCode || productCode;
  const [mode, setMode] = useState<VisualMode>(canDraw ? "drawing" : "model");
  const drawing = useDrawingObjectUrl(token, branch, paCode || null);
  const glbUrl =
    has3dModel && productCode ? buildPublicProductModelGlbUrl(token, branch, productCode) : null;

  const producedQty = resolveOperationProducedQty(operation, appointments);
  const pendingQty = resolveOperationPendingQty(operation, producedQty);
  const appointmentCount =
    appointments.data?.summary.appointment_count ?? operation.appointment_count ?? 0;

  useEffect(() => {
    setMode(canDraw ? "drawing" : "model");
  }, [canDraw, productCode, paCode]);

  const canFullscreen =
    (mode === "drawing" && canDraw && drawing.status === "ready") ||
    (mode === "model" && has3dModel);

  return (
    <section className="pcp-pub pcp-pub--detail">
      <BrandBar
        title={`OP ${operation.production_order}`}
        titleExtra={
          <CopyValueButton value={operation.production_order} label="Copiar OP" />
        }
        stats={
          <span className={`pcp-pub__badge pcp-pub__badge--${status.tone}`}>
            {status.tone === "running" ? (
              <span className="pcp-pub__badge-dot" aria-hidden="true" />
            ) : null}
            {status.label}
          </span>
        }
        lead={
          <button type="button" className="pcp-pub__back" onClick={onBack}>
            <span aria-hidden="true">←</span> Voltar para a fila
          </button>
        }
        actions={
          <nav className="pcp-pub__queue-nav" aria-label="Navegação na fila">
            <button
              type="button"
              className="pcp-pub__queue-nav-btn"
              onClick={onPrevious}
              disabled={!onPrevious}
              title={onPrevious ? `Operação ${position - 1} da fila` : "Início da fila"}
            >
              <span aria-hidden="true">‹</span> Anterior
            </button>
            <span className="pcp-pub__queue-nav-pos" aria-live="polite">
              {position}/{queueSize}
            </span>
            <button
              type="button"
              className="pcp-pub__queue-nav-btn"
              onClick={onNext}
              disabled={!onNext}
              title={onNext ? `Operação ${position + 1} da fila` : "Fim da fila"}
            >
              Próxima <span aria-hidden="true">›</span>
            </button>
          </nav>
        }
      />

      <div className="pcp-pub__wrap">
        <div className="pcp-pub__split">
          <div className="pcp-pub__split-main">
            <h2 className="pcp-pub__detail-product">
              <strong
                className={
                  paCode
                    ? "pcp-pub__detail-product-code pcp-pub__product-code--pa"
                    : "pcp-pub__detail-product-code"
                }
              >
                {displayProductCode}
              </strong>
              <span className="pcp-pub__detail-product-desc">
                {operation.pa_product_description || operation.product_description}
              </span>
            </h2>

            {status.operatorNote ? (
              <p className="pcp-pub__detail-operator">{status.operatorNote}</p>
            ) : null}

            <dl className="pcp-pub__facts">
              <Fact label="Operação">
                {operation.operation_code} · {operation.operation_description}
              </Fact>
              <Fact label="Ferramenta">{operation.tool || "—"}</Fact>
              <Fact label="Recurso">{operation.resource || "—"}</Fact>
              <Fact label="Produto da OP" wide>
                {operation.product_code}
                <span className="pcp-pub__fact-sub">{operation.product_description}</span>
              </Fact>
            </dl>

            <h3 className="pcp-pub__detail-section">Quantidades</h3>
            <dl className="pcp-pub__facts pcp-pub__facts--num">
              <Fact label="Planejada">
                {formatQty(operation.planned_qty)}{" "}
                {formatUnit(operation.unit, operation.planned_qty)}
              </Fact>
              <Fact label="Produzida">
                {appointments.loading ? (
                  "…"
                ) : producedQty == null ? (
                  "—"
                ) : (
                  <>
                    {formatQty(producedQty)} {formatUnit(operation.unit, producedQty)}
                    <span className="pcp-pub__fact-sub">apontada nesta operação</span>
                  </>
                )}
              </Fact>
              <Fact label="Pendente" emphasis>
                {appointments.loading ? (
                  "…"
                ) : pendingQty == null ? (
                  "—"
                ) : (
                  <>
                    {formatQty(pendingQty)} {formatUnit(operation.unit, pendingQty)}
                  </>
                )}
              </Fact>
            </dl>

            <h3 className="pcp-pub__detail-section">Programação e entrega</h3>
            <dl className="pcp-pub__facts pcp-pub__facts--num">
              <Fact label="Início programado">
                {formatDate(operation.scheduled_date)}
                {operation.scheduled_start_time ? (
                  <span className="pcp-pub__fact-sub">{operation.scheduled_start_time}</span>
                ) : null}
              </Fact>
              <Fact label="Fim programado">
                {formatDate(operation.scheduled_end_date)}
                {operation.scheduled_end_time ? (
                  <span className="pcp-pub__fact-sub">{operation.scheduled_end_time}</span>
                ) : null}
              </Fact>
              <Fact label="Pedido cliente">{formatDate(operation.pa_due_date)}</Fact>
            </dl>

            <div className="pcp-pub__detail-actions">
              <button
                type="button"
                className="pcp-pub__drawing"
                onClick={() => setAppointmentsOpen(true)}
              >
                Ver apontamentos
                {appointmentCount > 0 ? ` (${appointmentCount})` : ""}
              </button>
            </div>
          </div>

          <aside className="pcp-pub__split-aside" aria-label="Visualização">
            <div className="pcp-pub__preview-head">
              <div className="pcp-pub__preview-heading">
                <VisualModeTabs
                  show={canDraw && has3dModel}
                  mode={mode}
                  onChange={setMode}
                />
              </div>
              {canFullscreen ? (
                <button
                  type="button"
                  className="pcp-pub__ghost pcp-pub__ghost--plain"
                  onClick={() => setFullscreen(true)}
                >
                  Tela cheia
                </button>
              ) : null}
            </div>

            {mode === "drawing" ? (
              <>
                {!paCode ? (
                  <p className="pcp-pub__preview-state">
                    Esta operação não tem PA vinculado na fila, então não há desenho para exibir.
                  </p>
                ) : null}
                {paCode && drawing.status === "loading" ? (
                  <p className="pcp-pub__preview-state">Carregando desenho…</p>
                ) : null}
                {paCode && drawing.status === "error" ? (
                  <p className="pcp-pub__preview-state pcp-pub__preview-state--error">
                    {drawing.message}
                  </p>
                ) : null}
                {paCode && drawing.status === "ready" && drawing.objectUrl ? (
                  <iframe
                    className="pcp-pub__preview-frame"
                    title={`Desenho ${paCode}`}
                    src={drawing.objectUrl}
                  />
                ) : null}
              </>
            ) : glbUrl && productCode ? (
              <ProductModelViewer
                className="pcp-pub__preview-model"
                src={glbUrl}
                alt={`Modelo 3D do produto ${productCode}`}
              />
            ) : (
              <p className="pcp-pub__preview-state">
                Não há modelo 3D anexado ao produto desta operação.
              </p>
            )}
          </aside>
        </div>
      </div>

      {fullscreen && (canDraw || has3dModel) ? (
        <DrawingViewer
          token={token}
          branch={branch}
          paCode={paCode || null}
          productCode={productCode || null}
          has3dModel={has3dModel}
          onClose={() => setFullscreen(false)}
        />
      ) : null}

      {appointmentsOpen ? (
        <AppointmentsModal
          operation={operation}
          appointments={appointments}
          onClose={() => setAppointmentsOpen(false)}
        />
      ) : null}
    </section>
  );
}

/** Soma apontada nesta operação (não C2_QUJE da OP).
 *
 * A API já devolve o total da operação; o histórico da janela só cobre snapshot
 * antigo, publicado antes do campo existir. */
function resolveOperationProducedQty(
  operation: MachineLoadOperation,
  appointments: PublicOperationAppointmentsState,
): number | null {
  const fromApi = operation.operation_produced_qty;
  if (typeof fromApi === "number" && Number.isFinite(fromApi)) return fromApi;
  if (appointments.loading) return null;
  if (appointments.data) {
    return appointments.data.summary.produced_qty ?? 0;
  }
  // Falha do histórico: não mascara com C2_QUJE (outra grandeza).
  return null;
}

function resolveOperationPendingQty(
  operation: MachineLoadOperation,
  producedQty: number | null,
): number | null {
  const fromApi = operation.operation_pending_qty;
  if (typeof fromApi === "number" && Number.isFinite(fromApi)) return fromApi;
  if (producedQty == null || !Number.isFinite(operation.planned_qty)) return null;
  return Math.max(0, Math.round((operation.planned_qty - producedQty) * 1000) / 1000);
}

function AppointmentsModal({
  operation,
  appointments,
  onClose,
}: {
  operation: MachineLoadOperation;
  appointments: PublicOperationAppointmentsState;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const { data: payload, loading, error } = appointments;
  const items = payload?.items ?? [];
  const count = payload?.summary.appointment_count ?? operation.appointment_count ?? 0;
  const totalQty = payload?.summary.produced_qty ?? null;

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-appointments-title"
    >
      <button type="button" className="pcp-pub-modal__backdrop" aria-label="Fechar" onClick={onClose} />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--appointments">
        <header className="pcp-pub-modal__head">
          <h2 id="pcp-pub-appointments-title">Apontamentos</h2>
          <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
            Fechar
          </button>
        </header>

        <dl className="pcp-pub__facts pcp-pub__facts--num">
          <Fact label="Registrados">{loading ? "…" : count}</Fact>
          <Fact label="Total apontado">
            {loading
              ? "…"
              : totalQty == null
                ? "—"
                : `${formatQty(totalQty)} ${formatUnit(operation.unit, totalQty)}`}
          </Fact>
          <Fact label="Último">
            {operation.last_appointment_date
              ? formatDateTime(operation.last_appointment_date)
              : items[0]?.produced_on
                ? formatAppointmentWhen(items[0].produced_on, items[0].start_time)
                : "—"}
          </Fact>
        </dl>

        {loading ? (
          <p className="pcp-pub-modal__empty">Carregando apontamentos…</p>
        ) : error ? (
          <p className="pcp-pub-modal__empty">{error}</p>
        ) : items.length > 0 ? (
          <div className="pcp-pub-modal__table-wrap">
            <table className="pcp-pub-modal__table">
              <thead>
                <tr>
                  <th scope="col">Data</th>
                  <th scope="col">Quantidade</th>
                  <th scope="col">Posto</th>
                  <th scope="col">Operador</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row, index) => {
                  const qty = row.quantity;
                  return (
                    <tr key={`${row.produced_on}-${row.start_time}-${row.work_center}-${index}`}>
                      <td>{formatAppointmentWhen(row.produced_on, row.start_time)}</td>
                      <td className="pcp-pub__num">
                        {qty == null
                          ? "—"
                          : `${formatQty(qty)} ${formatUnit(row.unit ?? operation.unit, qty)}`}
                      </td>
                      <td>{row.work_center?.trim() || "—"}</td>
                      <td>{row.operator_name?.trim() || "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="pcp-pub-modal__empty">Nenhum apontamento registrado nesta operação.</p>
        )}
      </div>
    </div>
  );
}

function formatAppointmentWhen(date: string | null, time: string | null): string {
  const day = formatDate(date);
  const clock = (time || "").trim().slice(0, 5);
  if (day === "—" && !clock) return "—";
  if (!clock) return day;
  if (day === "—") return clock;
  return `${day}, ${clock}`;
}

function Fact({
  label,
  children,
  emphasis,
  wide,
}: {
  label: string;
  children: ReactNode;
  emphasis?: boolean;
  wide?: boolean;
}) {
  return (
    <div
      className={`pcp-pub__fact${emphasis ? " pcp-pub__fact--emphasis" : ""}${
        wide ? " pcp-pub__fact--wide" : ""
      }`}
    >
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
