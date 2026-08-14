import { buildIssuanceSheet, type IssuanceSheetField } from "../../domain/issuanceSheet";
import type { IssuanceRequest } from "../../domain/types";
import { formatQuantity, formatTaxId } from "../format";
import { DetailFields } from "../kit";
import { CopyableValue } from "./CopyableValue";

type Props = {
  request: IssuanceRequest;
};

function displayValue(field: IssuanceSheetField): string {
  if (!field.value) return "";
  if (field.format === "taxId") return formatTaxId(field.value);
  if (field.format === "quantity") return formatQuantity(Number(field.value));
  return field.value;
}

function fieldNode(field: IssuanceSheetField) {
  const text = displayValue(field);
  if (field.copyable && field.value) {
    return (
      <CopyableValue value={field.copyValue ?? field.value} label={field.label}>
        {text}
      </CopyableValue>
    );
  }
  return text;
}

export function IssuanceProtheusSheet({ request }: Props) {
  const sections = buildIssuanceSheet(request);
  return (
    <div className="ii-sheet" data-testid="issuance-sheet">
      {sections.map((section) => (
        <section
          key={section.id}
          className={
            section.id === "extras" || section.id === "situation"
              ? "ii-card ii-sheet__full"
              : "ii-card"
          }
        >
          <h2>{section.title}</h2>
          <DetailFields
            fields={section.fields.map((field) => ({
              label: field.label,
              hint: field.hint,
              value: fieldNode(field) || undefined,
              wide: field.wide,
            }))}
          />
        </section>
      ))}
    </div>
  );
}
