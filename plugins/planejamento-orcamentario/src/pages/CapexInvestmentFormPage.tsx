import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { FilePenLine, Save } from "lucide-react";

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
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import {
  CAPEX_CLASSIFICATION_OPTIONS,
  CAPEX_ORIGIN_OPTIONS,
  CAPEX_PRIORITY_OPTIONS,
  CAPEX_SHIFT_OPTIONS,
  isVersionConflictError,
  missingFieldLabel,
  normalizeMoneyInput,
} from "../utils/capexInvestments";
import { isPlanEditable, planLockReason, planStatusLabel } from "../utils/capexPlans";
import { formatCostCenterLabel } from "../utils/orgCostCenters";
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
};

export function CapexInvestmentFormPage({ mode, investmentId }: CapexInvestmentFormPageProps) {
  const preselectedCc = readQueryParam("cost_center_id");
  const preselectedUnit = readQueryParam("unit_id");

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
        if (reason === "manual" || mode === "create") {
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
  }, [exercise, mode, readOnly, versionConflict]);

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

  const missingLabels = useMemo(
    () => (investment?.missing_fields ?? []).map(missingFieldLabel),
    [investment?.missing_fields],
  );

  const backHref = capexHref({
    costCenterId: form.cost_center_id || preselectedCc || undefined,
  });

  if (bootLoading) {
    return (
      <PageShell title="Investimento CAPEX" subtitle="Carregando…" backHref={backHref}>
        <LoadingActivityCard title="Carregando formulário…" variant="panel" />
      </PageShell>
    );
  }

  if (bootError) {
    return (
      <PageShell title="Investimento CAPEX" backHref={backHref}>
        <StateBox variant="error" dismissible={false}>
          {bootError}
        </StateBox>
      </PageShell>
    );
  }

  if (!exercise) {
    return (
      <PageShell title="Investimento CAPEX" backHref={routeHref("home")}>
        <StateBox variant="warning" dismissible={false}>
          Sem exercício ativo. Não é possível criar investimentos agora.
        </StateBox>
      </PageShell>
    );
  }

  if (!modulesUnlocked) {
    return (
      <PageShell title="Investimento CAPEX" backHref={routeHref("orientacoes")}>
        <StateBox variant="warning" dismissible={false}>
          Confirme a leitura das orientações vigentes para liberar o módulo CAPEX.{" "}
          <a href={routeHref("orientacoes")}>Ir para Orientações</a>
        </StateBox>
      </PageShell>
    );
  }

  if (responsibilities.length === 0) {
    return (
      <PageShell title="Investimento CAPEX" backHref={routeHref("capex")}>
        <StateBox variant="default" dismissible={false}>
          Você não possui centros de custo atribuídos neste exercício.
        </StateBox>
      </PageShell>
    );
  }

  const pageTitle = planLocked
    ? "Investimento (somente leitura)"
    : investment?.status === "archived"
      ? "Investimento arquivado"
      : "Rascunho de investimento";
  const pageSubtitle = planLocked
    ? `Planejamento em status “${planStatusLabel(plan?.status)}”. Edição e anexos bloqueados.`
    : investment?.status === "archived"
      ? "Somente leitura — arquivamento não pode ser editado nesta etapa."
      : "Salve parcialmente a qualquer momento. Envie o planejamento do centro quando estiver completo.";

  return (
    <PageShell
      title={pageTitle}
      subtitle={pageSubtitle}
      icon={<FilePenLine size={28} strokeWidth={1.75} aria-hidden="true" />}
      backHref={backHref}
      actions={
        !readOnly ? (
          <span className={`po-save-status po-save-status--${saveStatus}`} aria-live="polite">
            {saveStatusLabel(saveStatus)}
          </span>
        ) : null
      }
    >
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
          <button type="button" className="po-btn po-btn--secondary" onClick={() => void reloadFromServer()}>
            Recarregar versão atual
          </button>{" "}
          <span className="po-muted">ou permaneça na tela para copiar/revisar os dados locais.</span>
        </StateBox>
      ) : null}

      {investment ? (
        <StateBox variant={investment.is_complete ? "success" : "warning"} dismissible={false}>
          {investment.is_complete
            ? "Rascunho completo para futura submissão (submissão ainda não disponível)."
            : `Rascunho incompleto. Pendências: ${missingLabels.join(", ") || "—"}. O salvamento parcial continua permitido.`}
        </StateBox>
      ) : null}

      <form className="po-form" onSubmit={(e) => void handleManualSave(e)}>
        <SectionCard title="Identificação" hint="Centro de custo apenas entre suas responsabilidades.">
          <label>
            Exercício
            <input
              type="text"
              readOnly
              value={`${exercise.year} — ${exercise.name}`}
            />
          </label>
          <label>
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
          <label>
            Filial
            <input type="text" readOnly value={selectedCc?.unit_id || form.unit_id || "—"} />
          </label>
          <label>
            Área
            <input type="text" readOnly value={selectedCc?.area_id || "—"} />
          </label>
          <label>
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
          <p className="po-muted">
            A categoria classifica o tipo de investimento. Não confundir com conta contábil do ERP
            (não disponível nesta fase).
          </p>
        </SectionCard>

        <SectionCard title="Dados do investimento">
          <label>
            Descrição
            <textarea
              rows={3}
              disabled={readOnly}
              value={form.description}
              onChange={(e) => patchForm({ description: e.target.value })}
            />
          </label>
          <label>
            Justificativa
            <textarea
              rows={3}
              disabled={readOnly}
              value={form.justification}
              onChange={(e) => patchForm({ justification: e.target.value })}
            />
          </label>
          <label>
            Fornecedor provável
            <input
              disabled={readOnly}
              value={form.probable_supplier_name}
              onChange={(e) => patchForm({ probable_supplier_name: e.target.value })}
            />
          </label>
          <label>
            Código do fornecedor
            <input
              disabled={readOnly}
              value={form.probable_supplier_code}
              onChange={(e) => patchForm({ probable_supplier_code: e.target.value })}
            />
          </label>
          <label>
            Valor previsto
            <input
              inputMode="decimal"
              disabled={readOnly}
              value={form.estimated_amount}
              placeholder="0,00"
              onChange={(e) =>
                patchForm({ estimated_amount: normalizeMoneyInput(e.target.value) })
              }
            />
          </label>
          <label>
            Moeda
            <input type="text" readOnly value={form.currency || "BRL"} />
          </label>
          <label>
            Data necessária de recebimento
            <input
              type="date"
              disabled={readOnly}
              value={form.required_date}
              onChange={(e) => patchForm({ required_date: e.target.value })}
            />
          </label>
          <p className="po-field-help">
            Informe a data em que o bem precisa estar faturado, recebido ou disponível para a área.
          </p>
          <label>
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
          <label>
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
          <label>
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
          <label>
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
          <label>
            Observações
            <textarea
              rows={3}
              disabled={readOnly}
              value={form.observations}
              onChange={(e) => patchForm({ observations: e.target.value })}
            />
          </label>
        </SectionCard>

        {!readOnly ? (
          <div className="po-form-actions">
            <button
              type="submit"
              className="po-btn po-btn--primary"
              disabled={saveStatus === "saving" || versionConflict}
            >
              <Save size={16} aria-hidden="true" />
              {saveStatus === "saving" ? "Salvando…" : "Salvar rascunho"}
            </button>
          </div>
        ) : null}
      </form>

      <CapexInvestmentAttachmentsPanel investmentId={persistedId} readOnly={readOnly} />
    </PageShell>
  );
}
