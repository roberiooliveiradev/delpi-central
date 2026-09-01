import { FieldLabel, SectionHintLabel } from "@delpi/plugin-ui/index";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import type {
  CreateStrategicIndicatorGoalRequest,
  GoalMode,
  GoalPeriodicity,
  GoalScopeBranch,
  MonthlyTargetItem,
  StrategicIndicatorGoalItem,
  UpdateStrategicIndicatorGoalRequest,
} from "../../data/types/indicatorGoals";
import { SI_HELP } from "../../content/helpTooltips";
import {
  getGoalModeLabel,
  getGoalPeriodicityLabel,
  getGoalScopeBranchLabel,
} from "../presentation/labels";
import { clampGoalYear, MIN_GOAL_YEAR, MAX_GOAL_YEAR } from "../utils/goalYearHelpers";
import {
  buildEmptyCurveTargets,
  getCurveHintText,
  getCurvePointLabels,
  getCurveSectionTitle,
  normalizeCurveTargets,
} from "../utils/curveTargets";
import {
  validateIndicatorGoalForm,
  validateIndicatorGoalFormTargetStep,
  validateIndicatorGoalFormValueStep,
  type IndicatorGoalCatalogEntry,
} from "../utils/goalFormValidation";
import {
  expectedMonthlyCurvePointCount,
  resolveGoalValueForApi,
} from "../utils/goalValuePolicy";
import { GoalScopeBadges } from "./GoalScopeBadges";
import "./IndicatorGoalForm.css";
import { SiSelectControl } from "./siFiltersUi";
import { SiNativeTextAreaControl, SiNativeTextControl } from "./siNativeFormFields";

type IndicatorOption = {
  value: string;
  label: string;
};

export type IndicatorGoalFormLayout = "flat" | "wizard" | "compact";

export type IndicatorGoalFormPanelShell = {
  title: string;
  cycleYear?: number;
  onBack?: () => void;
  versionLabel?: string;
};

type IndicatorGoalFormProps = {
  saving: boolean;
  initialValue?: StrategicIndicatorGoalItem | null;
  duplicateFrom?: StrategicIndicatorGoalItem | null;
  indicatorOptions?: Array<string | IndicatorOption>;
  indicatorCatalog?: IndicatorGoalCatalogEntry[];
  defaultGoalYear?: number;
  lockGoalYear?: boolean;
  /** flat = legado (modais); wizard = criar/duplicar no detail; compact = editar no detail. */
  layout?: IndicatorGoalFormLayout;
  panelShell?: IndicatorGoalFormPanelShell;
  onCreate?: (payload: CreateStrategicIndicatorGoalRequest) => Promise<void>;
  onUpdate?: (
    goalId: string,
    payload: UpdateStrategicIndicatorGoalRequest,
  ) => Promise<void>;
  onCancel?: () => void;
};

type WizardStep = 1 | 2 | 3;

function normalizeIndicatorOptions(
  options: Array<string | IndicatorOption>,
): IndicatorOption[] {
  return options.map((option) =>
    typeof option === "string" ? { value: option, label: option } : option,
  );
}

