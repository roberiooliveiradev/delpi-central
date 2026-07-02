import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ClipboardCheck,
  Copy,
  Download,
  Loader2,
  X,
} from "lucide-react";

import { getLabel } from "../api/qualityLabelsApi";
import type { AuditMetadata, QualityLabel } from "../types/qualityLabels";
import { formatOperationalUnit } from "../utils/operationalUnits";

type Props = {
  label: QualityLabel;
  onClose: () => void;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? (value as Array<Record<string, unknown>>) : [];
}

function text(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  return String(value);
}

const OP_FIELDS: { key: string; label: string }[] = [
  { key: "production_order", label: "OP" },
  { key: "order_number", label: "Pedido (C2_NUM)" },
  { key: "product_code", label: "Produto" },
  { key: "product_description", label: "Descrição" },
  { key: "product_type", label: "Tipo" },
  { key: "unit", label: "Unid. medida" },
  { key: "planned_qty", label: "Qtd. planejada" },
  { key: "produced_qty", label: "Qtd. produzida" },
  { key: "order_status", label: "Status" },
  { key: "issue_date", label: "Emissão" },
  { key: "due_date", label: "Previsão" },
  { key: "finish_date", label: "Encerramento" },
];

function countItems(section: Record<string, unknown> | null | undefined): number {
  if (!section) return 0;
  const items = asArray(section.items);
  if (items.length > 0) return items.length;
  const total = section.total;
  return typeof total === "number" ? total : 0;
}

export function AuditMetadataModal({ label, onClose }: Props) {
  const [metadata, setMetadata] = useState<AuditMetadata | null>(
    label.auditMetadata ?? null,
  );
  const [loading, setLoading] = useState(!label.auditMetadata);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [rawOpen, setRawOpen] = useState(false);

  useEffect(() => {
    if (label.auditMetadata) return;
    const controller = new AbortController();
    setLoading(true);
    getLabel(label.id, controller.signal)
      .then((detail) => setMetadata(detail.auditMetadata ?? {}))
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar auditoria.");
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [label.id, label.auditMetadata]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const order = asRecord(metadata?.productionOrder?.order);
  const linkSummary = asRecord(metadata?.productionOrder?.linkSummary);
  const product = metadata?.product ?? null;
  const structure = asRecord(product?.structure);
  const routing = asRecord(product?.routing);
  const inspection = asRecord(product?.inspection);
  const sources = metadata?.sources ?? [];
  const errors = metadata?.errors ?? [];

  const structureRoot = asRecord(structure.root);
  const inspectionItems = asArray(inspection.items);
  const inspectionWithTests = inspectionItems.filter((i) => i.has_inspection).length;

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(JSON.stringify(metadata ?? {}, null, 2));
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Não foi possível copiar o JSON.");
    }
  }

  function handleDownload() {
    const blob = new Blob([JSON.stringify(metadata ?? {}, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `auditoria-op-${label.productionOrder}-${label.productCode}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="ql-modal-overlay" onMouseDown={onClose}>
      <div
        className="ql-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Metadados de auditoria"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <header className="ql-modal__header">
          <div className="ql-modal__title">
            <ClipboardCheck className="ql-icon" />
            <div>
              <h2>Auditoria da inspeção</h2>
              <p>
                OP {label.productionOrder} · {label.productCode}
                {metadata?.capturedAt
                  ? ` · capturado em ${new Date(metadata.capturedAt).toLocaleString("pt-BR")}`
                  : ""}
              </p>
            </div>
          </div>
          <button type="button" className="ql-icon-btn" title="Fechar" onClick={onClose}>
            <X className="ql-icon" />
          </button>
        </header>

        <div className="ql-modal__body">
          {loading ? (
            <div className="ql-state">
              <p>
                <Loader2 className="ql-icon ql-spin" /> Carregando snapshot...
              </p>
            </div>
          ) : error ? (
            <div className="ql-state ql-state--error"><p>{error}</p></div>
          ) : !metadata || Object.keys(metadata).length === 0 ? (
            <div className="ql-state">
              <p>Sem metadados de auditoria para esta etiqueta.</p>
            </div>
          ) : (
            <>
              {errors.length > 0 && (
                <div className="ql-warning">
                  <AlertTriangle className="ql-icon" />
                  <div>
                    <p className="ql-warning__title">
                      Captura parcial: algumas fontes falharam.
                    </p>
                    <ul className="ql-warning__list">
                      {errors.map((err, idx) => (
                        <li key={idx}>
                          {err.operationId}: {err.message}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              <section className="ql-audit-section">
                <h3 className="ql-audit-section__title">Ordem de produção</h3>
                <dl className="ql-audit-grid">
                  {OP_FIELDS.map((field) => (
                    <div key={field.key} className="ql-audit-grid__item">
                      <dt>{field.label}</dt>
                      <dd>
                        {field.key === "production_order"
                          ? text(order[field.key])
                          : text(order[field.key])}
                      </dd>
                    </div>
                  ))}
                  <div className="ql-audit-grid__item">
                    <dt>Unidade</dt>
                    <dd>{formatOperationalUnit(order.branch as string | null)}</dd>
                  </div>
                  <div className="ql-audit-grid__item">
                    <dt>OPs vinculadas (PI)</dt>
                    <dd>{text(linkSummary.total_pi_orders)}</dd>
                  </div>
                </dl>
              </section>

              <section className="ql-audit-cards">
                <div className="ql-audit-card">
                  <span className="ql-audit-card__value">{countItems(structure)}</span>
                  <span className="ql-audit-card__label">Itens da estrutura (BOM)</span>
                  {structureRoot.code ? (
                    <span className="ql-audit-card__meta">
                      Raiz: {text(structureRoot.code)}
                    </span>
                  ) : null}
                </div>
                <div className="ql-audit-card">
                  <span className="ql-audit-card__value">{countItems(routing)}</span>
                  <span className="ql-audit-card__label">Operações do roteiro</span>
                </div>
                <div className="ql-audit-card">
                  <span className="ql-audit-card__value">
                    {inspectionWithTests}/{inspectionItems.length || countItems(inspection)}
                  </span>
                  <span className="ql-audit-card__label">Itens com inspeção</span>
                </div>
              </section>

              <section className="ql-audit-section">
                <h3 className="ql-audit-section__title">Fontes do snapshot</h3>
                <table className="ql-audit-sources">
                  <thead>
                    <tr>
                      <th>Operação</th>
                      <th>Situação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sources.map((source, idx) => (
                      <tr key={idx}>
                        <td>{source.operationId}</td>
                        <td>
                          <span
                            className={`ql-badge ${source.ok ? "ql-badge--on" : "ql-badge--off"}`}
                          >
                            {source.ok ? "OK" : "Falha"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </section>

              <details
                className="ql-audit-raw"
                open={rawOpen}
                onToggle={(e) => setRawOpen((e.target as HTMLDetailsElement).open)}
              >
                <summary>JSON completo (auditoria)</summary>
                <pre className="ql-audit-json">
                  {JSON.stringify(metadata, null, 2)}
                </pre>
              </details>
            </>
          )}
        </div>

        <footer className="ql-modal__footer">
          <button
            type="button"
            className="ql-btn ql-btn--ghost"
            onClick={handleCopy}
            disabled={!metadata}
          >
            <Copy className="ql-icon" /> {copied ? "Copiado!" : "Copiar JSON"}
          </button>
          <button
            type="button"
            className="ql-btn ql-btn--ghost"
            onClick={handleDownload}
            disabled={!metadata}
          >
            <Download className="ql-icon" /> Baixar JSON
          </button>
        </footer>
      </div>
    </div>
  );
}
