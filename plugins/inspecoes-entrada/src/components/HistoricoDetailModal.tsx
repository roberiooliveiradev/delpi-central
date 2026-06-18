import { useEffect, useState } from "react";
import { ChevronDown, Printer, X } from "lucide-react";

import { useInspecoesEntradaHistoricoDetalhe } from "../hooks/useInspecoesEntradaHistoricoDetalhe";
import type { InspecoesEntradaHistoricoDetalheSummary } from "../types/inspecoesEntradaHistoricoDetalhe";
import { formatDateTimePt, formatNumber, formatText } from "../utils/format";
import { formatCertificateProductLabel } from "../utils/certificateFormat";
import { printQualityCertificate } from "../utils/qualityCertificatePrint";
import { buildTestTitle } from "../utils/testMeasurementDisplay";
import { resolveResultBadge } from "../utils/resultBadge";
import { InspecaoTestCard } from "./InspecaoTestCard";
import { ResultBadge } from "./ResultBadge";

type HistoricoDetailModalProps = {
  branch: string;
  inspectionId: string | null;
  onClose: () => void;
};

function buildInspectorLabel(summary: InspecoesEntradaHistoricoDetalheSummary): string {
  return formatText(summary.inspector_name);
}

export function HistoricoDetailModal({
  branch,
  inspectionId,
  onClose,
}: HistoricoDetailModalProps) {
  const { data, loading, error, reload } = useInspecoesEntradaHistoricoDetalhe(
    branch,
    inspectionId,
  );
  const [printError, setPrintError] = useState<{ inspectionId: string; message: string } | null>(
    null,
  );

  useEffect(() => {
    if (!inspectionId) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    document.addEventListener("keydown", handleKeyDown);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [inspectionId, onClose]);

  if (!inspectionId) return null;

  const summary = data?.summary;
  const tests = data?.tests ?? [];
  const totals = data?.totals;
  const canPrintCertificate = Boolean(!loading && !error && data);
  const visiblePrintError =
    printError && printError.inspectionId === inspectionId ? printError.message : null;

  function handlePrintCertificate() {
    if (!data || !inspectionId) return;

    const result = printQualityCertificate(data);
    if (!result.success) {
      setPrintError({
        inspectionId,
        message: result.error ?? "Não foi possível abrir a impressão do certificado.",
      });
      return;
    }

    setPrintError(null);
  }

  return (
    <div className="ie-modal" role="dialog" aria-modal="true" aria-label="Detalhes da inspeção">
      <button
        className="ie-modal__backdrop"
        type="button"
        onClick={onClose}
        aria-label="Fechar modal"
      />
      <div className="ie-modal__panel ie-modal__panel--detail">
        <header className="ie-modal__header">
          <div className="ie-modal-detail__heading">
            {summary ? (
              <>
                <div className="ie-modal-detail__title-row">
                  <ResultBadge badge={resolveResultBadge(summary.result)} />
                  <h2>
                    NF {formatText(summary.invoice_number)} · Série {formatText(summary.invoice_series)} · Item{" "}
                    {formatText(summary.invoice_item)}
                  </h2>
                </div>
                <p className="ie-modal-detail__supplier">{formatText(summary.supplier_name)}</p>
                <p className="ie-modal-detail__meta">
                  Produto {formatCertificateProductLabel(summary)} · Lote {formatText(summary.lot)} ·{" "}
                  {formatNumber(summary.quantity)} {formatText(summary.unit)}
                </p>
                <p className="ie-modal-detail__meta">
                  Laudo em {formatDateTimePt(summary.report_date, summary.report_time)} por{" "}
                  {buildInspectorLabel(summary)}
                </p>
              </>
            ) : (
              <h2>Detalhes da inspeção</h2>
            )}
          </div>
          <div className="ie-modal__header-actions">
            <button
              type="button"
              className="ie-btn ie-btn--primary ie-btn--sm"
              disabled={!canPrintCertificate}
              onClick={handlePrintCertificate}
            >
              <Printer size={16} aria-hidden="true" />
              Imprimir certificado
            </button>
            <button className="ie-btn ie-btn--ghost ie-modal__close" type="button" onClick={onClose}>
              <X size={16} aria-hidden="true" />
              Fechar
            </button>
          </div>
        </header>

        <div className="ie-modal__body">
          {visiblePrintError ? (
            <div className="ie-alert ie-alert--error" role="alert">
              <p>{visiblePrintError}</p>
            </div>
          ) : null}
          {loading ? (
            <div className="ie-state-box ie-state-box--compact" role="status">
              Carregando detalhe da inspeção…
            </div>
          ) : null}

          {!loading && error ? (
            <div className="ie-alert ie-alert--error" role="alert">
              <p>{error}</p>
              <button type="button" className="ie-btn ie-btn--ghost" onClick={reload}>
                Tentar novamente
              </button>
            </div>
          ) : null}

          {!loading && !error && summary && totals ? (
            <>
              <div className="ie-modal-detail__chips" aria-label="Resumo da inspeção">
                <div className="ie-modal-detail__chip">
                  <span>Ensaios</span>
                  <strong>{totals.tests_count.toLocaleString("pt-BR")}</strong>
                </div>
                <div className="ie-modal-detail__chip ie-modal-detail__chip--danger">
                  <span>Reprovados</span>
                  <strong>{totals.failed_tests_count.toLocaleString("pt-BR")}</strong>
                </div>
                <div className="ie-modal-detail__chip">
                  <span>Qtd. aprovada</span>
                  <strong>{formatNumber(summary.approved_quantity)}</strong>
                </div>
                <div className="ie-modal-detail__chip">
                  <span>Qtd. rejeitada</span>
                  <strong>{formatNumber(summary.rejected_quantity)}</strong>
                </div>
              </div>

              <section className="ie-modal-detail__section" aria-label="Ensaios da inspeção">
                <h3>Ensaios da inspeção</h3>
                {tests.length === 0 ? (
                  <div className="ie-state-box ie-state-box--compact">
                    Nenhum ensaio registrado para esta inspeção.
                  </div>
                ) : (
                  <div className="ie-test-card-list">
                    {tests.map((test) => (
                      <InspecaoTestCard
                        key={`${test.test_code}-${test.measurement_date}-${test.measurement_time}-${test.result_code}-${test.qer_key ?? ""}`}
                        test={test}
                      />
                    ))}
                  </div>
                )}
              </section>

              <details className="ie-modal-detail__technical" key={inspectionId}>
                <summary>
                  <span>Ver dados técnicos</span>
                  <ChevronDown size={16} aria-hidden="true" />
                </summary>
                <dl className="ie-detail-grid">
                  <div>
                    <dt>ID da inspeção</dt>
                    <dd>{formatText(data?.inspection_id)}</dd>
                  </div>
                  <div>
                    <dt>Status inspeção</dt>
                    <dd>{formatText(summary.inspection_status)}</dd>
                  </div>
                  <div>
                    <dt>Código laudo</dt>
                    <dd>{formatText(summary.report_code)}</dd>
                  </div>
                  <div>
                    <dt>Fornecedor</dt>
                    <dd>
                      {formatText(summary.supplier_code)}/{formatText(summary.supplier_store)}
                    </dd>
                  </div>
                  <div>
                    <dt>Matrícula ensaiador (laudo)</dt>
                    <dd>{formatText(summary.inspector_registration)}</dd>
                  </div>
                  <div>
                    <dt>Login ensaiador (laudo)</dt>
                    <dd>{formatText(summary.inspector_login)}</dd>
                  </div>
                </dl>

                {tests.length > 0 ? (
                  <div className="ie-modal-detail__technical-tests">
                    <h4>Dados técnicos por ensaio</h4>
                    <ul className="ie-technical-test-list">
                      {tests.map((test) => (
                        <li key={`tech-${test.test_code}-${test.qer_key ?? ""}`}>
                          <strong>{buildTestTitle(test)}</strong>
                          <span>
                            {test.qer_key ? `Chave ${formatText(test.qer_key)}` : "—"}
                            {test.sequence_number ? ` · Seq. ${formatText(test.sequence_number)}` : ""}
                            {test.laboratory ? ` · Lab. ${formatText(test.laboratory)}` : ""}
                            {test.sample_number !== null
                              ? ` · Amostra ${test.sample_number.toLocaleString("pt-BR")}`
                              : ""}
                            {test.measurement_source
                              ? ` · Fonte ${formatText(test.measurement_source)}`
                              : ""}
                            {test.numeric_measurement_indicator
                              ? ` · Ind. ${formatText(test.numeric_measurement_indicator)}`
                              : ""}
                            {test.inspector_registration
                              ? ` · Mat. ${formatText(test.inspector_registration)}`
                              : ""}
                            {test.inspector_login ? ` · Login ${formatText(test.inspector_login)}` : ""}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </details>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
