import { useEffect, useState } from "react";
import type { PublicInspection } from "./api";
import "./inspection.css";

const RESULT_META: Record<string, { label: string; tone: string }> = {
  approved: { label: "Aprovado pela Qualidade", tone: "ok" },
  conditional: { label: "Aprovado com ressalvas", tone: "warn" },
  rejected: { label: "Reprovado", tone: "bad" },
};

function formatDate(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleDateString("pt-BR");
}

export function InspectionView({ inspection }: { inspection: PublicInspection }) {
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setRevealed(true), 120);
    return () => window.clearTimeout(timer);
  }, []);

  const meta = RESULT_META[inspection.result] ?? { label: "Inspeção da Qualidade", tone: "ok" };

  return (
    <div className={`qlp-card${revealed ? " is-revealed" : ""}`}>
      <span className="qlp-eyebrow">Controle da Qualidade · {inspection.companyName}</span>

      <div className={`qlp-seal qlp-seal--${meta.tone}`}>
        <span className="qlp-seal__check">✓</span>
        {meta.label}
      </div>

      <h1 className="qlp-product">{inspection.productCode}</h1>
      <p className="qlp-desc">{inspection.productDescription}</p>

      <dl className="qlp-details">
        <div className="qlp-detail">
          <dt>Ordem de produção</dt>
          <dd>{inspection.productionOrder}</dd>
        </div>
        {inspection.branch && (
          <div className="qlp-detail">
            <dt>Filial</dt>
            <dd>{inspection.branch}</dd>
          </div>
        )}
        {inspection.productUnit && (
          <div className="qlp-detail">
            <dt>Unidade</dt>
            <dd>{inspection.productUnit}</dd>
          </div>
        )}
        <div className="qlp-detail">
          <dt>Data da inspeção</dt>
          <dd>{formatDate(inspection.inspectedAt)}</dd>
        </div>
        <div className="qlp-detail">
          <dt>Inspetor responsável</dt>
          <dd>{inspection.inspectorName}</dd>
        </div>
      </dl>

      <p className="qlp-footer">
        Este produto passou pela inspeção de qualidade da {inspection.companyName}.
      </p>
    </div>
  );
}
