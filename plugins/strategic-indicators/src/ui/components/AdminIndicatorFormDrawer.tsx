import { SectionHintLabel } from "@delpi/plugin-ui/index";
import { useEffect, useState } from "react";
import type {
  AdminDepartmentIndicatorItem,
  BranchValueAggregation,
  CreateAdminDepartmentIndicatorRequest,
  UpdateAdminDepartmentIndicatorRequest,
} from "../../data/types/settings";
import { SI_HELP } from "../../content/helpTooltips";
import {
  getBranchValueAggregationLabel,
  getPerformanceDirectionLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import { validateIndicatorSourceKey } from "../utils/indicatorSourceKeyValidation";
import { ActiveToggle } from "./ActiveToggle";
import { DrawerPanel } from "./DrawerPanel";
import { SiAdminFormField } from "./SiAdminFormField";
import { SI_VALUE_UNIT_OPTIONS, SiSelectControl } from "./siFiltersUi";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";
import "./AdminIndicatorFormDrawer.css";

const BRANCH_AGGREGATION_HELP = {
  auto: SI_HELP.badges.branchAggregationAuto,
  sum: SI_HELP.badges.branchAggregationSum,
  average: SI_HELP.badges.branchAggregationAverage,
  source_consolidated: SI_HELP.badges.branchAggregationSource,
} as const;

export type IndicatorFormState = {
  indicator_id: string;
  indicator_name: string;
  weight_pct: number;
  scope_type: "consolidated" | "per_unit";
  performance_direction: "higher_is_better" | "lower_is_better";
  strategic_description: string;
  source_key: string;
  value_unit: string;
  value_prefix: string;
  value_suffix: string;
  value_decimals: number;
  branch_value_aggregation: BranchValueAggregation;
  display_order: number;
  is_active: boolean;
};

export const emptyIndicatorForm: IndicatorFormState = {
  indicator_id: "",
  indicator_name: "",
  weight_pct: 0,
  scope_type: "consolidated",
  performance_direction: "higher_is_better",
  strategic_description: "",
  source_key: "",
  value_unit: "",
  value_prefix: "",
  value_suffix: "",
  value_decimals: 2,
  branch_value_aggregation: "auto",
  display_order: 0,
  is_active: true,
};

export function indicatorFormFromItem(item: AdminDepartmentIndicatorItem): IndicatorFormState {
  return {
    indicator_id: item.indicator_id,
    indicator_name: item.indicator_name,
    weight_pct: item.weight_pct,
    scope_type: item.scope_type,
    performance_direction: item.performance_direction,
    strategic_description: item.strategic_description,
    source_key: item.source_key ?? "",
    value_unit: item.value_unit ?? "",
    value_prefix: item.value_prefix ?? "",
    value_suffix: item.value_suffix ?? "",
    value_decimals: Number(item.value_decimals ?? 2),
    branch_value_aggregation: item.branch_value_aggregation ?? "auto",
    display_order: item.display_order,
    is_active: item.is_active,
  };
}

type AdminIndicatorFormDrawerProps = {
  open: boolean;
  mode: "create" | "edit";
  saving: boolean;
  form: IndicatorFormState;
  formError: string | null;
  onClose: () => void;
  onChange: (next: IndicatorFormState) => void;
  onSubmit: () => Promise<void>;
};

function validateEssentialStep(form: IndicatorFormState, mode: "create" | "edit"): string | null {
  if (!form.indicator_name.trim()) {
    return "Informe o nome do indicador.";
  }
  if (mode === "create" && !form.indicator_id.trim()) {
    return "Informe o ID técnico do indicador.";
  }
  return validateIndicatorSourceKey(
    form.source_key,
    mode === "create" ? true : form.is_active,
  );
}

export function AdminIndicatorFormDrawer({
  open,
  mode,
  saving,
  form,
  formError,
  onClose,
  onChange,
  onSubmit,
}: AdminIndicatorFormDrawerProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setStep(1);
      setLocalError(null);
    }
  }, [open, mode]);

  const errorMessage = localError ?? formError;

  function patchForm(patch: Partial<IndicatorFormState>) {
    onChange({ ...form, ...patch });
  }

  function handleContinue() {
    const validationError = validateEssentialStep(form, mode);
    if (validationError) {
      setLocalError(validationError);
      return;
    }
    setLocalError(null);
    setStep(2);
  }

  async function handleSave() {
    const validationError = validateEssentialStep(form, mode);
    if (validationError) {
      setLocalError(validationError);
      setStep(1);
      return;
    }
    setLocalError(null);
    await onSubmit();
  }

  const title =
    mode === "create" ? "Novo indicador estrutural" : "Editar indicador estrutural";

  return (
    <DrawerPanel
      open={open}
      onClose={onClose}
      title={title}
      description={`Passo ${step} de 2 — ${step === 1 ? "Essencial" : "Formato e avançado"}`}
      size="xl"
      footer={
        step === 1 ? (
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={onClose}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={handleContinue}
              disabled={saving}
            >
              Continuar →
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => {
                setLocalError(null);
                setStep(1);
              }}
              disabled={saving}
            >
              ← Voltar
            </button>
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSave()}
              disabled={saving}
            >
              {saving ? "Salvando..." : "Salvar indicador"}
            </button>
          </>
        )
      }
    >
      {errorMessage ? (
        <p className="si-settings-editor__alert si-settings-editor__alert--error">
          {errorMessage}
        </p>
      ) : null}

      {step === 1 ? (
        <div className="si-admin-form-grid">
          <SectionHintLabel
            label="Essencial"
            hint={SI_HELP.indicator.sectionEssential}
            className="si-admin-form-grid__section-title si-admin-form-grid__section-title--full"
          />

          <SiAdminFormField label="Nome" hint={SI_HELP.indicator.indicatorName}>
            <SiNativeTextControl
              value={form.indicator_name}
              onChange={(value) => patchForm({ indicator_name: value })}
            />
          </SiAdminFormField>

          <SiAdminFormField label="ID" hint={SI_HELP.indicator.indicatorId}>
            <SiNativeTextControl
              value={form.indicator_id}
              disabled={mode === "edit"}
              onChange={(value) => patchForm({ indicator_id: value })}
            />
          </SiAdminFormField>

          <SiAdminFormField label="Peso" hint={SI_HELP.indicator.weightPct}>
            <SiNativeTextControl
              type="number"
              value={form.weight_pct}
              onChange={(value) => patchForm({ weight_pct: Number(value || 0) })}
            />
          </SiAdminFormField>

          <SiAdminFormField label="Escopo" hint={SI_HELP.indicator.scopeType}>
            <SiSelectControl
              value={form.scope_type}
              onChange={(value) =>
                patchForm({ scope_type: value as "consolidated" | "per_unit" })
              }
              options={[
                { value: "consolidated", label: getScopeTypeLabel("consolidated") },
                { value: "per_unit", label: getScopeTypeLabel("per_unit") },
              ]}
            />
          </SiAdminFormField>

          {form.scope_type === "per_unit" ? (
            <SiAdminFormField
              label="Agregação entre filiais"
              hint={SI_HELP.indicator.branchValueAggregation}
            >
              <SiSelectControl
                value={form.branch_value_aggregation}
                onChange={(value) =>
                  patchForm({
                    branch_value_aggregation: value as BranchValueAggregation,
                  })
                }
                options={[
                  { value: "auto", label: getBranchValueAggregationLabel("auto") },
                  { value: "sum", label: getBranchValueAggregationLabel("sum") },
                  { value: "average", label: getBranchValueAggregationLabel("average") },
                  {
                    value: "source_consolidated",
                    label: getBranchValueAggregationLabel("source_consolidated"),
                  },
                ]}
              />
              <p className="si-indicator-form-drawer__aggregation-hints">
                <span title={BRANCH_AGGREGATION_HELP.auto}>Automático</span>
                {" · "}
                <span title={BRANCH_AGGREGATION_HELP.sum}>Soma</span>
                {" · "}
                <span title={BRANCH_AGGREGATION_HELP.average}>Média</span>
                {" · "}
                <span title={BRANCH_AGGREGATION_HELP.source_consolidated}>Fonte</span>
              </p>
            </SiAdminFormField>
          ) : null}

          <SiAdminFormField
            label="Chave da fonte (obrigatória se ativo)"
            hint={SI_HELP.indicator.sourceKey}
          >
            <SiNativeTextControl
              value={form.source_key}
              placeholder="ex.: commercial_rol, production_otd"
              onChange={(value) => patchForm({ source_key: value })}
            />
          </SiAdminFormField>

          <SiAdminFormField
            label="Direção de performance"
            hint={SI_HELP.indicator.performanceDirection}
          >
            <SiSelectControl
              value={form.performance_direction}
              onChange={(value) =>
                patchForm({
                  performance_direction: value as "higher_is_better" | "lower_is_better",
                })
              }
              options={[
                {
                  value: "higher_is_better",
                  label: getPerformanceDirectionLabel("higher_is_better"),
                },
                {
                  value: "lower_is_better",
                  label: getPerformanceDirectionLabel("lower_is_better"),
                },
              ]}
            />
          </SiAdminFormField>

          {mode === "edit" ? (
            <SiAdminFormField label="Ativo" hint={SI_HELP.indicator.isActive}>
              <ActiveToggle
                active={form.is_active}
                disabled={saving}
                helpHint={SI_HELP.indicator.isActive}
                ariaLabel="Indicador ativo"
                onToggle={(is_active) => patchForm({ is_active })}
              />
            </SiAdminFormField>
          ) : null}
        </div>
      ) : (
        <div className="si-admin-form-grid">
          <SectionHintLabel
            label="Formato e avançado"
            hint={SI_HELP.indicator.sectionFormat}
            className="si-admin-form-grid__section-title si-admin-form-grid__section-title--full"
          />

          <SiAdminFormField label="Unidade" hint={SI_HELP.indicator.valueUnit}>
            <SiSelectControl
              value={form.value_unit}
              onChange={(value) => patchForm({ value_unit: value })}
              allowEmpty
              emptyLabel="Não informada"
              options={[...SI_VALUE_UNIT_OPTIONS]}
            />
          </SiAdminFormField>

          <SiAdminFormField label="Casas decimais" hint={SI_HELP.indicator.valueDecimals}>
            <SiNativeTextControl
              type="number"
              min={0}
              max={6}
              value={form.value_decimals}
              onChange={(value) =>
                patchForm({ value_decimals: Number(value || 0) })
              }
            />
          </SiAdminFormField>

          <SiAdminFormField label="Prefixo" hint={SI_HELP.indicator.valuePrefix}>
            <SiNativeTextControl
              placeholder="Ex.: R$"
              value={form.value_prefix}
              onChange={(value) => patchForm({ value_prefix: value })}
            />
          </SiAdminFormField>

          <SiAdminFormField label="Sufixo" hint={SI_HELP.indicator.valueSuffix}>
            <SiNativeTextControl
              placeholder="Ex.: %, PPM, /mês, dias"
              value={form.value_suffix}
              onChange={(value) => patchForm({ value_suffix: value })}
            />
          </SiAdminFormField>

          <SiAdminFormField label="Ordem" hint={SI_HELP.indicator.displayOrder}>
            <SiNativeTextControl
              type="number"
              value={form.display_order}
              onChange={(value) =>
                patchForm({ display_order: Number(value || 0) })
              }
            />
          </SiAdminFormField>

          <SiAdminFormField
            label="Descrição estratégica"
            hint={SI_HELP.indicator.strategicDescription}
            fullWidth
          >
            <SiNativeTextAreaControl
              rows={3}
              value={form.strategic_description}
              aria-label="Descrição estratégica"
              onChange={(strategic_description) =>
                patchForm({ strategic_description })
              }
            />
          </SiAdminFormField>
        </div>
      )}
    </DrawerPanel>
  );
}
