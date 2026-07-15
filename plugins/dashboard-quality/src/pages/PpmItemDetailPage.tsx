import { GHOST_BTN } from "../ui/ghostChrome";
import { useMemo } from "react";
import { ArrowLeft } from "lucide-react";

import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { QualityNav } from "../components/QualityNav";
import { QUALITY_ROUTES } from "../constants/routes";
import type { PpmItem } from "../types/ppm";
import { formatDisplayDate } from "../utils/dates";
import {
  formatCustomerRef,
  formatDecimal,
  formatNonconformityCode,
} from "../utils/format";
import { navigateQualityBack } from "../utils/navigation";
import { readPpmDetailRecord } from "../utils/recordDetailStorage";
import { readQualityFilters } from "../utils/filterUrl";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

type PpmItemDetailPageProps = {
  pathname?: string;
};

export function PpmItemDetailPage(_props: PpmItemDetailPageProps) {
  const item = useMemo(() => readPpmDetailRecord<PpmItem>(), []);

  const fields = useMemo(
    () =>
      item
        ? [
            { label: OPERATIONAL_UNIT_COLUMN_LABEL, value: formatOperationalUnitCode(item.branch) },
            {
              label: "Data de registro",
              value: formatDisplayDate(item.registered_date),
            },
            {
              label: "Código",
              value: formatNonconformityCode(item.code, item.code_display),
            },
            { label: "Revisão", value: item.revision },
            { label: "Item", value: item.item_code ?? "—" },
            { label: "Descrição", value: item.description ?? "—", wide: true },
            {
              label: "Descrição detalhada",
              value: item.detailed_description ?? "—",
              wide: true,
            },
            {
              label: "Cliente",
              value: formatCustomerRef(item.customer_code, item.customer_store),
            },
            { label: "Nome do cliente", value: item.customer_name ?? "—", wide: true },
            {
              label: "Qtd. devolvida (un)",
              value: formatDecimal(item.returned_quantity_un),
            },
            {
              label: "Qtd. devolvida (original)",
              value: item.returned_quantity_original ?? "—",
            },
          ]
        : [],
    [item]
  );

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityNav currentPath={QUALITY_ROUTES.ppm} />

      <header className="dq-page-header dq-detail-header">
        <div>
          <h1>{item ? formatNonconformityCode(item.code, item.code_display) : "Detalhe PPM"}</h1>
          <p>
            {item
              ? [item.branch, item.item_code, formatDisplayDate(item.registered_date)]
                  .filter(Boolean)
                  .join(" · ")
              : "Registro não encontrado. Volte à listagem e abra o item novamente."}
          </p>
        </div>
        <div className="dq-page-header__actions">
          <button
            type="button"
            className={`${GHOST_BTN} dq-no-print`}
            onClick={() => navigateQualityBack(QUALITY_ROUTES.ppm, readQualityFilters())}
          >
            <ArrowLeft size={16} />
            Voltar
          </button>
        </div>
      </header>

      {item ? (
        <section className="dq-detail-layout">
          <article className="dq-card dq-detail-card">
            <h2 className="dq-section-title">Dados do registro</h2>
            <DetailFieldGrid fields={fields} />
          </article>
        </section>
      ) : null}
    </div>
  );
}