export function IndicatorGoalForm({
  saving,
  initialValue,
  duplicateFrom = null,
  indicatorOptions = [],
  indicatorCatalog = [],
  defaultGoalYear,
  lockGoalYear = false,
  layout = "flat",
  panelShell,
  onCreate,
  onUpdate,
  onCancel,
}: IndicatorGoalFormProps) {
  const [indicatorId, setIndicatorId] = useState("");
  const [goalYear, setGoalYear] = useState<number>(new Date().getFullYear());
  const [goalLabel, setGoalLabel] = useState("");
  const [goalValue, setGoalValue] = useState<number>(0);
  const [goalPeriodicity, setGoalPeriodicity] =
    useState<GoalPeriodicity>("monthly");
  const [goalMode, setGoalMode] = useState<GoalMode>("standard");
  const [goalScopeBranch, setGoalScopeBranch] = useState<GoalScopeBranch | string>("");
  const [monthlyTargets, setMonthlyTargets] = useState<MonthlyTargetItem[]>(
    buildEmptyCurveTargets("monthly"),
  );
  const [validFrom, setValidFrom] = useState("");
  const [validTo, setValidTo] = useState("");
  const [notes, setNotes] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [wizardStep, setWizardStep] = useState<WizardStep>(1);
  const [validityOpen, setValidityOpen] = useState(false);

  const formSeed = duplicateFrom ?? initialValue;
  const isEditing = useMemo(
    () => !!initialValue && !duplicateFrom,
    [initialValue, duplicateFrom],
  );
  const normalizedIndicatorOptions = useMemo(
    () => normalizeIndicatorOptions(indicatorOptions),
    [indicatorOptions],
  );
  const curvePointLabels = useMemo(
    () => getCurvePointLabels(goalPeriodicity),
    [goalPeriodicity],
  );
  const effectiveLayout: IndicatorGoalFormLayout = isEditing ? "compact" : layout;

  useEffect(() => {
    if (!formSeed) {
      setIndicatorId("");
      setGoalYear(clampGoalYear(defaultGoalYear ?? new Date().getFullYear()));
      setGoalLabel("");
      setGoalValue(0);
      setGoalPeriodicity("monthly");
      setGoalMode("standard");
      setGoalScopeBranch("");
      setMonthlyTargets(buildEmptyCurveTargets("monthly"));
      setValidFrom("");
      setValidTo("");
      setNotes("");
      setLocalError(null);
      setWizardStep(1);
      setValidityOpen(false);
      return;
    }

    setIndicatorId(formSeed.indicator_id);
    setGoalYear(formSeed.goal_year);
    setGoalLabel(formSeed.goal_label);
    setGoalValue(formSeed.goal_value);
    setGoalPeriodicity(formSeed.goal_periodicity);
    setGoalMode(formSeed.goal_mode);
    setGoalScopeBranch(formSeed.goal_scope_branch ?? "");
    setMonthlyTargets(
      normalizeCurveTargets(formSeed.monthly_targets, formSeed.goal_periodicity),
    );
    setValidFrom(formSeed.valid_from ?? "");
    setValidTo(formSeed.valid_to ?? "");
    setNotes(formSeed.notes ?? "");
    setLocalError(null);
    setWizardStep(1);
    setValidityOpen(Boolean(formSeed.valid_from || formSeed.valid_to || formSeed.notes));
  }, [formSeed, defaultGoalYear]);

  function updateMonthlyTarget(monthNumber: number, targetValue: number) {
    setMonthlyTargets((current) =>
      current.map((item) =>
        item.month_number === monthNumber
          ? { ...item, target_value: targetValue }
          : item,
      ),
    );
  }

  function validationInput() {
    return {
      indicatorId,
      goalYear,
      goalLabel,
      goalScopeBranch,
      goalMode,
      goalPeriodicity,
      goalValue,
      monthlyTargets,
      indicatorOptions: normalizedIndicatorOptions,
      indicatorCatalog,
      isEditing,
    };
  }

  async function handleSubmit() {
    setLocalError(null);

    const validationError = validateIndicatorGoalForm(validationInput());
    if (validationError) {
      setLocalError(validationError);
      return;
    }

    if (validFrom && validTo && validFrom > validTo) {
      setLocalError("A data final não pode ser anterior à data inicial.");
      return;
    }

    const resolvedGoalValue = resolveGoalValueForApi(goalMode, goalValue);
    const resolvedMonthlyTargets = goalMode === "monthly_curve" ? monthlyTargets : [];

    if (isEditing && initialValue && onUpdate) {
      const payload: UpdateStrategicIndicatorGoalRequest = {
        goal_label: goalLabel.trim(),
        goal_value: resolvedGoalValue,
        goal_periodicity: goalPeriodicity,
        goal_mode: goalMode,
        monthly_targets: resolvedMonthlyTargets,
        valid_from: validFrom || null,
        valid_to: validTo || null,
        notes: notes || null,
      };

      if (indicatorId.trim() !== initialValue.indicator_id) {
        payload.indicator_id = indicatorId.trim();
      }
      if (Number(goalYear) !== Number(initialValue.goal_year)) {
        payload.goal_year = Number(goalYear);
      }
      const initialScope = initialValue.goal_scope_branch ?? "";
      if (goalScopeBranch !== initialScope) {
        payload.goal_scope_branch = goalScopeBranch;
      }

      await onUpdate(initialValue.id, payload);
      return;
    }

    if (onCreate) {
      await onCreate({
        indicator_id: indicatorId.trim(),
        goal_year: Number(goalYear),
        goal_scope_branch: goalScopeBranch,
        goal_label: goalLabel.trim(),
        goal_value: resolvedGoalValue,
        goal_periodicity: goalPeriodicity,
        goal_mode: goalMode,
        monthly_targets: resolvedMonthlyTargets,
        valid_from: validFrom || null,
        valid_to: validTo || null,
        notes: notes || null,
      });
    }
  }

  function handleWizardContinue() {
    setLocalError(null);
    if (wizardStep === 1) {
      const error = validateIndicatorGoalFormTargetStep(validationInput());
      if (error) {
        setLocalError(error);
        return;
      }
      setWizardStep(2);
      return;
    }
    if (wizardStep === 2) {
      const error = validateIndicatorGoalFormValueStep(validationInput());
      if (error) {
        setLocalError(error);
        return;
      }
      setWizardStep(3);
    }
  }

  function renderIndicatorField(disabled = false) {
    if (normalizedIndicatorOptions.length > 0) {
      return (
        <SiSelectControl
          value={indicatorId}
          disabled={disabled}
          onChange={(nextId) => {
            setIndicatorId(nextId);
            if (!isEditing && !goalLabel.trim()) {
              const match = normalizedIndicatorOptions.find(
                (option) => option.value === nextId,
              );
              if (match) {
                const [name] = match.label.split(" · ");
                setGoalLabel(name?.trim() ?? match.label);
              }
            }
          }}
          allowEmpty
          emptyLabel="Selecione"
          options={normalizedIndicatorOptions}
        />
      );
    }

    return (
      <SiNativeTextControl
        value={indicatorId}
        disabled={disabled}
        onChange={setIndicatorId}
      />
    );
  }

  function renderTargetFields(options?: { showScopeInTarget?: boolean }) {
    const showScope = options?.showScopeInTarget ?? effectiveLayout !== "wizard";

    return (
      <>
        <Field label="Indicador" hint={SI_HELP.goalForm.indicatorId}>
          {renderIndicatorField(isEditing && effectiveLayout === "compact")}
        </Field>

        <Field label="Ano da meta" hint={SI_HELP.goalForm.goalYear}>
          <SiNativeTextControl
            type="number"
            min={MIN_GOAL_YEAR}
            max={MAX_GOAL_YEAR}
            value={goalYear}
            readOnly={lockGoalYear}
            onChange={(value) => setGoalYear(clampGoalYear(Number(value)))}
          />
        </Field>

        {showScope ? (
          <Field label="Escopo da meta" hint={SI_HELP.goalForm.goalScopeBranch}>
            <SiSelectControl
              value={goalScopeBranch}
              onChange={setGoalScopeBranch}
              allowEmpty
              emptyLabel={getGoalScopeBranchLabel("")}
              options={[
                { value: "01", label: getGoalScopeBranchLabel("01") },
                { value: "02", label: getGoalScopeBranchLabel("02") },
              ]}
            />
          </Field>
        ) : null}

        <Field label="Nome da meta" hint={SI_HELP.goalForm.goalLabel} fullWidth>
          <SiNativeTextControl value={goalLabel} onChange={setGoalLabel} />
        </Field>
      </>
    );
  }

  function renderValueFields() {
    return (
      <>
        <Field label="Modo da meta" hint={SI_HELP.goalForm.goalMode}>
          <SiSelectControl
            value={goalMode}
            onChange={(nextMode) => {
              const resolvedMode = nextMode as GoalMode;
              setGoalMode(resolvedMode);
              if (resolvedMode === "monthly_curve") {
                setMonthlyTargets(buildEmptyCurveTargets(goalPeriodicity));
              }
            }}
            options={[
              { value: "standard", label: getGoalModeLabel("standard") },
              { value: "monthly_curve", label: getGoalModeLabel("monthly_curve") },
            ]}
          />
        </Field>

        {effectiveLayout === "wizard" ? (
          <Field label="Escopo da meta" hint={SI_HELP.goalForm.goalScopeBranch}>
            <SiSelectControl
              value={goalScopeBranch}
              onChange={setGoalScopeBranch}
              allowEmpty
              emptyLabel={getGoalScopeBranchLabel("")}
              options={[
                { value: "01", label: getGoalScopeBranchLabel("01") },
                { value: "02", label: getGoalScopeBranchLabel("02") },
              ]}
            />
          </Field>
        ) : null}

        <Field label="Periodicidade" hint={SI_HELP.goalForm.goalPeriodicity}>
          <SiSelectControl
            value={goalPeriodicity}
            onChange={(nextPeriodicity) => {
              const resolvedPeriodicity = nextPeriodicity as GoalPeriodicity;
              setGoalPeriodicity(resolvedPeriodicity);
              if (goalMode === "monthly_curve") {
                setMonthlyTargets((current) =>
                  normalizeCurveTargets(current, resolvedPeriodicity),
                );
              }
            }}
            options={[
              { value: "monthly", label: "Mensal" },
              { value: "annual", label: "Anual" },
              { value: "quarterly", label: "Trimestral" },
              { value: "weekly", label: "Semanal" },
            ]}
          />
        </Field>

        {goalMode === "standard" ? (
          <Field label="Valor da meta" hint={SI_HELP.goalForm.goalValue}>
            <SiNativeTextControl
              type="number"
              step="0.0001"
              value={goalValue}
              onChange={(value) => setGoalValue(Number(value))}
            />
          </Field>
        ) : null}

        {renderCurveGrid()}
      </>
    );
  }

  function renderValidityFields() {
    return (
      <>
        <Field label="Vigência inicial" hint={SI_HELP.goalForm.validFrom}>
          <SiNativeTextControl type="date" value={validFrom} onChange={setValidFrom} />
        </Field>

        <Field label="Vigência final" hint={SI_HELP.goalForm.validTo}>
          <SiNativeTextControl type="date" value={validTo} onChange={setValidTo} />
        </Field>

        <Field label="Observações" hint={SI_HELP.goalForm.notes} fullWidth>
          <SiNativeTextAreaControl
            value={notes}
            aria-label="Observações"
            onChange={setNotes}
          />
        </Field>
      </>
    );
  }

  function renderCurveGrid() {
    if (goalMode !== "monthly_curve") return null;

    return (
      <div className="si-settings-form-field si-settings-form-field--full">
        <FieldLabel
          label={getCurveSectionTitle(goalPeriodicity)}
          hint={SI_HELP.goalForm.monthlyTargets}
          className="si-settings-form-field__label"
        />

        <div className="si-monthly-targets-toolbar">
          <span className="si-monthly-targets-toolbar__badge">
            {getGoalModeLabel(goalMode)}
          </span>
          <span className="si-monthly-targets-toolbar__summary">
            {expectedMonthlyCurvePointCount(goalPeriodicity)} pontos ·{" "}
            {getGoalPeriodicityLabel(goalPeriodicity)}
          </span>
        </div>
        <p className="si-monthly-targets-hint">{getCurveHintText(goalPeriodicity)}</p>

        <div
          className={`si-monthly-targets-grid ${
            goalPeriodicity === "weekly" ? "si-monthly-targets-grid--weekly" : ""
          }`}
        >
          {monthlyTargets.map((item, index) => (
            <label key={item.month_number} className="si-monthly-targets-grid__item">
              <span>{curvePointLabels[index] ?? `#${item.month_number}`}</span>
              <SiNativeTextControl
                type="number"
                step="0.0001"
                value={item.target_value}
                onChange={(value) =>
                  updateMonthlyTarget(item.month_number, Number(value || 0))
                }
              />
            </label>
          ))}
        </div>
      </div>
    );
  }

  function renderWizardStepper() {
    const steps: Array<{ id: WizardStep; label: string }> = [
      { id: 1, label: "Destino" },
      { id: 2, label: "Valor" },
      { id: 3, label: "Vigência" },
    ];

    return (
      <div className="si-goal-form-panel__stepper" role="tablist" aria-label="Passos do formulário">
        {steps.map((step) => (
          <button
            key={step.id}
            type="button"
            role="tab"
            aria-selected={wizardStep === step.id}
            className={`si-goal-form-panel__step ${
              wizardStep === step.id ? "is-active" : wizardStep > step.id ? "is-done" : ""
            }`}
            onClick={() => {
              if (step.id < wizardStep) {
                setLocalError(null);
                setWizardStep(step.id);
              }
            }}
          >
            {step.id}. {step.label}
          </button>
        ))}
      </div>
    );
  }

  function renderFormCard(
    title: string,
    hint: string,
    stepBadge: string | null,
    children: ReactNode,
  ) {
    return (
      <section className="si-goal-form-card">
        <header className="si-goal-form-card__header">
          <SectionHintLabel label={title} hint={hint} />
          {stepBadge ? (
            <span className="si-goal-form-card__step-badge">{stepBadge}</span>
          ) : null}
        </header>
        <div className="si-goal-form-card__body si-admin-form-grid">{children}</div>
      </section>
    );
  }

  function renderBody() {
    if (effectiveLayout === "flat") {
      return (
        <div className="si-modal-form__grid">
          <SectionHintLabel
            label="Destino"
            hint={SI_HELP.goalForm.sectionTarget}
            className="si-modal-form__section-title si-modal-form__section-title--full"
          />
          {renderTargetFields()}
          <SectionHintLabel
            label="Valor e periodicidade"
            hint={SI_HELP.goalForm.sectionValue}
            className="si-modal-form__section-title si-modal-form__section-title--full"
          />
          {renderValueFields()}
          <SectionHintLabel
            label="Vigência"
            hint={SI_HELP.goalForm.sectionValidity}
            className="si-modal-form__section-title si-modal-form__section-title--full"
          />
          {renderValidityFields()}
        </div>
      );
    }

    if (effectiveLayout === "wizard") {
      return (
        <div className="si-goal-form-panel__body">
          {renderWizardStepper()}
          {wizardStep === 1
            ? renderFormCard(
                "Destino",
                SI_HELP.goalForm.sectionTarget,
                "passo 1/3",
                renderTargetFields({ showScopeInTarget: false }),
              )
            : null}
          {wizardStep === 2
            ? renderFormCard(
                "Valor e periodicidade",
                SI_HELP.goalForm.sectionValue,
                "passo 2/3",
                renderValueFields(),
              )
            : null}
          {wizardStep === 3
            ? renderFormCard(
                "Vigência e observações",
                SI_HELP.goalForm.sectionValidity,
                "passo 3/3",
                renderValidityFields(),
              )
            : null}
        </div>
      );
    }

    return (
      <div className="si-goal-form-panel__body si-goal-form-panel__body--compact">
        <div className="si-goal-form-panel__compact-grid">
          {renderFormCard(
            "Destino",
            SI_HELP.goalForm.sectionTarget,
            null,
            renderTargetFields(),
          )}
          {renderFormCard(
            "Valor e periodicidade",
            SI_HELP.goalForm.sectionValue,
            panelShell?.versionLabel ?? null,
            renderValueFields(),
          )}
        </div>
        <details
          className="si-goal-form-panel__validity"
          open={validityOpen}
          onToggle={(event) => setValidityOpen(event.currentTarget.open)}
        >
          <summary>
            <SectionHintLabel
              label="Vigência e observações"
              hint={SI_HELP.goalForm.sectionValidity}
            />
          </summary>
          <div className="si-admin-form-grid si-goal-form-panel__validity-grid">
            {renderValidityFields()}
          </div>
        </details>
      </div>
    );
  }

  function renderFooter() {
    if (effectiveLayout === "wizard") {
      return (
        <div className="si-goal-form-panel__footer">
          {onCancel ? (
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={onCancel}
              disabled={saving}
            >
              Cancelar
            </button>
          ) : null}
          {wizardStep > 1 ? (
            <button
              type="button"
              className="si-settings-editor__button si-settings-editor__button--secondary"
              onClick={() => {
                setLocalError(null);
                setWizardStep((current) => (current > 1 ? ((current - 1) as WizardStep) : current));
              }}
              disabled={saving}
            >
              ← Voltar
            </button>
          ) : null}
          {wizardStep < 3 ? (
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={handleWizardContinue}
              disabled={saving}
            >
              Continuar →
            </button>
          ) : (
            <button
              type="button"
              className="si-settings-editor__button"
              onClick={() => void handleSubmit()}
              disabled={saving}
            >
              {saving
                ? "Salvando..."
                : duplicateFrom
                  ? "Salvar cópia"
                  : "Criar meta"}
            </button>
          )}
        </div>
      );
    }

    return (
      <div
        className={
          panelShell ? "si-goal-form-panel__footer" : "si-modal-form__actions"
        }
      >
        {onCancel ? (
          <button
            type="button"
            className="si-settings-editor__button si-settings-editor__button--secondary"
            onClick={onCancel}
            disabled={saving}
          >
            {panelShell ? "Descartar" : "Cancelar"}
          </button>
        ) : null}

        <button
          type="button"
          className="si-settings-editor__button"
          onClick={() => void handleSubmit()}
          disabled={saving}
        >
          {saving
            ? "Salvando..."
            : isEditing
              ? "Salvar alterações"
              : duplicateFrom
                ? "Salvar cópia"
                : "Criar meta"}
        </button>
      </div>
    );
  }

  const formContent = (
    <>
      {localError ? (
        <div className="si-settings-editor__alert si-settings-editor__alert--error">
          {localError}
        </div>
      ) : null}
      {renderBody()}
      {renderFooter()}
    </>
  );

  if (!panelShell) {
    return <div className="si-modal-form">{formContent}</div>;
  }

  return (
    <div className="si-goal-form-panel">
      <header className="si-goal-form-panel__header">
        <div className="si-goal-form-panel__header-main">
          {panelShell.onBack ? (
            <button
              type="button"
              className="si-goal-form-panel__back"
              onClick={panelShell.onBack}
            >
              ← Voltar à lista
            </button>
          ) : null}
          <div className="si-goal-form-panel__title-row">
            <h3 className="si-goal-form-panel__title">{panelShell.title}</h3>
            {typeof panelShell.cycleYear === "number" ? (
              <span className="si-goal-form-panel__cycle">Ciclo {panelShell.cycleYear}</span>
            ) : null}
            <GoalScopeBadges selectedScope={goalScopeBranch} />
          </div>
        </div>
      </header>
      {formContent}
    </div>
  );
}

function Field({
  label,
  hint,
  children,
  fullWidth = false,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
  fullWidth?: boolean;
}) {
  return (
    <label
      className={`si-settings-form-field ${fullWidth ? "si-settings-form-field--full" : ""}`}
    >
      <FieldLabel label={label} hint={hint} className="si-settings-form-field__label" />
      {children}
    </label>
  );
}
