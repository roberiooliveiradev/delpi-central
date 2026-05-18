import { Database } from "lucide-react";

export function TotvsSourceBanner() {
  return (
    <div className="dq-totvs-banner" role="note">
      <Database size={18} aria-hidden="true" />
      <div>
        <strong>Origem: TOTVS Protheus</strong>
        <p>
          Consulta analítica de não conformidades. Não confundir com o módulo de
          gestão de NC em PostgreSQL (workflow interno).
        </p>
      </div>
    </div>
  );
}
