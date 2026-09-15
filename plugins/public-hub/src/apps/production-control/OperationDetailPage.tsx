import { useState } from "react";
import type { ReactNode } from "react";
import type { MachineLoadOperation } from "./api";
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
} from "./cockpitShared";

type Props = {
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  position: number;
  onBack: () => void;
};

/**
 * Detalhe da operação com o desenho ao lado.
 *
 * Só apresenta o que a fila publicada já traz — nenhuma consulta nova ao TOTVS.
 */
export function OperationDetailPage({ token, branch, operation, position, onBack }: Props) {
  const [fullscreen, setFullscreen] = useState(false);
  const status = resolveStatus(operation);
  const paCode = operation.pa_product_code?.trim() || "";
  const displayProductCode = paCode || operation.product_code;
  const drawing = useDrawingObjectUrl(token, branch, paCode || null);

  return (
    <section className="pcp-pub pcp-pub--detail">
      <BrandBar
        eyebrow={`Operação ${position} da fila · ${operation.work_center}`}
        title={`OP ${operation.production_order}`}
        code={operation.operation_code}
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
      />

      <div className="pcp-pub__wrap">
        <div className="pcp-pub__split">
          <div className="pcp-pub__split-main">
            <h2 className="pcp-pub__detail-product">
              <strong className={paCode ? "pcp-pub__product-code--pa" : undefined}>
                {displayProductCode}
              </strong>{" "}
              {operation.pa_product_description || operation.product_description}
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
              <Fact label="Produto intermediário">
                {operation.product_code}
                <span className="pcp-pub__fact-sub">{operation.product_description}</span>
              </Fact>
            </dl>

            <h3 className="pcp-pub__detail-section">Quantidades</h3>
            <dl className="pcp-pub__facts pcp-pub__facts--num">
              <Fact label="Planejada">
                {formatQty(operation.planned_qty)} {formatUnit(operation.unit)}
              </Fact>
              <Fact label="Produzida">
                {formatQty(operation.produced_qty)} {formatUnit(operation.unit)}
              </Fact>
              <Fact label="Pendente" emphasis>
                {formatQty(operation.pending_qty)} {formatUnit(operation.unit)}
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
              <Fact label="Entrega do PA">{formatDate(operation.pa_due_date)}</Fact>
            </dl>

            <h3 className="pcp-pub__detail-section">Apontamentos</h3>
            <dl className="pcp-pub__facts pcp-pub__facts--num">
              <Fact label="Registrados">{operation.appointment_count ?? 0}</Fact>
              <Fact label="Último">
                {operation.last_appointment_date
                  ? formatDateTime(operation.last_appointment_date)
                  : "—"}
              </Fact>
              <Fact label="Operadores ativos">{operation.active_operator_count ?? 0}</Fact>
            </dl>

            <p className="pcp-pub__detail-copy">
              <span className="pcp-pub__order-label">OP</span>
              <strong>{operation.production_order}</strong>
              <CopyValueButton value={operation.production_order} label="Copiar OP" />
            </p>
          </div>

          <aside className="pcp-pub__split-aside" aria-label="Desenho do produto">
            <div className="pcp-pub__preview-head">
              <span className="pcp-pub__preview-title">
                {paCode ? `Desenho ${paCode}` : "Desenho"}
              </span>
              {paCode && drawing.status === "ready" ? (
                <button
                  type="button"
                  className="pcp-pub__ghost pcp-pub__ghost--plain"
                  onClick={() => setFullscreen(true)}
                >
                  Tela cheia
                </button>
              ) : null}
            </div>

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
          </aside>
        </div>
      </div>

      {fullscreen && paCode ? (
        <DrawingViewer
          token={token}
          branch={branch}
          paCode={paCode}
          onClose={() => setFullscreen(false)}
        />
      ) : null}
    </section>
  );
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
    <div className={`pcp-pub__fact ${emphasis ? "pcp-pub__fact--emphasis" : ""}`}>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}
