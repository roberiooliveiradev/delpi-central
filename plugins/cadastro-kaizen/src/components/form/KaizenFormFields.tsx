import { FormSection } from "./FormSection";
import { KaizenParticipantsField } from "./KaizenParticipantsField";
import { FieldLabel } from "../ui/HelpTooltip";
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

export function KaizenFormFields({ values, onChange }: KaizenFormFieldsProps) {
  return (
    <>
      <FormSection title="Identificação">
        <div className="kz-field">
          <label htmlFor="kz-branch">Filial *</label>
          <select
            id="kz-branch"
            required
            value={values.branch_code}
            onChange={(event) => onChange("branch_code", event.target.value)}
          >
            {BRANCHES.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="kz-field">
          <FieldLabel label="Status" htmlFor="kz-status" hint={KAIZEN_HELP_TOOLTIPS.fields.status} />
          <select
            id="kz-status"
            value={values.status}
            onChange={(event) =>
              onChange("status", event.target.value as KaizenFormValues["status"])
            }
          >
            {KAIZEN_STATUSES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="kz-field kz-span-2">
          <FieldLabel label="Título *" htmlFor="kz-title" hint={KAIZEN_HELP_TOOLTIPS.fields.title} />
          <input
            id="kz-title"
            required
            value={values.title}
            maxLength={500}
            onChange={(event) => onChange("title", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-sector">Área / setor</label>
          <input
            id="kz-sector"
            value={values.sector}
            onChange={(event) => onChange("sector", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <FieldLabel
            label="Categoria"
            htmlFor="kz-category"
            hint={KAIZEN_HELP_TOOLTIPS.fields.category}
          />
          <select
            id="kz-category"
            value={values.category}
            onChange={(event) => onChange("category", event.target.value)}
          >
            <option value="">Sem categoria</option>
            {KAIZEN_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div className="kz-field">
          <label htmlFor="kz-investment">Investimento (R$)</label>
          <input
            id="kz-investment"
            value={values.investment}
            onChange={(event) => onChange("investment", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <FieldLabel
            label="Data implantação"
            htmlFor="kz-date-implemented"
            hint={KAIZEN_HELP_TOOLTIPS.fields.dateImplemented}
          />
          <input
            id="kz-date-implemented"
            type="date"
            value={values.date_implemented}
            onChange={(event) => onChange("date_implemented", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-date-discontinued">Data descontinuação</label>
          <input
            id="kz-date-discontinued"
            type="date"
            value={values.date_discontinued}
            onChange={(event) => onChange("date_discontinued", event.target.value)}
          />
        </div>

        <div className="kz-field kz-span-2">
          <label>Equipe / responsáveis</label>
          <KaizenParticipantsField
            participants={values.participants}
            onChange={(participants) => onChange("participants", participants)}
          />
        </div>

        <div className="kz-field kz-span-2">
          <FieldLabel
            label="Descrição do processo"
            htmlFor="kz-process"
            hint={KAIZEN_HELP_TOOLTIPS.fields.processDescription}
          />
          <textarea
            id="kz-process"
            value={values.process_description}
            onChange={(event) => onChange("process_description", event.target.value)}
          />
        </div>

        <div className="kz-field kz-span-2">
          <FieldLabel
            label="Melhoria realizada"
            htmlFor="kz-improvement"
            hint={KAIZEN_HELP_TOOLTIPS.fields.improvementDescription}
          />
          <textarea
            id="kz-improvement"
            value={values.improvement_description}
            onChange={(event) => onChange("improvement_description", event.target.value)}
          />
        </div>
      </FormSection>

      <FormSection title="Economia">
        <div className="kz-field">
          <FieldLabel
            label="Tipo de economia"
            htmlFor="kz-savings-type"
            hint={KAIZEN_HELP_TOOLTIPS.fields.savingsType}
          />
          <select
            id="kz-savings-type"
            value={values.savings_type}
            onChange={(event) =>
              onChange("savings_type", event.target.value as KaizenFormValues["savings_type"])
            }
          >
            <option value="">Inferir automaticamente</option>
            {SAVINGS_TYPES.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </div>

        <div className="kz-field">
          <label htmlFor="kz-seconds">Segundos por ocorrência</label>
          <input
            id="kz-seconds"
            value={values.seconds_per_occurrence}
            onChange={(event) => onChange("seconds_per_occurrence", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-occurrences">Ocorrências por dia</label>
          <input
            id="kz-occurrences"
            value={values.occurrences_per_day}
            onChange={(event) => onChange("occurrences_per_day", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-hourly-cost">Custo hora (R$)</label>
          <input
            id="kz-hourly-cost"
            value={values.hourly_cost}
            onChange={(event) => onChange("hourly_cost", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-quantity">Quantidade economizada/dia</label>
          <input
            id="kz-quantity"
            value={values.quantity_saved_per_day}
            onChange={(event) => onChange("quantity_saved_per_day", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-unit-cost">Custo unitário material (R$)</label>
          <input
            id="kz-unit-cost"
            value={values.unit_material_cost}
            onChange={(event) => onChange("unit_material_cost", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <label htmlFor="kz-fixed-savings">Economia fixa/dia (R$)</label>
          <input
            id="kz-fixed-savings"
            value={values.fixed_daily_savings}
            onChange={(event) => onChange("fixed_daily_savings", event.target.value)}
          />
        </div>

        <div className="kz-field">
          <FieldLabel
            label="Economia realizada/dia (R$)"
            htmlFor="kz-realized-savings"
            hint={KAIZEN_HELP_TOOLTIPS.fields.realizedDailySavings}
          />
          <input
            id="kz-realized-savings"
            value={values.realized_daily_savings}
            onChange={(event) => onChange("realized_daily_savings", event.target.value)}
          />
        </div>
      </FormSection>

      <section>
        <h2 className="kz-section-title">Observações</h2>
        <div className="kz-field">
          <label htmlFor="kz-notes">Notas</label>
          <textarea
            id="kz-notes"
            value={values.notes}
            onChange={(event) => onChange("notes", event.target.value)}
          />
        </div>
      </section>
    </>
  );
}