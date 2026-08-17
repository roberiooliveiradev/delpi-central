import {
  type FormEvent,
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  CheckCircle2,
  CircleAlert,
  MapPin,
  Save,
} from "lucide-react";

import { HttpRequestError } from "../api/httpClient";
import {
  createCapexInvestment,
  fetchBudgetContext,
  fetchMyCapexResponsibilities,
  getCapexInvestment,
  listActiveCapexCategories,
  resolveCapexPlan,
  updateCapexInvestment,
} from "../api/budgetPlanningApi";
import type {
  BudgetExercise,
  BudgetResponsibility,
  CapexCategory,
  CapexInvestment,
  CapexPlan,
} from "../types/budgetPlanning";
import { CapexInvestmentAttachmentsPanel } from "../components/CapexInvestmentAttachmentsPanel";
import { CapexCategoryVisual } from "../components/CapexCategoryVisual";
import { CapexInvestmentFormWizard } from "../components/CapexInvestmentFormWizard";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import {
  CAPEX_CLASSIFICATION_OPTIONS,
  CAPEX_ORIGIN_OPTIONS,
  CAPEX_PRIORITY_OPTIONS,
  CAPEX_SHIFT_OPTIONS,
  CAPEX_WIZARD_STEPS,
  exerciseMonthOptions,
  isVersionConflictError,
  isWizardStepComplete,
  missingFieldLabel,
  monthValueToRequiredDate,
  normalizeMoneyInput,
  requiredDateToMonthValue,
  wizardProgressPercent,
  wizardStepBlockingMessage,
} from "../utils/capexInvestments";
import { isPlanEditable, planLockReason, planStatusLabel } from "../utils/capexPlans";
import { formatCostCenterLabel, branchCityLabel } from "../utils/orgCostCenters";
import {
  capexHref,
  capexInvestmentHref,
  readQueryParam,
  routeHref,
} from "../utils/routing";

const AUTOSAVE_MS = 1000;

type FormState = {
  unit_id: string;
  cost_center_id: string;
  category_id: string;
  description: string;
  justification: string;
  probable_supplier_name: string;
  probable_supplier_code: string;
  estimated_amount: string;
  currency: string;
  required_date: string;
  priority: string;
  origin: string;
  classification: string;
  shift: string;
  observations: string;
};

type SaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

const emptyForm = (): FormState => ({
  unit_id: "",
  cost_center_id: "",
  category_id: "",
  description: "",
  justification: "",
  probable_supplier_name: "",
  probable_supplier_code: "",
  estimated_amount: "",
  currency: "BRL",
  required_date: "",
  priority: "",
  origin: "",
  classification: "",
  shift: "",
  observations: "",
});

function investmentToForm(row: CapexInvestment): FormState {
  return {
    unit_id: row.unit_id || "",
    cost_center_id: row.cost_center_id || "",
    category_id: row.category_id || "",
    description: row.description || "",
    justification: row.justification || "",
    probable_supplier_name: row.probable_supplier_name || "",
    probable_supplier_code: row.probable_supplier_code || "",
    estimated_amount: row.estimated_amount || "",
    currency: row.currency || "BRL",
    required_date: row.required_date?.slice(0, 10) || "",
    priority: row.priority || "",
    origin: row.origin || "",
    classification: row.classification || "",
    shift: row.shift || "",
    observations: row.observations || "",
  };
}

function buildPayload(form: FormState) {
  return {
    unit_id: form.unit_id || null,
    cost_center_id: form.cost_center_id,
    category_id: form.category_id || null,
    description: form.description.trim() || null,
    justification: form.justification.trim() || null,
    probable_supplier_name: form.probable_supplier_name.trim() || null,
    probable_supplier_code: form.probable_supplier_code.trim() || null,
    estimated_amount: form.estimated_amount ? normalizeMoneyInput(form.estimated_amount) || null : null,
    currency: form.currency || "BRL",
    required_date: form.required_date || null,
    priority: form.priority || null,
    origin: form.origin || null,
    classification: form.classification || null,
    shift: form.shift || null,
    observations: form.observations.trim() || null,
  };
}

function saveStatusLabel(status: SaveStatus): string {
  switch (status) {
    case "dirty":
      return "Alterações pendentes";
    case "saving":
      return "Salvando";
    case "saved":
      return "Salvo";
    case "error":
      return "Erro ao salvar";
    default:
      return "";
  }
}

