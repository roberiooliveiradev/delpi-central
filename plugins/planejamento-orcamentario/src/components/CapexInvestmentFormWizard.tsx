import type { FormEvent, ReactNode } from "react";
import { useEffect, useState } from "react";
import { Check, ChevronLeft, ChevronRight, FileText } from "lucide-react";

import type { BudgetExercise, BudgetResponsibility, CapexCategory } from "../types/budgetPlanning";
import { CapexCategoryVisual } from "./CapexCategoryVisual";
import { CapexInvestmentAttachmentsPanel } from "./CapexInvestmentAttachmentsPanel";
import { SectionCard, StateBox } from "./uiKit";
import {
  CAPEX_CLASSIFICATION_OPTIONS,
  CAPEX_ORIGIN_OPTIONS,
  CAPEX_PRIORITY_OPTIONS,
  CAPEX_SHIFT_OPTIONS,
  CAPEX_WIZARD_STEPS,
  exerciseMonthOptions,
  isWizardStepComplete,
  monthValueToRequiredDate,
  normalizeMoneyInput,
  requiredDateToMonthValue,
  wizardProgressPercent,
} from "../utils/capexInvestments";
import { formatCostCenterLabel } from "../utils/orgCostCenters";

export type CapexInvestmentWizardForm = {
  unit_id: string;
  cost_center_id: string;
  category_id: string;
  description: string;
  justification: string;
  probable_supplier_name: string;
  estimated_amount: string;
  required_date: string;
  priority: string;
  origin: string;
  classification: string;
  shift: string;
  observations: string;
};

type CapexInvestmentFormWizardProps = {
  form: CapexInvestmentWizardForm;
  patchForm: (patch: Partial<CapexInvestmentWizardForm>) => void;
  exercise: BudgetExercise;
  categories: CapexCategory[];
  responsibilities: BudgetResponsibility[];
  selectedCc: BudgetResponsibility | undefined;
  lockCostCenter: boolean;
  readOnly: boolean;
  persistedId: string | null;
  wizardStep: number;
  wizardMax: number;
  stepError: string | null;
  saveStatus: "idle" | "dirty" | "saving" | "saved" | "error";
  versionConflict: boolean;
  saveStatusLabel: string;
  alerts?: ReactNode;
  onJump: (index: number) => void;
  onBack: () => void;
  onNext: () => void;
  onClose?: () => void;
  onManualSave: (event: FormEvent) => void;
};

