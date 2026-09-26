import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { ArrowLeft, ClipboardCheck, ClipboardList, Package } from "lucide-react";
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
  WorkCenterShiftMetrics,
  type VisualMode,
} from "./cockpitShared";
import { ProductModelViewer } from "./ProductModelViewer";
import { ProductionRunControls } from "./ProductionRunControls";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime";
import {
  usePublicOperationAppointments,
  type PublicOperationAppointmentsState,
} from "./usePublicOperationAppointments";
import {
  usePublicOperationMaterials,
  type PublicOperationMaterialsState,
} from "./usePublicOperationMaterials";
import {
  usePublicOperationProcessInspections,
  type PublicOperationProcessInspectionsState,
} from "./usePublicOperationProcessInspections";

type Props = {
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  position: number;
  queueSize: number;
  workCenter: string;
  workCenterName: string;
  shiftLabel: string;
  shiftPct: number | null;
  shiftProducedQty: number | null;
  downtimeHours: number | null;
  downtimeAvailable: boolean;
  runUpdatedSignal: number;
  runRealtimeEvent: MachineLoadRealtimeEvent | null;
  realtimeConnected: boolean;
  onOpenPerformance: () => void;
  onOpenDowntime: () => void;
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
  workCenter,
  workCenterName,
  shiftLabel,
  shiftPct,
  shiftProducedQty,
  downtimeHours,
  downtimeAvailable,
  runUpdatedSignal,
  runRealtimeEvent,
  realtimeConnected,
  onOpenPerformance,
  onOpenDowntime,
  onBack,
  onPrevious,
  onNext,
}: Props) {
  const [fullscreen, setFullscreen] = useState(false);
  const [appointmentsOpen, setAppointmentsOpen] = useState(false);
  const [materialsOpen, setMaterialsOpen] = useState(false);
  const [inspectionsOpen, setInspectionsOpen] = useState(false);
  const appointments = usePublicOperationAppointments(
    token,
    branch,
    operation.production_order,
    operation.operation_code,
  );
  const materials = usePublicOperationMaterials(
    token,
    branch,
    operation.production_order,
    operation.operation_code,
    materialsOpen,
  );
  const inspections = usePublicOperationProcessInspections(
    token,
    branch,
    operation.production_order,
    operation.operation_code,
  );
  const inspectionCount =
    inspections.data?.summary.inspection_count ?? inspections.data?.items.length ?? 0;
  const inspectionsTone =
    inspections.loading || inspections.error
      ? null
      : inspectionCount > 0
        ? "ok"
        : "empty";
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
        eyebrow={workCenterName || "Centro de trabalho"}
        title={`OP ${operation.production_order}`}
        code={workCenter}
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
        metrics={
          <WorkCenterShiftMetrics
            shiftLabel={shiftLabel}
            shiftPct={shiftPct}
            shiftProducedQty={shiftProducedQty}
            downtimeHours={downtimeHours}
            downtimeAvailable={downtimeAvailable}
            onOpenPerformance={onOpenPerformance}
            onOpenDowntime={onOpenDowntime}
          />
        }
        lead={
          <button
            type="button"
            className="pcp-pub__back pcp-pub__back--icon"
            onClick={onBack}
            aria-label="Voltar para a fila"
            title="Voltar para a fila"
          >
            <ArrowLeft size={22} strokeWidth={2.4} aria-hidden="true" />
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

            <div className="pcp-pub__detail-op-product" aria-label="Produto da OP">
              <span className="pcp-pub__detail-op-product-label">Produto da OP</span>
              <strong className="pcp-pub__detail-op-product-code">
                {operation.product_code || "—"}
              </strong>
              {operation.product_description?.trim() ? (
                <span className="pcp-pub__detail-op-product-desc">
                  {operation.product_description}
                </span>
              ) : null}
            </div>

            <dl className="pcp-pub__facts">
              <Fact label="Operação">
                {operation.operation_code} · {operation.operation_description}
              </Fact>
              <Fact label="Ferramenta">{operation.tool || "—"}</Fact>
            </dl>

            <h3 className="pcp-pub__detail-section">Quantidades</h3>
            <dl className="pcp-pub__facts pcp-pub__facts--num pcp-pub__facts--qty">
              <Fact label="Planejada">
                {formatQty(operation.planned_qty)}{" "}
                {formatUnit(operation.unit, operation.planned_qty)}
              </Fact>
              <Fact label="Produzida">
                {appointments.loading
                  ? "…"
                  : producedQty == null
                    ? "—"
                    : `${formatQty(producedQty)} ${formatUnit(operation.unit, producedQty)}`}
              </Fact>
              <Fact label="Pendente" emphasis>
                {appointments.loading
                  ? "…"
                  : pendingQty == null
                    ? "—"
                    : `${formatQty(pendingQty)} ${formatUnit(operation.unit, pendingQty)}`}
              </Fact>
            </dl>

            <ProductionRunControls
              token={token}
              branch={branch}
              workCenter={workCenter}
              operation={operation}
              runUpdatedSignal={runUpdatedSignal}
              runRealtimeEvent={runRealtimeEvent}
              realtimeConnected={realtimeConnected}
            />

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
                className="pcp-pub__icon-btn"
                onClick={() => setAppointmentsOpen(true)}
                aria-label={
                  appointmentCount > 0
                    ? `Ver apontamentos (${appointmentCount})`
                    : "Ver apontamentos"
                }
                title={
                  appointmentCount > 0
                    ? `Ver apontamentos (${appointmentCount})`
                    : "Ver apontamentos"
                }
              >
                <ClipboardList size={20} strokeWidth={2.2} aria-hidden="true" />
                {appointmentCount > 0 ? (
                  <span className="pcp-pub__icon-btn-badge">{appointmentCount}</span>
                ) : null}
              </button>
              <button
                type="button"
                className="pcp-pub__icon-btn"
                onClick={() => setMaterialsOpen(true)}
                aria-label="Matérias-primas"
                title="Matérias-primas"
              >
                <Package size={20} strokeWidth={2.2} aria-hidden="true" />
              </button>
              <button
                type="button"
                className={[
                  "pcp-pub__icon-btn",
                  inspectionsTone === "ok" ? "pcp-pub__icon-btn--ok" : "",
                  inspectionsTone === "empty" ? "pcp-pub__icon-btn--empty" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => setInspectionsOpen(true)}
                aria-label={
                  inspectionsTone === "ok"
                    ? `Inspeções de processo (${inspectionCount})`
                    : inspectionsTone === "empty"
                      ? "Inspeções de processo (nenhuma registrada)"
                      : "Inspeções de processo"
                }
                title={
                  inspectionsTone === "ok"
                    ? `Inspeções realizadas (${inspectionCount})`
                    : inspectionsTone === "empty"
                      ? "Nenhuma inspeção registrada"
                      : "Inspeções de processo"
                }
              >
                <ClipboardCheck size={20} strokeWidth={2.2} aria-hidden="true" />
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

      {materialsOpen ? (
        <MaterialsModal
          materials={materials}
          onClose={() => setMaterialsOpen(false)}
        />
      ) : null}

      {inspectionsOpen ? (
        <ProcessInspectionsModal
          inspections={inspections}
          onClose={() => setInspectionsOpen(false)}
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
  const lastItem = items.length > 0 ? items[items.length - 1] : null;

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
              : lastItem?.produced_on
                ? formatAppointmentWhen(lastItem.produced_on, lastItem.start_time)
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

function MaterialsModal({
  materials,
  onClose,
}: {
  materials: PublicOperationMaterialsState;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const { data: payload, loading, error } = materials;
  const items = payload?.items ?? [];

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-materials-title"
    >
      <button type="button" className="pcp-pub-modal__backdrop" aria-label="Fechar" onClick={onClose} />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--materials">
        <header className="pcp-pub-modal__head">
          <h2 id="pcp-pub-materials-title">Matérias-primas</h2>
          <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
            Fechar
          </button>
        </header>

        {loading ? (
          <p className="pcp-pub-modal__empty">Carregando matérias-primas…</p>
        ) : error ? (
          <p className="pcp-pub-modal__empty">{error}</p>
        ) : items.length > 0 ? (
          <div className="pcp-pub-modal__table-wrap">
            <table className="pcp-pub-modal__table">
              <thead>
                <tr>
                  <th scope="col">Código</th>
                  <th scope="col">Descrição</th>
                  <th scope="col">UM</th>
                  <th scope="col">Original</th>
                  <th scope="col">Saldo</th>
                  <th scope="col">Consumido</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.product_code}>
                    <td>{row.product_code || "—"}</td>
                    <td>{row.description?.trim() || "—"}</td>
                    <td>{row.unit?.trim() || "—"}</td>
                    <td className="pcp-pub__num">{formatQty(row.original_qty)}</td>
                    <td className="pcp-pub__num">{formatQty(row.open_qty)}</td>
                    <td className="pcp-pub__num">{formatQty(row.consumed_qty)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="pcp-pub-modal__empty">
            Esta operação não possui matérias-primas vinculadas.
          </p>
        )}
      </div>
    </div>
  );
}

function ProcessInspectionsModal({
  inspections,
  onClose,
}: {
  inspections: PublicOperationProcessInspectionsState;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const { data: payload, loading, error } = inspections;
  const items = payload?.items ?? [];

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-inspections-title"
    >
      <button type="button" className="pcp-pub-modal__backdrop" aria-label="Fechar" onClick={onClose} />
      <div className="pcp-pub-modal__panel pcp-pub-modal__panel--inspections">
        <header className="pcp-pub-modal__head">
          <h2 id="pcp-pub-inspections-title">Inspeções de processo</h2>
          <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
            Fechar
          </button>
        </header>

        {loading ? (
          <p className="pcp-pub-modal__empty">Carregando inspeções…</p>
        ) : error ? (
          <p className="pcp-pub-modal__empty">{error}</p>
        ) : items.length > 0 ? (
          <div className="pcp-pub-modal__table-wrap">
            <table className="pcp-pub-modal__table">
              <thead>
                <tr>
                  <th scope="col">Quando</th>
                  <th scope="col">Inspetor</th>
                  <th scope="col">Resultado</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row, index) => (
                  <tr key={`${row.inspector_name}-${row.measurement_date}-${row.measurement_time}-${index}`}>
                    <td>{formatAppointmentWhen(row.measurement_date, row.measurement_time)}</td>
                    <td>{row.inspector_name?.trim() || "—"}</td>
                    <td>
                      <span
                        className={`pcp-pub-modal__result pcp-pub-modal__result--${inspectionResultTone(row.result_code, row.result)}`}
                      >
                        {formatInspectionResult(row.result)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="pcp-pub-modal__empty">
            Nenhuma inspeção de processo registrada para esta operação.
          </p>
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

function formatInspectionResult(result: string): string {
  const raw = (result || "").trim();
  if (!raw) return "Realizada";
  const upper = raw.toUpperCase();
  if (upper === "APROVADO") return "Aprovado";
  if (upper === "REPROVADO") return "Reprovado";
  if (upper === "TOLERANCIA" || upper === "TOLERÂNCIA") return "Tolerância";
  if (upper === "REALIZADA") return "Realizada";
  return raw;
}

function inspectionResultTone(code: string, result: string): "ok" | "fail" | "warn" | "neutral" {
  const c = (code || "").trim().toUpperCase();
  if (c === "A") return "ok";
  if (c === "R") return "fail";
  if (c === "T") return "warn";
  const upper = (result || "").trim().toUpperCase();
  if (upper.startsWith("APROV")) return "ok";
  if (upper.startsWith("REPROV")) return "fail";
  if (upper.startsWith("TOLER")) return "warn";
  return "neutral";
}

function Fact({
  label,
  children,
  emphasis,
}: {
  label: string;
  children: ReactNode;
  emphasis?: boolean;
}) {
  return (
    <div className={`pcp-pub__fact${emphasis ? " pcp-pub__fact--emphasis" : ""}`}>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
