import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { schemaPayloadFields } from "../domain/schemaPayload";
import type { RequestTypeSummary } from "../types/requests";
import { DetailFields, MyRequestsSectionCard } from "../ui/mrUi";

type SchemaPayloadCardProps = {
  requestType: RequestTypeSummary | null | undefined;
  payload: Record<string, unknown> | null | undefined;
};

/** Card genérico do formulário schema-driven — título/labels vêm do tipo. */
export function SchemaPayloadCard({
  requestType,
  payload,
}: SchemaPayloadCardProps) {
  const fields = schemaPayloadFields(requestType, payload);
  if (!fields.length) return null;
  return (
    <MyRequestsSectionCard
      title="Dados do formulário"
      hint={MY_REQUESTS_HELP_TOOLTIPS.detail.formData}
    >
      <DetailFields
        fields={fields.map((field) => ({
          label: field.label,
          hint: field.hint,
          value: field.value,
        }))}
      />
    </MyRequestsSectionCard>
  );
}
