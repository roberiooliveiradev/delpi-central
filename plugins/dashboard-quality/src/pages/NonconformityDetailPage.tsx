import { useMemo } from "react";
import { ArrowLeft } from "lucide-react";

import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { QualityNav } from "../components/QualityNav";
import { QUALITY_ROUTES } from "../constants/routes";
import type { Nonconformity } from "../types/nonconformity";
import { formatDisplayDate } from "../utils/dates";
import {
  formatCustomerRef,
  formatDecimal,
  formatNonconformityCode,
} from "../utils/format";
import {
  formatNonconformityStatusLabel,
  formatNonconformityTypeLabel,
} from "../utils/nonconformityLabels";
import { navigateQualityBack } from "../utils/navigation";
import { readNonconformityDetailRecord } from "../utils/recordDetailStorage";
import { readQualityFilters } from "../utils/filterUrl";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode } from "../utils/operationalUnitLabels";

type NonconformityDetailPageProps = {
  pathname?: string;
};

export function NonconformityDetailPage(_props: NonconformityDetailPageProps) {
  const item = useMemo(() => readNonconformityDetailRecord<Nonconformity>(), []);

  const fields = useMemo(
    () =>
      item
        ? [
            { label: "Tipo", value: formatNonconformityTypeLabel(item) },
            { label: OPERATIONAL_UNIT_COLUMN_LABEL, value: formatOperationalUnitCode(item.branch) },
            {
              label: "Código",
              value: formatNonconformityCode(item.code, item.code_display),
            },
            { label: "Revisão", value: item.revision },
            { label: "Status", value: formatNonconformityStatusLabel(item) },
            { label: "Item", value: item.item_code ?? "—" },
            { label: "OP", value: item.op_code ?? "—" },
            { label: "Descrição", value: item.description ?? "—", wide: true },
            {
              label: "Descrição detalhada",
              value: item.detailed_description ?? "—",
              wide: true,
            },
            {
              label: "Registro",
              value: formatDisplayDate(item.registered_date),
            },
            {
              label: "Ocorrência",
              value: formatDisplayDate(item.occurrence_date),
            },
            {
              label: "Cliente",
              value: formatCustomerRef(item.customer_code, item.customer_store),
            },
            { label: "Nome do cliente", value: item.customer_name ?? "—", wide: true },
            {
              label: "Qtd. devolvida",
              value: formatDecimal(item.returned_quantity),
            },
            {
              label: "Qtd. produzida",
              value: formatDecimal(item.produced_quantity),
            },
            { label: "Prioridade", value: item.priority_label ?? item.priority_code ?? "—" },
            { label: "Depto origem", value: item.origin_department ?? "—" },
            { label: "Depto destino", value: item.destination_department ?? "—" },
          ]
        : [],
    [item]
  );

  return (
    <div className="dashboard-quality dashboard-page dq-print-root">
      <QualityNav currentPath={QUALITY_ROUTES.nonconformities} />

      <header className="dq-page-header dq-detail-header">
        <div>
          <h1>
            {item
              ? formatNonconformityCode(item.code, item.code_display)
              : "Detalhe da não conformidade"}
          </h1>
          <p>
            {item
              ? [formatNonconformityTypeLabel(item), formatOperationalUnitCode(item.branch, ""), formatNonconformityStatusLabel(item)]
                  .filter(Boolean)
                  .join(" · ")
              : "Registro não encontrado. Volte à listagem e abra o item novamente."}
          </p>
        </div>
        <div className="dq-page-header__actions">
          <button
            type="button"
            className="dq-ghost-btn dq-no-print"
            onClick={() =>
              navigateQualityBack(QUALITY_ROUTES.nonconformities, readQualityFilters())
            }
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