type CapexInvestmentFormPageProps = {
  mode: "create" | "edit";
  investmentId?: string | null;
  /** Centro pré-selecionado (cockpit). Sobrescreve query string. */
  costCenterId?: string | null;
  unitId?: string | null;
  /** `page` = rota dedicada; `panel` = conteúdo do modal (sem PageShell). */
  presentation?: "page" | "panel";
  onClose?: () => void;
  onSaved?: (investment: CapexInvestment) => void;
};

export function CapexInvestmentFormPage({
  mode,
  investmentId,
  costCenterId: costCenterIdProp,
  unitId: unitIdProp,
  presentation = "page",
  onClose,
  onSaved,
}: CapexInvestmentFormPageProps) {
  const preselectedCc = (costCenterIdProp ?? readQueryParam("cost_center_id")).trim();
  const preselectedUnit = (unitIdProp ?? readQueryParam("unit_id")).trim();
  const lockCostCenter = Boolean(costCenterIdProp?.trim());
  const isPanel = presentation === "panel";

  const [exercise, setExercise] = useState<BudgetExercise | null>(null);
  const [modulesUnlocked, setModulesUnlocked] = useState(true);
  const [responsibilities, setResponsibilities] = useState<BudgetResponsibility[]>([]);
  const [categories, setCategories] = useState<CapexCategory[]>([]);
  const [investment, setInvestment] = useState<CapexInvestment | null>(null);
  const [form, setForm] = useState<FormState>(() => ({
    ...emptyForm(),
    unit_id: preselectedUnit,
    cost_center_id: preselectedCc,
  }));
  const [version, setVersion] = useState(1);
  const [bootLoading, setBootLoading] = useState(true);
  const [bootError, setBootError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [versionConflict, setVersionConflict] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [plan, setPlan] = useState<CapexPlan | null>(null);

  const [persistedId, setPersistedId] = useState<string | null>(investmentId ?? null);
  const [wizardStep, setWizardStep] = useState(0);
  const [wizardMax, setWizardMax] = useState(0);
  const [stepError, setStepError] = useState<string | null>(null);
  const dirtyRef = useRef(false);
  const savingRef = useRef(false);
  const formRef = useRef(form);
  const versionRef = useRef(version);
  const investmentIdRef = useRef<string | null>(investmentId ?? null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    formRef.current = form;
  }, [form]);

  useEffect(() => {
    versionRef.current = version;
  }, [version]);

  useEffect(() => {
    investmentIdRef.current = persistedId;
  }, [persistedId]);

  const planLocked = !isPlanEditable(plan);
  const readOnly = investment?.status === "archived" || planLocked;
  const selectedCc = responsibilities.find((r) => {
    if (r.cost_center_id !== form.cost_center_id) return false;
    if (form.unit_id) return r.unit_id === form.unit_id;
    return true;
  });
  const lockBanner = planLockReason(plan);

  const persist = useCallback(async (reason: "manual" | "auto") => {
    if (savingRef.current || readOnly || versionConflict) return;
    if (!exercise?.id) {
      setSaveError("Exercício ativo não encontrado.");
      setSaveStatus("error");
      return;
    }
    if (!formRef.current.cost_center_id) {
      setSaveError("Selecione um centro de custo autorizado.");
      setSaveStatus("error");
      return;
    }

    savingRef.current = true;
    setSaveStatus("saving");
    setSaveError(null);
    try {
      const payload = buildPayload(formRef.current);
      let saved: CapexInvestment;
      if (!investmentIdRef.current) {
        saved = await createCapexInvestment({
          exercise_id: exercise.id,
          ...payload,
        });
        investmentIdRef.current = saved.id;
        setPersistedId(saved.id);
        if (!isPanel && (reason === "manual" || mode === "create")) {
          window.history.replaceState({}, "", capexInvestmentHref(saved.id));
        }
      } else {
        saved = await updateCapexInvestment(investmentIdRef.current, {
          version: versionRef.current,
          ...payload,
        });
      }
      setInvestment(saved);
      setVersion(saved.version);
      versionRef.current = saved.version;
      setForm(investmentToForm(saved));
      dirtyRef.current = false;
      setSaveStatus("saved");
      setSuccessMsg(reason === "manual" ? "Rascunho salvo." : null);
      onSaved?.(saved);
    } catch (err: unknown) {
      if (isVersionConflictError(err)) {
        setVersionConflict(true);
        setSaveStatus("error");
        setSaveError(
          "Este investimento foi alterado em outra sessão. Recarregue a versão atual ou revise seus dados locais antes de continuar.",
        );
      } else {
        setSaveStatus("error");
        setSaveError(err instanceof Error ? err.message : "Falha ao salvar o rascunho.");
      }
    } finally {
      savingRef.current = false;
    }
  }, [exercise, isPanel, mode, onSaved, readOnly, versionConflict]);

  const scheduleAutosave = useCallback(() => {
    if (readOnly || versionConflict) return;
    dirtyRef.current = true;
    setSaveStatus("dirty");
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void persist("auto");
    }, AUTOSAVE_MS);
  }, [persist, readOnly, versionConflict]);

  function patchForm(patch: Partial<FormState>) {
    if (readOnly) return;
    setForm((prev) => ({ ...prev, ...patch }));
    scheduleAutosave();
  }

  useEffect(() => {
    const controller = new AbortController();
    setBootLoading(true);
    setBootError(null);

    (async () => {
      try {
        const ctx = await fetchBudgetContext(controller.signal);
        setExercise(ctx.exercise);
        setModulesUnlocked(Boolean(ctx.modules_unlocked));
        if (!ctx.exercise) return;
        if (!ctx.modules_unlocked) return;

        const [mine, cats] = await Promise.all([
          fetchMyCapexResponsibilities(ctx.exercise.id, controller.signal),
          listActiveCapexCategories(controller.signal),
        ]);
        if (controller.signal.aborted) return;
        setResponsibilities(mine.items ?? []);
        setCategories(cats.items ?? []);

        let costCenterForPlan = preselectedCc;
        let unitForPlan = preselectedUnit;
        if (mode === "edit" && investmentId) {
          const row = await getCapexInvestment(investmentId, controller.signal);
          if (controller.signal.aborted) return;
          setInvestment(row);
          setForm(investmentToForm(row));
          setVersion(row.version);
          setPersistedId(row.id);
          investmentIdRef.current = row.id;
          costCenterForPlan = row.cost_center_id;
          unitForPlan = row.unit_id;
        } else if (preselectedCc) {
          setForm((f) => ({
            ...f,
            cost_center_id: preselectedCc,
            unit_id: preselectedUnit || f.unit_id,
          }));
        }

        if (costCenterForPlan) {
          try {
            const resolved = await resolveCapexPlan(
              {
                exercise_id: ctx.exercise.id,
                cost_center_id: costCenterForPlan,
                unit_id: unitForPlan || undefined,
              },
              controller.signal,
            );
            if (!controller.signal.aborted) setPlan(resolved);
          } catch {
            if (!controller.signal.aborted) setPlan(null);
          }
        }
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setBootError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setBootError("Acesso negado (403) a este investimento CAPEX.");
        } else if (err instanceof HttpRequestError && err.status === 404) {
          setBootError("Investimento não encontrado ou sem permissão de visualização.");
        } else {
          setBootError(err instanceof Error ? err.message : "Erro ao carregar o formulário.");
        }
      } finally {
        if (!controller.signal.aborted) setBootLoading(false);
      }
    })();

    return () => {
      controller.abort();
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [investmentId, mode, preselectedCc, preselectedUnit]);

  useEffect(() => {
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      if (dirtyRef.current) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, []);

  async function reloadFromServer() {
    if (!investmentIdRef.current) return;
    setBootLoading(true);
    setVersionConflict(false);
    setSaveError(null);
    try {
      const row = await getCapexInvestment(investmentIdRef.current);
      setInvestment(row);
      setForm(investmentToForm(row));
      setVersion(row.version);
      dirtyRef.current = false;
      setSaveStatus("saved");
      setSuccessMsg("Versão atual recarregada do servidor.");
    } catch (err: unknown) {
      setBootError(err instanceof Error ? err.message : "Falha ao recarregar.");
    } finally {
      setBootLoading(false);
    }
  }

  async function handleManualSave(event: FormEvent) {
    event.preventDefault();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    await persist("manual");
  }

  async function handleWizardNext() {
    const msg = wizardStepBlockingMessage(wizardStep, form, { lockCostCenter });
    if (msg) {
      setStepError(msg);
      return;
    }
    setStepError(null);
    const last = wizardStep >= CAPEX_WIZARD_STEPS.length - 1;
    if (last) {
      if (!readOnly) {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        await persist("manual");
      }
      onClose?.();
      return;
    }
    const next = wizardStep + 1;
    if (CAPEX_WIZARD_STEPS[next]?.id === "attachments" && !investmentIdRef.current) {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      await persist("manual");
    }
    setWizardStep(next);
    setWizardMax((m) => Math.max(m, next));
  }

  function handleWizardBack() {
    setStepError(null);
    setWizardStep((s) => Math.max(0, s - 1));
  }

  function handleWizardJump(index: number) {
    if (index < 0 || index > wizardMax) return;
    setStepError(null);
    setWizardStep(index);
  }

  const missingLabels = useMemo(
    () => (investment?.missing_fields ?? []).map(missingFieldLabel),
    [investment?.missing_fields],
  );

  const backHref = capexHref({
    costCenterId: form.cost_center_id || preselectedCc || undefined,
    unitId: form.unit_id || preselectedUnit || undefined,
  });

  const wrapShell = (title: string, subtitle: string | undefined, content: ReactNode) => {
    if (isPanel) {
      return <div className="po-inv-form po-inv-form--panel">{content}</div>;
    }
    return (
      <PageShell title={title} subtitle={subtitle} backHref={backHref}>
        <div className="po-inv-form">{content}</div>
      </PageShell>
    );
  };

  if (bootLoading) {
    return wrapShell("Investimento CAPEX", "Carregando…", (
      <LoadingActivityCard title="Carregando formulário…" variant="panel" />
    ));
  }

  if (bootError) {
    return wrapShell("Investimento CAPEX", undefined, (
      <StateBox variant="error" dismissible={false}>
        {bootError}
      </StateBox>
    ));
  }

  if (!exercise) {
    return wrapShell("Investimento CAPEX", undefined, (
      <StateBox variant="warning" dismissible={false}>
        Sem exercício ativo. Não é possível criar investimentos agora.
      </StateBox>
    ));
  }

  if (!modulesUnlocked) {
    return wrapShell("Investimento CAPEX", undefined, (
      <StateBox variant="warning" dismissible={false}>
        Confirme a leitura das orientações vigentes para liberar o módulo CAPEX.{" "}
        <a href={routeHref("orientacoes")}>Ir para Orientações</a>
      </StateBox>
    ));
  }

  if (responsibilities.length === 0) {
    return wrapShell("Investimento CAPEX", undefined, (
      <StateBox variant="default" dismissible={false}>
        Você não possui centros de custo atribuídos neste exercício.
      </StateBox>
    ));
  }

  const pageTitle = planLocked
    ? "Investimento (somente leitura)"
    : investment?.status === "archived"
      ? "Investimento arquivado"
      : "Rascunho de investimento";
  const heroTitle =
    mode === "create"
      ? "Novo investimento"
      : investment?.status === "archived"
        ? "Visualizar investimento"
        : planLocked
          ? "Somente leitura"
          : "Editar investimento";
  const pageSubtitle = planLocked
    ? `Planejamento em status “${planStatusLabel(plan?.status)}”. Edição e anexos bloqueados.`
    : investment?.status === "archived"
      ? "Somente leitura — arquivamento não pode ser editado nesta etapa."
      : "Salve parcialmente a qualquer momento. Envie o planejamento do centro quando estiver completo.";

  const selectedCategory = categories.find((c) => c.id === form.category_id) ?? null;
  const locationLabel = selectedCc
    ? branchCityLabel(selectedCc.branch ?? selectedCc.unit_id)
    : "—";
  const completenessPct = investment
    ? investment.is_complete
      ? 100
      : Math.max(
          12,
          Math.round(
            (1 -
              (investment.missing_fields?.length ?? 0) /
                Math.max(1, (investment.missing_fields?.length ?? 0) + 4)) *
              100,
          ),
        )
    : form.description.trim() || form.estimated_amount || form.category_id
      ? 28
      : 8;

  if (isPanel) {
    const panelAlerts = (
      <>
        {lockBanner ? (
          <StateBox variant="warning" dismissible={false}>
            {lockBanner}
          </StateBox>
        ) : null}
        {mode === "create" && planLocked ? (
          <StateBox variant="error" dismissible={false}>
            Não é possível criar novos investimentos enquanto o planejamento estiver{" "}
            {planStatusLabel(plan?.status)}.{" "}
            {onClose ? (
              <button type="button" className="po-btn po-btn--secondary" onClick={onClose}>
                Fechar
              </button>
            ) : null}
          </StateBox>
        ) : null}
        {successMsg ? (
          <StateBox variant="success" dismissible={false}>
            {successMsg}
          </StateBox>
        ) : null}
        {saveError ? (
          <StateBox variant="error" dismissible={false}>
            {saveError}
          </StateBox>
        ) : null}
        {versionConflict ? (
          <StateBox variant="warning" dismissible={false}>
            Conflito de versão detectado.{" "}
            <button
              type="button"
              className="po-btn po-btn--secondary"
              onClick={() => void reloadFromServer()}
            >
              Recarregar versão atual
            </button>
          </StateBox>
        ) : null}
      </>
    );

    return wrapShell(
      pageTitle,
      undefined,
      <CapexInvestmentFormWizard
        form={form}
        patchForm={patchForm}
        exercise={exercise}
        categories={categories}
        responsibilities={responsibilities}
        selectedCc={selectedCc}
        lockCostCenter={lockCostCenter}
        readOnly={readOnly}
        persistedId={persistedId}
        wizardStep={wizardStep}
        wizardMax={wizardMax}
        stepError={stepError}
        saveStatus={saveStatus}
        versionConflict={versionConflict}
        saveStatusLabel={saveStatusLabel(saveStatus)}
        alerts={panelAlerts}
        onJump={handleWizardJump}
        onBack={handleWizardBack}
        onNext={() => {
          void handleWizardNext();
        }}
        onClose={onClose}
        onManualSave={(e) => void handleManualSave(e)}
      />,
    );
  }

  return wrapShell(pageTitle, undefined, (
      <>
        <header className="po-centros__hero">
          <div className="po-centros__hero-copy">
            <p className="po-centros__eyebrow">
              Elaboração · {exercise.year}
              {!readOnly && saveStatus !== "idle" ? (
                <>
                  {" "}
                  ·{" "}
                  <span className={`po-save-status po-save-status--${saveStatus}`}>
                    {saveStatusLabel(saveStatus)}
                  </span>
                </>
              ) : null}
            </p>
            <h2 className="po-centros__title">{heroTitle}</h2>
            <p className="po-centros__lead">{pageSubtitle}</p>
          </div>
          <aside className="po-centros__hero-panel" aria-label="Resumo do rascunho">
            <dl className="po-centros__meta">
              <div>
                <dt>Ciclo</dt>
                <dd>{exercise.year}</dd>
              </div>
              <div>
                <dt>Local</dt>
                <dd className="po-cockpit__meta-local">
                  <MapPin size={13} aria-hidden="true" />
                  {locationLabel}
                </dd>
              </div>
            </dl>
            {investment ? (
              <div
                className={`po-inv-form__progress${
                  investment.is_complete ? " is-complete" : " is-pending"
                }`}
              >
                <div className="po-inv-form__progress-head">
                  {investment.is_complete ? (
                    <CheckCircle2 size={16} aria-hidden="true" />
                  ) : (
                    <CircleAlert size={16} aria-hidden="true" />
                  )}
                  <span>{investment.is_complete ? "Pronto para o plano" : "Campos pendentes"}</span>
                </div>
                <div
                  className="po-inv-form__progress-track"
                  role="progressbar"
                  aria-valuenow={completenessPct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <span style={{ width: `${completenessPct}%` }} />
                </div>
              </div>
            ) : null}
          </aside>
        </header>

        {lockBanner ? (
          <StateBox variant="warning" dismissible={false}>
            {lockBanner}
          </StateBox>
        ) : null}

        {mode === "create" && planLocked ? (
          <StateBox variant="error" dismissible={false}>
            Não é possível criar novos investimentos enquanto o planejamento estiver{" "}
            {planStatusLabel(plan?.status)}.{" "}
            <a href={backHref}>Voltar ao centro de custo</a>
          </StateBox>
        ) : null}

        {successMsg ? (
          <StateBox variant="success" dismissible={false}>
            {successMsg}
          </StateBox>
        ) : null}

        {saveError ? (
          <StateBox variant="error" dismissible={false}>
            {saveError}
          </StateBox>
        ) : null}

        {versionConflict ? (
          <StateBox variant="warning" dismissible={false}>
            Conflito de versão detectado.{" "}
            <button
              type="button"
              className="po-btn po-btn--secondary"
              onClick={() => void reloadFromServer()}
            >
              Recarregar versão atual
            </button>{" "}
            <span className="po-muted">
              ou permaneça na tela para copiar/revisar os dados locais.
            </span>
          </StateBox>
        ) : null}

        {investment ? (
          <StateBox variant={investment.is_complete ? "success" : "warning"} dismissible={false}>
            {investment.is_complete
              ? "Rascunho completo para futura submissão (submissão ainda não disponível)."
              : `Rascunho incompleto. Pendências: ${missingLabels.join(", ") || "—"}. O salvamento parcial continua permitido.`}
          </StateBox>
        ) : null}

        <form className="po-inv-form__body" onSubmit={(e) => void handleManualSave(e)}>
          <SectionCard
            title="Identificação"
            hint="Escolha o centro (entre os seus) e a categoria do investimento."
          >
            <div className="po-inv-form__grid po-inv-form__grid--2">
              {lockCostCenter ? (
                <div className="po-inv-form__chips po-inv-form__field--span2" aria-label="Contexto">
                  <span className="po-inv-form__chip">
                    {formatCostCenterLabel({
                      branch: selectedCc?.branch ?? selectedCc?.unit_id ?? form.unit_id,
                      code: form.cost_center_id,
                    })}
                  </span>
                  <span className="po-inv-form__chip">
                    Exercício {exercise.year} — {exercise.name}
                  </span>
                  <span className="po-inv-form__chip">
                    Filial {selectedCc?.unit_id || form.unit_id || "—"}
                  </span>
                  <span className="po-inv-form__chip">
                    Área {selectedCc?.area_id || "—"}
                  </span>
                </div>
              ) : (
                <>
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

              {(selectedCc || form.unit_id) && (
                <div className="po-inv-form__chips po-inv-form__field--span2" aria-label="Contexto">
                  <span className="po-inv-form__chip">
                    Exercício {exercise.year} — {exercise.name}
                  </span>
                  <span className="po-inv-form__chip">
                    Filial {selectedCc?.unit_id || form.unit_id || "—"}
                  </span>
                  <span className="po-inv-form__chip">
                    Área {selectedCc?.area_id || "—"}
                  </span>
                </div>
              )}
                </>
              )}

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
            </div>

            {categories.length > 0 ? (
              <div className="po-inv-form__cat-tiles" role="list" aria-label="Atalhos de categoria">
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
              <p className="po-muted po-inv-form__hint">
                Categoria selecionada: <strong>{selectedCategory.name}</strong>. Classifica o tipo
                de investimento — não confundir com conta contábil do ERP.
              </p>
            ) : (
              <p className="po-muted po-inv-form__hint">
                A categoria classifica o tipo de investimento. Não confundir com conta contábil do
                ERP (não disponível nesta fase).
              </p>
            )}

            {/* Campos ocultos para leitores/teste que ainda referenciam Filial/Área/Exercício como inputs */}
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
              {lockCostCenter ? (
                <label>
                  Centro de custo
                  <input
                    type="text"
                    readOnly
                    value={formatCostCenterLabel({
                      branch: selectedCc?.branch ?? selectedCc?.unit_id ?? form.unit_id,
                      code: form.cost_center_id,
                    })}
                  />
                </label>
              ) : null}
            </div>
          </SectionCard>

          <SectionCard title="Dados do investimento">
            <div className="po-inv-form__group">
              <h3 className="po-inv-form__group-title">O que você precisa</h3>
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
            </div>

            <div className="po-inv-form__group">
              <h3 className="po-inv-form__group-title">Quanto e quando</h3>
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
            </div>

            <div className="po-inv-form__group">
              <h3 className="po-inv-form__group-title">Fornecedor e detalhes</h3>
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
            </div>

            {!readOnly ? (
              <div className="po-inv-form__footer">
                <p className="po-muted">
                  O autosave grava enquanto você digita. Use o botão para forçar o salvamento.
                </p>
                <div className="po-inv-form__footer-actions">
                  <button
                    type="submit"
                    className="po-btn po-btn--primary"
                    disabled={saveStatus === "saving" || versionConflict}
                  >
                    <Save size={16} aria-hidden="true" />
                    {saveStatus === "saving" ? "Salvando…" : "Salvar rascunho"}
                  </button>
                </div>
              </div>
            ) : null}
          </SectionCard>
        </form>

        <CapexInvestmentAttachmentsPanel investmentId={persistedId} readOnly={readOnly} />
      </>
  ));
}
