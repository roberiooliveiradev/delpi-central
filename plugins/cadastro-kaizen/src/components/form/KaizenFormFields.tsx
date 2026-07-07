import { FormSection } from "./FormSection";
import { SelectField, TextAreaField, TextField } from "./FormField";
import { KaizenParticipantsField } from "./KaizenParticipantsField";
import { SavingsParamFields } from "./SavingsParamFields";
import { FieldLabel } from "@delpi/plugin-ui";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  BRANCHES,
  KAIZEN_CATEGORIES,
  KAIZEN_STATUSES,
  SAVINGS_TYPES,
} from "../../constants/kaizen";
import type { KaizenFormValues } from "../../types/kaizen";

type KaizenFormFieldsProps = {
  values: KaizenFormValues;
  onChange: <K extends keyof KaizenFormValues>(key: K, value: KaizenFormValues[K]) => void;
};

const BRANCH_OPTIONS = BRANCHES.map((item) => ({ value: item.code, label: item.label }));
const CATEGORY_OPTIONS = KAIZEN_CATEGORIES.map((cat) => ({ value: cat, label: cat }));

export function KaizenFormFields({ values, onChange }: KaizenFormFieldsProps) {
  const isQualitative = values.savings_type === "qualitativo";

  return (
    <>
      <FormSection
        title="Identificação"
        hint={KAIZEN_HELP_TOOLTIPS.sections.identification}
        description="Unidade, título, equipe e descrição do processo"
      >
        <SelectField
          id="kz-branch"
          label="Unidade *"
          hint={KAIZEN_HELP_TOOLTIPS.fields.branch}
          required
          value={values.branch_code}
          onChange={(value) => onChange("branch_code", value)}
          options={BRANCH_OPTIONS}
        />

        <SelectField
          id="kz-status"
          label="Status"
          hint={KAIZEN_HELP_TOOLTIPS.fields.status}
          value={values.status}
          onChange={(value) => onChange("status", value as KaizenFormValues["status"])}
          options={KAIZEN_STATUSES}
        />

        <TextField
          id="kz-title"
          label="Título *"
          hint={KAIZEN_HELP_TOOLTIPS.fields.title}
          span
          required
          maxLength={500}
          value={values.title}
          onChange={(value) => onChange("title", value)}
        />

        <TextField
          id="kz-sector"
          label="Área / setor"
          hint={KAIZEN_HELP_TOOLTIPS.fields.sector}
          value={values.sector}
          onChange={(value) => onChange("sector", value)}
        />

        <SelectField
          id="kz-category"
          label="Categoria"
          hint={KAIZEN_HELP_TOOLTIPS.fields.category}
          value={values.category}
          onChange={(value) => onChange("category", value)}
          options={CATEGORY_OPTIONS}
          placeholderOption="Sem categoria"
        />

        <TextField
          id="kz-investment"
          label="Investimento (R$)"
          hint={KAIZEN_HELP_TOOLTIPS.fields.investment}
          inputMode="decimal"
          value={values.investment}
          onChange={(value) => onChange("investment", value)}
        />

        <TextField
          id="kz-date-implemented"
          label="Data implantação"
          hint={KAIZEN_HELP_TOOLTIPS.fields.dateImplemented}
          type="date"
          value={values.date_implemented}
          onChange={(value) => onChange("date_implemented", value)}
        />

        <TextField
          id="kz-date-discontinued"
          label="Data descontinuação"
          hint={KAIZEN_HELP_TOOLTIPS.fields.dateDiscontinued}
          type="date"
          value={values.date_discontinued}
          onChange={(value) => onChange("date_discontinued", value)}
        />

        <div className="kz-field kz-span-2">
          <FieldLabel label="Equipe / responsáveis" hint={KAIZEN_HELP_TOOLTIPS.sections.participants}  className="kz-field__label" />
          <KaizenParticipantsField
            participants={values.participants}
            onChange={(participants) => onChange("participants", participants)}
          />
        </div>

        <TextAreaField
          id="kz-process"
          label="Descrição do processo"
          hint={KAIZEN_HELP_TOOLTIPS.fields.processDescription}
          value={values.process_description}
          onChange={(value) => onChange("process_description", value)}
        />

        <TextAreaField
          id="kz-problem"
          label="Problema / oportunidade"
          hint={KAIZEN_HELP_TOOLTIPS.fields.problemDescription}
          value={values.problem_description}
          onChange={(value) => onChange("problem_description", value)}
        />

        <TextAreaField
          id="kz-improvement"
          label="Melhoria realizada"
          hint={KAIZEN_HELP_TOOLTIPS.fields.improvementDescription}
          value={values.improvement_description}
          onChange={(value) => onChange("improvement_description", value)}
        />

        <TextAreaField
          id="kz-expected"
          label="Resultado esperado"
          hint={KAIZEN_HELP_TOOLTIPS.fields.expectedResult}
          value={values.expected_result}
          onChange={(value) => onChange("expected_result", value)}
        />
      </FormSection>

      <FormSection
        title="Economia"
        hint={KAIZEN_HELP_TOOLTIPS.sections.savings}
        description="Escolha o tipo — só os parâmetros que se aplicam a ele aparecem."
      >
        <SelectField
          id="kz-savings-type"
          label="Tipo de economia"
          hint={KAIZEN_HELP_TOOLTIPS.fields.savingsType}
          value={values.savings_type}
          onChange={(value) => onChange("savings_type", value as KaizenFormValues["savings_type"])}
          options={SAVINGS_TYPES}
          placeholderOption="Inferir automaticamente"
        />

        <SavingsParamFields
          savingsType={values.savings_type}
          values={values}
          onChange={(field, value) => onChange(field, value)}
          idPrefix="kz-new"
        />

        <TextField
          id="kz-realized-savings"
          label="Economia realizada/dia (R$)"
          hint={KAIZEN_HELP_TOOLTIPS.fields.realizedDailySavings}
          inputMode="decimal"
          value={values.realized_daily_savings}
          onChange={(value) => onChange("realized_daily_savings", value)}
        />

        {isQualitative ? (
          <p className="kz-field kz-span-2 kz-form-note">
            Economia qualitativa não gera cálculo monetário automático. Informe a economia
            realizada/dia se houver um valor medido.
          </p>
        ) : null}
      </FormSection>

      <FormSection title="Observações" description="Notas livres sobre o kaizen">
        <TextAreaField
          id="kz-notes"
          label="Notas"
          hint={KAIZEN_HELP_TOOLTIPS.fields.notes}
          value={values.notes}
          onChange={(value) => onChange("notes", value)}
        />
      </FormSection>
    </>
  );
}
