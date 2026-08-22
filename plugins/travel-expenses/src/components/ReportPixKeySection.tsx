import type { ReportDetail } from "../api/travelExpensesApi";
import { formatPixKeyDisplay } from "../constants/pixKeyTypes";

export function ReportPixKeySection({ report }: { report: ReportDetail }) {
  const pix = formatPixKeyDisplay(report.pixKeyType, report.pixKeyValue);
  if (!pix) return null;

  return (
    <div className="te-doc-section">
      <h3 className="te-doc-section-title">PIX para ressarcimento</h3>
      <div className="te-doc-pix-key">
        <p className="te-doc-info">
          <strong>Tipo</strong>
          {pix.label}
        </p>
        <p className="te-doc-info">
          <strong>Chave</strong>
          {pix.value}
        </p>
      </div>
    </div>
  );
}
