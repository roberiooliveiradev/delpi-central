import { Database } from "lucide-react";

export function DataSourceBanner() {
  return (
    <aside className="dh-source-banner" role="note">
      <Database size={20} aria-hidden="true" />
      <div>
        <strong>Fonte: Portal RH</strong>
        <p>
          Absenteísmo, turnover, horas de treinamento, PDI e satisfação interna
          consolidados por filial no período selecionado.
        </p>
      </div>
    </aside>
  );
}