export function CapexInvestmentFormWizard({
  form,
  patchForm,
  exercise,
  categories,
  responsibilities,
  selectedCc,
  lockCostCenter,
  readOnly,
  persistedId,
  wizardStep,
  wizardMax,
  stepError,
  saveStatus,
  versionConflict,
  saveStatusLabel,
  alerts,
  onJump,
  onBack,
  onNext,
  onClose,
  onManualSave: _onManualSave,
}: CapexInvestmentFormWizardProps) {
  const step = CAPEX_WIZARD_STEPS[wizardStep] ?? CAPEX_WIZARD_STEPS[0];
  const isLast = wizardStep >= CAPEX_WIZARD_STEPS.length - 1;
  const progress = wizardProgressPercent(wizardStep);
  const selectedCategory = categories.find((c) => c.id === form.category_id) ?? null;
  const [wantAttachments, setWantAttachments] = useState<boolean | null>(null);

  useEffect(() => {
    if (step.id !== "attachments") {
      setWantAttachments(null);
    }
  }, [step.id]);

  return (
    <div className="po-inv-wizard">
      <nav className="po-wizard" aria-label="Progresso do cadastro">
        <div className="po-wizard__head">
          <p className="po-wizard__eyebrow">
            Etapa {wizardStep + 1} de {CAPEX_WIZARD_STEPS.length}
            {!readOnly && saveStatus !== "idle" ? (
              <>
                {" "}
                · <span className={`po-save-status po-save-status--${saveStatus}`}>{saveStatusLabel}</span>
              </>
            ) : null}
          </p>
          <strong className="po-wizard__current">{step.title}</strong>
        </div>
        <ol className="po-wizard__steps">
          {CAPEX_WIZARD_STEPS.map((item, index) => {
            const done = index < wizardStep || isWizardStepComplete(index, form, { lockCostCenter });
            const current = index === wizardStep;
            const reachable = index <= wizardMax;
            return (
              <li
                key={item.id}
                className={[
                  "po-wizard__step",
                  current ? "is-current" : "",
                  done && !current ? "is-done" : "",
                  !reachable ? "is-locked" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                <button
                  type="button"
                  disabled={!reachable}
                  aria-current={current ? "step" : undefined}
                  onClick={() => onJump(index)}
                >
                  <span className="po-wizard__bullet" aria-hidden="true">
                    {done && !current ? <Check size={14} /> : index + 1}
                  </span>
                  <span className="po-wizard__label">{item.label}</span>
                </button>
              </li>
            );
          })}
        </ol>
        <div
          className="po-wizard__track"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
          aria-label="Avanço do cadastro"
        >
          <span style={{ width: `${progress}%` }} />
        </div>
      </nav>

      {alerts}

      {stepError ? (
        <StateBox variant="warning" dismissible={false}>
          {stepError}
        </StateBox>
      ) : null}

      <form
        className="po-inv-form__body po-inv-wizard__body"
        onSubmit={(e) => {
          e.preventDefault();
        }}
      >
        <SectionCard title={step.title} hint={step.hint}>
          {step.id === "category" ? (
            <div className="po-inv-form__grid po-inv-form__grid--2">
              {!lockCostCenter ? (
                <label className="po-inv-form__field po-inv-form__field--span2">
                  Centro de custo
                  <select
                    required
                    disabled={readOnly || Boolean(persistedId)}
                    value={
                      form.cost_center_id && form.unit_id
                        ? `${form.unit_id}|${form.cost_center_id}`
                        : form.cost_center_id
                          ? `${selectedCc?.unit_id || ""}|${form.cost_center_id}`
                          : ""
                    }
                    onChange={(e) => {
                      const raw = e.target.value;
                      const sep = raw.indexOf("|");
                      if (sep < 0) {
                        patchForm({ cost_center_id: raw, unit_id: "" });
                        return;
                      }
                      patchForm({
                        unit_id: raw.slice(0, sep),
                        cost_center_id: raw.slice(sep + 1),
                      });
                    }}
                  >
                    <option value="">Selecione…</option>
                    {responsibilities.map((r) => (
                      <option key={r.id} value={`${r.unit_id}|${r.cost_center_id}`}>
                        {formatCostCenterLabel({
                          branch: r.branch ?? r.unit_id,
                          code: r.cost_center_id,
                        })}
                        {r.area_id ? ` · ${r.area_id}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              <label className="po-inv-form__field po-inv-form__field--span2">
                Categoria de investimento
                <select
                  disabled={readOnly}
                  value={form.category_id}
                  onChange={(e) => patchForm({ category_id: e.target.value })}
                >
                  <option value="">Selecione…</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </label>

              {categories.length > 0 ? (
                <div
                  className="po-inv-form__cat-tiles po-inv-form__field--span2"
                  role="list"
                  aria-label="Atalhos de categoria"
                >
                  {categories.map((c) => {
                    const active = form.category_id === c.id;
                    return (
                      <button
                        key={c.id}
                        type="button"
                        role="listitem"
                        disabled={readOnly}
                        className={`po-inv-form__cat-tile${active ? " is-active" : ""}`}
                        onClick={() => patchForm({ category_id: c.id })}
                      >
                        <CapexCategoryVisual
                          categoryId={c.id}
                          iconKey={c.icon_key}
                          hasCustomIcon={Boolean(c.has_custom_icon)}
                          size={22}
                        />
                        <span>{c.name}</span>
                      </button>
                    );
                  })}
                </div>
              ) : null}

              {selectedCategory ? (
                <p className="po-muted po-inv-form__hint po-inv-form__field--span2">
                  Categoria selecionada: <strong>{selectedCategory.name}</strong>.
                </p>
              ) : null}

              <div className="po-sr-only">
                <label>
                  Exercício
                  <input type="text" readOnly value={`${exercise.year} — ${exercise.name}`} />
                </label>
                <label>
                  Filial
                  <input type="text" readOnly value={selectedCc?.unit_id || form.unit_id || "—"} />
                </label>
                <label>
                  Área
                  <input type="text" readOnly value={selectedCc?.area_id || "—"} />
                </label>
              </div>
            </div>
          ) : null}

          {step.id === "need" ? (
            <div className="po-inv-form__grid">
              <label className="po-inv-form__field po-inv-form__field--span2">
                Descrição
                <textarea
                  rows={3}
                  disabled={readOnly}
                  placeholder="Ex.: Notebooks para a equipe de RH"
                  value={form.description}
                  onChange={(e) => patchForm({ description: e.target.value })}
                />
              </label>
              <label className="po-inv-form__field po-inv-form__field--span2">
                Justificativa
                <textarea
                  rows={3}
                  disabled={readOnly}
                  placeholder="Por que este investimento é necessário neste ciclo?"
                  value={form.justification}
                  onChange={(e) => patchForm({ justification: e.target.value })}
                />
              </label>
            </div>
          ) : null}

          {step.id === "timing" ? (
            <>
              <div className="po-inv-form__grid po-inv-form__grid--2">
                <div className="po-inv-form__field">
                  <label htmlFor="po-inv-estimated-amount">Valor previsto</label>
                  <div className="po-inv-form__money">
                    <span aria-hidden="true">R$</span>
                    <input
                      id="po-inv-estimated-amount"
                      inputMode="decimal"
                      disabled={readOnly}
                      value={form.estimated_amount}
                      placeholder="0,00"
                      onChange={(e) =>
                        patchForm({ estimated_amount: normalizeMoneyInput(e.target.value) })
                      }
                    />
                  </div>
                </div>
                <label className="po-inv-form__field">
                  Mês necessário de recebimento
                  <select
                    disabled={readOnly}
                    value={requiredDateToMonthValue(form.required_date)}
                    onChange={(e) =>
                      patchForm({
                        required_date: monthValueToRequiredDate(e.target.value),
                      })
                    }
                  >
                    <option value="">Selecione…</option>
                    {exerciseMonthOptions(exercise.year).map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="po-inv-form__field">
                  Prioridade
                  <select
                    disabled={readOnly}
                    value={form.priority}
                    onChange={(e) => patchForm({ priority: e.target.value })}
                  >
                    <option value="">Selecione…</option>
                    {CAPEX_PRIORITY_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="po-inv-form__field">
                  Origem
                  <select
                    disabled={readOnly}
                    value={form.origin}
                    onChange={(e) => patchForm({ origin: e.target.value })}
                  >
                    <option value="">Selecione…</option>
                    {CAPEX_ORIGIN_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <p className="po-field-help">
                Escolha o mês do ciclo em que o bem precisa estar disponível para a área.
              </p>
            </>
          ) : null}

          {step.id === "details" ? (
            <div className="po-inv-form__grid po-inv-form__grid--2">
              <label className="po-inv-form__field po-inv-form__field--span2">
                Fornecedor provável
                <input
                  disabled={readOnly}
                  value={form.probable_supplier_name}
                  onChange={(e) => patchForm({ probable_supplier_name: e.target.value })}
                />
              </label>
              <label className="po-inv-form__field">
                Classificação
                <select
                  disabled={readOnly}
                  value={form.classification}
                  onChange={(e) => patchForm({ classification: e.target.value })}
                >
                  <option value="">Opcional…</option>
                  {CAPEX_CLASSIFICATION_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="po-inv-form__field">
                Turno
                <select
                  disabled={readOnly}
                  value={form.shift}
                  onChange={(e) => patchForm({ shift: e.target.value })}
                >
                  <option value="">Opcional…</option>
                  {CAPEX_SHIFT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="po-inv-form__field po-inv-form__field--span2">
                Observações
                <textarea
                  rows={3}
                  disabled={readOnly}
                  value={form.observations}
                  onChange={(e) => patchForm({ observations: e.target.value })}
                />
              </label>
            </div>
          ) : null}

          {step.id === "attachments" ? (
            <div className="po-inv-wizard__attachments">
              {wantAttachments === null ? (
                <div className="po-attach-choice" role="group" aria-label="Deseja anexar documentos?">
                  <p className="po-attach-choice__question">
                    Deseja anexar algum arquivo para auxiliar o responsável pela aprovação?
                  </p>
                  <p className="po-attach-choice__hint">
                    Não é obrigatório. Orçamentos, propostas ou imagens ajudam na análise.
                  </p>
                  <div className="po-attach-choice__actions">
                    <button
                      type="button"
                      className="po-btn po-btn--secondary po-attach-choice__btn"
                      onClick={() => void onNext()}
                    >
                      Não, concluir sem anexos
                    </button>
                    <button
                      type="button"
                      className="po-btn po-btn--primary po-attach-choice__btn"
                      onClick={() => setWantAttachments(true)}
                    >
                      <FileText size={16} aria-hidden="true" />
                      Sim, quero anexar
                    </button>
                  </div>
                </div>
              ) : (
                <CapexInvestmentAttachmentsPanel
                  investmentId={persistedId}
                  readOnly={readOnly}
                  embedded
                />
              )}
            </div>
          ) : null}

          <div className="po-inv-form__footer po-inv-wizard__footer">
            <p className="po-muted">
              {isLast && wantAttachments === null
                ? "Escolha se deseja incluir documentos de apoio."
                : isLast
                  ? "Ao concluir, o rascunho fica salvo no centro de custo."
                  : "O rascunho é salvo automaticamente enquanto você preenche."}
            </p>
            <div className="po-inv-form__footer-actions">
              {onClose ? (
                <button type="button" className="po-btn po-btn--secondary" onClick={onClose}>
                  Fechar
                </button>
              ) : null}
              {wizardStep > 0 ? (
                <button
                  type="button"
                  className="po-btn po-btn--secondary"
                  onClick={() => {
                    if (step.id === "attachments" && wantAttachments === true) {
                      setWantAttachments(null);
                      return;
                    }
                    onBack();
                  }}
                >
                  <ChevronLeft size={16} aria-hidden="true" />
                  Voltar
                </button>
              ) : null}
              {!(isLast && wantAttachments === null) ? (
                <button
                  type="button"
                  className="po-btn po-btn--primary"
                  disabled={saveStatus === "saving" || versionConflict}
                  onClick={() => void onNext()}
                >
                  {isLast ? (
                    readOnly ? (
                      "Fechar"
                    ) : (
                      <>
                        <Check size={16} aria-hidden="true" />
                        Concluir
                      </>
                    )
                  ) : (
                    <>
                      Continuar
                      <ChevronRight size={16} aria-hidden="true" />
                    </>
                  )}
                </button>
              ) : null}
            </div>
          </div>
        </SectionCard>
      </form>
    </div>
  );
}
