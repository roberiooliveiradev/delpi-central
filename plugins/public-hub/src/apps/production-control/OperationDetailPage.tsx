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
 * Detalhe da operação com visualização ao lado: PDF do PA e, se houver, 3D do produto da OP.
 *
 * Só apresenta o que a fila publicada já traz — nenhuma consulta nova ao TOTVS.
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
                {formatQty(operation.produced_qty)}{" "}
                {formatUnit(operation.unit, operation.produced_qty)}
              </Fact>
              <Fact label="Pendente" emphasis>
                {formatQty(operation.pending_qty)}{" "}
                {formatUnit(operation.unit, operation.pending_qty)}
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
                {(operation.appointment_count ?? 0) > 0
                  ? ` (${operation.appointment_count})`
                  : ""}
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
        <AppointmentsModal operation={operation} onClose={() => setAppointmentsOpen(false)} />
      ) : null}
    </section>
  );
}

function AppointmentsModal({
  operation,
  onClose,
}: {
  operation: MachineLoadOperation;
  onClose: () => void;
}) {
  const operatorName = operation.active_operator_name?.trim() || null;
  const appointmentCount = operation.appointment_count ?? 0;
  const activeCount = operation.active_operator_count ?? 0;
  const unit = formatUnit(operation.unit, operation.produced_qty);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="pcp-pub-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pcp-pub-appointments-title"
    >
      <button type="button" className="pcp-pub-modal__backdrop" aria-label="Fechar" onClick={onClose} />
      <div className="pcp-pub-modal__panel">
        <header className="pcp-pub-modal__head">
          <h2 id="pcp-pub-appointments-title">Apontamentos</h2>
          <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
            Fechar
          </button>
        </header>

        <dl className="pcp-pub__facts pcp-pub__facts--num">
          <Fact label="Registrados">{appointmentCount}</Fact>
          <Fact label="Último">
            {operation.last_appointment_date
              ? formatDateTime(operation.last_appointment_date)
              : "—"}
          </Fact>
          <Fact label="Operadores ativos">{activeCount}</Fact>
        </dl>

        <h3 className="pcp-pub__detail-section">Quem apontou</h3>
        {operatorName ? (
          <ul className="pcp-pub-modal__operators">
            <li className="pcp-pub-modal__operator">
              <span className="pcp-pub-modal__operator-name">{operatorName}</span>
              <span className="pcp-pub-modal__operator-qty">
                {formatQty(operation.produced_qty)} {unit}
                <span className="pcp-pub__fact-sub">produzida na OP</span>
              </span>
              {activeCount > 1 ? (
                <span className="pcp-pub__fact-sub">
                  +{activeCount - 1} operador(es) ativo(s) no coletor
                </span>
              ) : null}
            </li>
          </ul>
        ) : appointmentCount > 0 ? (
          <p className="pcp-pub-modal__empty">
            Há {appointmentCount} apontamento(s) registrado(s), mas nenhum operador ativo agora.
            Quantidade produzida: {formatQty(operation.produced_qty)} {unit}.
          </p>
        ) : (
          <p className="pcp-pub-modal__empty">Nenhum apontamento registrado nesta operação.</p>
        )}
      </div>
    </div>
  );
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
