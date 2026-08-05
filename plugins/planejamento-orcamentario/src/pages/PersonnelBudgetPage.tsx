import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Archive, Plus, RefreshCw, Users } from "lucide-react";

import {
  archivePersonnelPlanLine,
  createPersonnelPlanLine,
  fetchBudgetContext,
  fetchMyPersonnelResponsibilities,
  getPersonnelPlan,
  listErpCostCenters,
  listPersonnelPlans,
  resolvePersonnelPlan,
  updatePersonnelPlanLine,
} from "../api/budgetPlanningApi";
import type {
  BudgetExercise,
  BudgetResponsibility,
  ErpCostCenter,
  PersonnelPlan,
  PersonnelPlanLine,
} from "../types/budgetPlanning";
import { PageShell } from "../components/PageShell";
import { PersonnelPlanWorkflowPanel } from "../components/PersonnelPlanWorkflowPanel";
import { LoadingActivityCard, SectionCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import {
  costCenterKey,
  formatCostCenterLabel,
} from "../utils/orgCostCenters";
import {
  buildPersonnelLineCreatePayload,
  buildPersonnelLineUpdatePayload,
  findDuplicatePositionName,
  HEADCOUNT_COLUMNS,
  isPersonnelPlanEditable,
  isPersonnelPlanLockedError,
  isPersonnelVersionConflictError,
  lineFromServer,
  mapPersonnelError,
  PERSONNEL_AUTOSAVE_MS,
  personnelPlanLockReason,
  personnelSaveStatusLabel,
  POSITION_NAME_MAX_LENGTH,
  type PersonnelSaveStatus,
  validatePositionName,
} from "../utils/personnelPlans";
import {
  hasPersonnelApproveAccess,
  hasPersonnelEditAccess,
  hasPersonnelSubmitAccess,
  hasPersonnelViewAccess,
} from "../utils/permissions";
import {
  pessoalApprovalsHref,
  pessoalHref,
  readQueryParam,
  routeHref,
} from "../utils/routing";

type DraftRow = {
  localKey: string;
  id: string | null;
  position_name: string;
  headcount_dec_2025: string;
  headcount_oct_2026: string;
  headcount_forecast: string;
  headcount_dec_2027: string;
  observations: string;
  version: number;
  saveStatus: PersonnelSaveStatus;
  saveError: string | null;
  versionConflict: boolean;
  serverLine: PersonnelPlanLine | null;
};

function newLocalKey(): string {
  return `local-${Math.random().toString(36).slice(2, 10)}`;
}

function emptyDraftRow(): DraftRow {
  return {
    localKey: newLocalKey(),
    id: null,
    position_name: "",
    headcount_dec_2025: "",
    headcount_oct_2026: "",
    headcount_forecast: "",
    headcount_dec_2027: "",
    observations: "",
    version: 1,
    saveStatus: "idle",
    saveError: null,
    versionConflict: false,
    serverLine: null,
  };
}

function draftFromLine(line: PersonnelPlanLine): DraftRow {
  const mapped = lineFromServer(line);
  return {
    ...mapped,
    localKey: line.id,
    id: line.id,
    saveStatus: "idle",
    saveError: null,
    versionConflict: false,
    serverLine: line,
  };
}

function exerciseTitle(exercise: BudgetExercise | null | undefined): string {
  if (!exercise) return "Exercício vigente";
  return `${exercise.year} — ${exercise.name}`;
}

export function PersonnelBudgetPage() {
  const selectedCc = readQueryParam("cost_center_id");
  const selectedUnit = readQueryParam("unit_id");
  const { profile } = usePermissions();
  const canView = hasPersonnelViewAccess(profile);
  const canEditPerm = hasPersonnelEditAccess(profile);
  const canSubmit = hasPersonnelSubmitAccess(profile);
  const canApprove = hasPersonnelApproveAccess(profile);

  const [exercise, setExercise] = useState<BudgetExercise | null>(null);
  const [modulesUnlocked, setModulesUnlocked] = useState(false);
  const [responsibilities, setResponsibilities] = useState<BudgetResponsibility[]>([]);
  const [erpByBranch, setErpByBranch] = useState<Record<string, ErpCostCenter[]>>({});
  const [plan, setPlan] = useState<PersonnelPlan | null>(null);
  const [rows, setRows] = useState<DraftRow[]>([]);
  const planEditable = isPersonnelPlanEditable(plan);
  const canEdit = canEditPerm && planEditable;

  const [bootLoading, setBootLoading] = useState(true);
  const [planLoading, setPlanLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [planError, setPlanError] = useState<string | null>(null);
  const [planEmptyHint, setPlanEmptyHint] = useState<string | null>(null);

  const rowsRef = useRef(rows);
  const planIdRef = useRef<string | null>(null);
  const savingKeysRef = useRef(new Set<string>());
  const debounceRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    rowsRef.current = rows;
  }, [rows]);

  useEffect(() => {
    planIdRef.current = plan?.id ?? null;
  }, [plan]);

  const selectedResponsibility = useMemo(() => {
    if (!selectedCc) return null;
    return (
      responsibilities.find((r) => {
        if (r.cost_center_id !== selectedCc) return false;
        if (selectedUnit) return (r.unit_id || r.branch) === selectedUnit;
        return true;
      }) ?? null
    );
  }, [responsibilities, selectedCc, selectedUnit]);

  const labelForResponsibility = useCallback(
    (row: BudgetResponsibility) => {
      const branch = row.branch || row.unit_id;
      const erp = (erpByBranch[branch] ?? []).find(
        (cc) => cc.code === row.cost_center_id && cc.branch === branch,
      );
      return formatCostCenterLabel({
        branch,
        code: row.cost_center_id,
        description: erp?.description,
      });
    },
    [erpByBranch],
  );

  useEffect(() => {
    const controller = new AbortController();
    if (!canView) {
      queueMicrotask(() => {
        if (!controller.signal.aborted) {
          setBootLoading(false);
          setError("Sem permissão para consultar o Orçamento de Pessoal.");
        }
      });
      return () => controller.abort();
    }

    setBootLoading(true);
    setError(null);

    fetchBudgetContext(controller.signal)
      .then(async (ctx) => {
        setExercise(ctx.exercise);
        setModulesUnlocked(Boolean(ctx.modules_unlocked));
        if (!ctx.exercise || !ctx.modules_unlocked) {
          setResponsibilities([]);
          return;
        }
        const mine = await fetchMyPersonnelResponsibilities(
          ctx.exercise.id,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        const items = mine.items ?? [];
        setResponsibilities(items);

        const branches = [
          ...new Set(
            items
              .map((r) => String(r.branch || r.unit_id || "").trim())
              .filter((b) => b === "01" || b === "02"),
          ),
        ];
        const erpEntries = await Promise.all(
          branches.map(async (branch) => {
            try {
              const result = await listErpCostCenters(branch, controller.signal);
              return [branch, result.items ?? []] as const;
            } catch {
              return [branch, []] as const;
            }
          }),
        );
        if (!controller.signal.aborted) {
          setErpByBranch(Object.fromEntries(erpEntries));
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(mapPersonnelError(err));
        setResponsibilities([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBootLoading(false);
      });

    return () => controller.abort();
  }, [canView]);

  const applyPlan = useCallback((next: PersonnelPlan | null) => {
    setPlan(next);
    setRows((next?.lines ?? []).filter((ln) => ln.is_active !== false).map(draftFromLine));
  }, []);

  const refreshPlanTotals = useCallback(async (planId: string) => {
    try {
      const fresh = await getPersonnelPlan(planId);
      setPlan(fresh);
    } catch {
      /* totais: best-effort; linhas já estão atualizadas */
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadPlan() {
      setPlan(null);
      setRows([]);
      setPlanError(null);
      setPlanEmptyHint(null);

      if (!selectedCc || !selectedResponsibility || !exercise?.id || !modulesUnlocked) {
        return;
      }

      const unitId =
        selectedUnit ||
        selectedResponsibility.unit_id ||
        selectedResponsibility.branch ||
        "";
      if (!unitId) {
        setPlanError("Filial obrigatória para abrir o planejamento de Pessoal.");
        return;
      }

      setPlanLoading(true);
      try {
        if (canEditPerm) {
          const resolved = await resolvePersonnelPlan(
            {
              exercise_id: exercise.id,
              unit_id: unitId,
              cost_center_id: selectedCc,
            },
            controller.signal,
          );
          if (!controller.signal.aborted) applyPlan(resolved);
        } else {
          const listed = await listPersonnelPlans(
            {
              exercise_id: exercise.id,
              unit_id: unitId,
              cost_center_id: selectedCc,
              page: 1,
              page_size: 5,
            },
            controller.signal,
          );
          if (controller.signal.aborted) return;
          const first = listed.items?.[0] ?? null;
          if (!first) {
            setPlanEmptyHint(
              "Ainda não há planejamento de Pessoal para este centro. Um editor com permissão de edição precisa iniciar o rascunho.",
            );
            applyPlan(null);
          } else {
            const full = await getPersonnelPlan(first.id, controller.signal);
            if (!controller.signal.aborted) applyPlan(full);
          }
        }
      } catch (err: unknown) {
        if (controller.signal.aborted) return;
        setPlanError(mapPersonnelError(err));
        applyPlan(null);
      } finally {
        if (!controller.signal.aborted) setPlanLoading(false);
      }
    }

    void loadPlan();
    return () => controller.abort();
  }, [
    applyPlan,
    canEditPerm,
    exercise?.id,
    modulesUnlocked,
    selectedCc,
    selectedResponsibility,
    selectedUnit,
  ]);

  const hasPendingLineWork = useMemo(
    () => rows.some((r) => r.saveStatus === "dirty" || r.saveStatus === "saving"),
    [rows],
  );

  const handleWorkflowPlanChange = useCallback(
    (next: PersonnelPlan | null) => {
      if (!next) return;
      setPlan(next);
      // Não sobrescrever drafts sujos com o payload do workflow.
      setRows((prev) => {
        const dirty = prev.some(
          (r) => r.saveStatus === "dirty" || r.saveStatus === "saving",
        );
        if (dirty) return prev;
        return (next.lines ?? [])
          .filter((ln) => ln.is_active !== false)
          .map(draftFromLine);
      });
    },
    [],
  );

  const focusLine = useCallback((lineId: string) => {
    const el = document.querySelector(
      `[data-personnel-line-id="${CSS.escape(lineId)}"]`,
    );
    if (el instanceof HTMLElement) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      const input = el.querySelector("input, textarea");
      if (input instanceof HTMLElement) input.focus();
    }
  }, []);

  const updateRow = useCallback((localKey: string, patch: Partial<DraftRow>) => {
    setRows((prev) =>
      prev.map((row) => (row.localKey === localKey ? { ...row, ...patch } : row)),
    );
  }, []);

  const persistRow = useCallback(
    async (localKey: string) => {
      if (!canEdit || savingKeysRef.current.has(localKey)) return;
      const row = rowsRef.current.find((r) => r.localKey === localKey);
      const planId = planIdRef.current;
      if (!row || !planId || row.versionConflict) return;

      const nameCheck = validatePositionName(row.position_name);
      if (!nameCheck.ok) {
        if (!row.id) {
          updateRow(localKey, {
            saveStatus: row.position_name.trim() ? "error" : "idle",
            saveError: row.position_name.trim() ? nameCheck.message : null,
          });
        } else {
          updateRow(localKey, {
            saveStatus: "error",
            saveError: nameCheck.message,
          });
        }
        return;
      }

      if (
        findDuplicatePositionName(
          rowsRef.current.map((r) => ({
            localKey: r.localKey,
            position_name: r.position_name,
          })),
          nameCheck.name,
          localKey,
        )
      ) {
        updateRow(localKey, {
          saveStatus: "error",
          saveError:
            "[budget_personnel_line_duplicate_position] Já existe linha ativa para este cargo neste plano.",
        });
        return;
      }

      savingKeysRef.current.add(localKey);
      updateRow(localKey, { saveStatus: "saving", saveError: null });
      try {
        let saved: PersonnelPlanLine;
        if (!row.id) {
          const created = buildPersonnelLineCreatePayload(row);
          if (!created.ok) {
            updateRow(localKey, {
              saveStatus: "error",
              saveError: created.code
                ? `[${created.code}] ${created.message}`
                : created.message,
            });
            return;
          }
          saved = await createPersonnelPlanLine(planId, created.payload);
        } else {
          const updated = buildPersonnelLineUpdatePayload(row.version, row);
          if (!updated.ok) {
            updateRow(localKey, {
              saveStatus: "error",
              saveError: updated.code
                ? `[${updated.code}] ${updated.message}`
                : updated.message,
            });
            return;
          }
          saved = await updatePersonnelPlanLine(row.id, updated.payload);
        }
        const mapped = lineFromServer(saved);
        updateRow(localKey, {
          ...mapped,
          id: saved.id,
          localKey,
          saveStatus: "saved",
          saveError: null,
          versionConflict: false,
          serverLine: saved,
        });
        await refreshPlanTotals(planId);
      } catch (err: unknown) {
        if (isPersonnelVersionConflictError(err)) {
          updateRow(localKey, {
            saveStatus: "error",
            versionConflict: true,
            saveError:
              "[budget_personnel_line_version_conflict] Esta linha foi alterada em outra sessão. Recarregue a versão do servidor ou revise os valores locais.",
          });
        } else if (isPersonnelPlanLockedError(err)) {
          updateRow(localKey, {
            saveStatus: "error",
            saveError: mapPersonnelError(err),
          });
          try {
            const fresh = await getPersonnelPlan(planId);
            applyPlan(fresh);
          } catch {
            /* reload best-effort */
          }
        } else {
          updateRow(localKey, {
            saveStatus: "error",
            saveError: mapPersonnelError(err),
          });
        }
      } finally {
        savingKeysRef.current.delete(localKey);
      }
    },
    [applyPlan, canEdit, refreshPlanTotals, updateRow],
  );

  const scheduleAutosave = useCallback(
    (localKey: string) => {
      if (!canEdit) return;
      const existing = debounceRef.current.get(localKey);
      if (existing) clearTimeout(existing);
      updateRow(localKey, { saveStatus: "dirty", saveError: null });
      const timer = setTimeout(() => {
        debounceRef.current.delete(localKey);
        void persistRow(localKey);
      }, PERSONNEL_AUTOSAVE_MS);
      debounceRef.current.set(localKey, timer);
    },
    [canEdit, persistRow, updateRow],
  );

  useEffect(() => {
    const timers = debounceRef.current;
    return () => {
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  function patchRowField(
    localKey: string,
    field: keyof DraftRow,
    value: string,
  ) {
    if (!canEdit) return;
    setRows((prev) =>
      prev.map((row) =>
        row.localKey === localKey
          ? {
              ...row,
              [field]: value,
              saveStatus: "dirty" as const,
              saveError: null,
            }
          : row,
      ),
    );
    scheduleAutosave(localKey);
  }

  function handleAddRow() {
    if (!canEdit || !plan) return;
    const draft = emptyDraftRow();
    setRows((prev) => [...prev, draft]);
    window.requestAnimationFrame(() => {
      const el = document.querySelector<HTMLInputElement>(
        `input[data-personnel-focus="${draft.localKey}"]`,
      );
      el?.focus();
    });
  }

  async function handleReloadRow(localKey: string) {
    const row = rowsRef.current.find((r) => r.localKey === localKey);
    const planId = planIdRef.current;
    if (!row?.id || !planId) return;
    try {
      const fresh = await getPersonnelPlan(planId);
      const serverLine = (fresh.lines ?? []).find((ln) => ln.id === row.id);
      if (!serverLine) {
        setRows((prev) => prev.filter((r) => r.localKey !== localKey));
        setPlan(fresh);
        return;
      }
      updateRow(localKey, {
        ...draftFromLine(serverLine),
        localKey: serverLine.id,
        saveStatus: "saved",
        saveError: null,
        versionConflict: false,
      });
      setPlan(fresh);
    } catch (err: unknown) {
      updateRow(localKey, {
        saveStatus: "error",
        saveError: mapPersonnelError(err),
      });
    }
  }

  async function handleArchive(localKey: string) {
    if (!canEdit) return;
    const row = rowsRef.current.find((r) => r.localKey === localKey);
    if (!row) return;
    if (!row.id) {
      setRows((prev) => prev.filter((r) => r.localKey !== localKey));
      return;
    }
    const confirmed = window.confirm(
      `Arquivar o cargo "${row.position_name || "sem nome"}"?\n\n` +
        "A linha será removida do planejamento ativo, mas permanecerá preservada no histórico técnico. Não há restauração nesta fase.",
    );
    if (!confirmed) return;
    const timer = debounceRef.current.get(localKey);
    if (timer) {
      clearTimeout(timer);
      debounceRef.current.delete(localKey);
    }
    try {
      await archivePersonnelPlanLine(row.id);
      setRows((prev) => prev.filter((r) => r.localKey !== localKey));
      if (planIdRef.current) await refreshPlanTotals(planIdRef.current);
    } catch (err: unknown) {
      updateRow(localKey, {
        saveStatus: "error",
        saveError: mapPersonnelError(err),
      });
    }
  }

  const readOnly = !canEdit;
  const lockReason = personnelPlanLockReason(plan);

  return (
    <PageShell
      title="Orçamento de Pessoal"
      subtitle="Preencha o headcount por cargo nos centros de custo atribuídos a você."
      icon={<Users size={28} strokeWidth={1.75} aria-hidden="true" />}
      actions={
        <>
          {canApprove ? (
            <a className="po-btn po-btn--secondary" href={pessoalApprovalsHref()}>
              Aprovações
            </a>
          ) : null}
          <a className="po-btn po-btn--secondary" href={routeHref("home")}>
            Voltar ao início
          </a>
        </>
      }
    >
      {bootLoading ? (
        <LoadingActivityCard title="Carregando Orçamento de Pessoal…" variant="panel" />
      ) : null}

      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      {!bootLoading && !error && !modulesUnlocked ? (
        <StateBox variant="warning" dismissible={false}>
          Leia e confirme as orientações orçamentárias para liberar a elaboração do módulo Pessoal.
        </StateBox>
      ) : null}

      {!bootLoading && !error && modulesUnlocked && responsibilities.length === 0 ? (
        <SectionCard
          title="Nenhum centro atribuído"
          hint="Responsabilidades do módulo personnel."
        >
          <p className="po-muted">
            Você ainda não possui centros de custo vinculados ao Orçamento de Pessoal neste
            exercício. Solicite à administração a atribuição de responsabilidade com o módulo{" "}
            <strong>personnel</strong>.
          </p>
        </SectionCard>
      ) : null}

      {!bootLoading && !error && responsibilities.length > 0 ? (
        <SectionCard
          title="Centros de custo"
          hint={exerciseTitle(exercise)}
        >
          <p className="po-muted">
            Selecione um centro para abrir o planejamento. Filiais 01 e 02 com o mesmo código
            aparecem separadamente.
          </p>
          <ul className="po-link-list po-personnel-cc-list">
            {responsibilities.map((row) => {
              const unit = row.unit_id || row.branch || "";
              const href = pessoalHref({
                costCenterId: row.cost_center_id,
                unitId: unit,
              });
              const active =
                selectedCc === row.cost_center_id &&
                (!selectedUnit || selectedUnit === unit);
              return (
                <li key={costCenterKey({ id: row.id, branch: unit, code: row.cost_center_id })}>
                  <a
                    href={href}
                    className={active ? "po-personnel-cc-link is-active" : "po-personnel-cc-link"}
                    aria-current={active ? "page" : undefined}
                  >
                    {labelForResponsibility(row)}
                  </a>
                </li>
              );
            })}
          </ul>
        </SectionCard>
      ) : null}

      {selectedCc &&
      selectedResponsibility &&
      exercise &&
      (canEditPerm || canSubmit) ? (
        <PersonnelPlanWorkflowPanel
          exercise={exercise}
          costCenterId={selectedCc}
          unitId={
            selectedUnit ||
            selectedResponsibility.unit_id ||
            selectedResponsibility.branch ||
            ""
          }
          areaId={selectedResponsibility.area_id}
          canSubmit={canSubmit}
          hasPendingLineWork={hasPendingLineWork}
          onPlanChange={handleWorkflowPlanChange}
          onSubmitted={handleWorkflowPlanChange}
          onFocusLine={focusLine}
        />
      ) : null}

      {selectedCc && selectedResponsibility ? (
        <SectionCard
          title={labelForResponsibility(selectedResponsibility)}
          hint={
            readOnly
              ? "Modo somente leitura"
              : "Rascunho com autosave por linha."
          }
        >
          {lockReason ? (
            <StateBox variant="warning" dismissible={false}>
              {lockReason}
            </StateBox>
          ) : null}

          {planLoading ? (
            <LoadingActivityCard title="Resolvendo planejamento…" variant="panel" />
          ) : null}

          {planError ? (
            <StateBox variant="error" dismissible={false}>
              {planError}
            </StateBox>
          ) : null}

          {planEmptyHint ? (
            <StateBox variant="default" dismissible={false}>
              {planEmptyHint}
            </StateBox>
          ) : null}

          {plan && !planLoading ? (
            <>
              {readOnly ? (
                <StateBox variant="default" dismissible={false}>
                  Modo somente leitura
                </StateBox>
              ) : null}
              <div className="po-kpi-grid po-personnel-totals" data-testid="personnel-totals">
                <div className="po-kpi-card">
                  <span className="po-kpi-card__label">Cargos</span>
                  <strong className="po-kpi-card__value">{plan.position_count}</strong>
                </div>
                {HEADCOUNT_COLUMNS.map((col) => (
                  <div className="po-kpi-card" key={col.field}>
                    <span className="po-kpi-card__label">Total {col.label}</span>
                    <strong className="po-kpi-card__value">
                      {plan.totals?.[col.field] ?? 0}
                    </strong>
                  </div>
                ))}
                <div className="po-kpi-card">
                  <span className="po-kpi-card__label">Linhas incompletas</span>
                  <strong className="po-kpi-card__value">{plan.incomplete_line_count}</strong>
                </div>
              </div>

              {canEdit ? (
                <div className="po-toolbar">
                  <button
                    type="button"
                    className="po-btn po-btn--primary"
                    onClick={handleAddRow}
                    data-testid="personnel-add-line"
                  >
                    <Plus size={16} aria-hidden="true" />
                    Adicionar cargo
                  </button>
                </div>
              ) : null}

              {rows.length === 0 ? (
                <p className="po-muted" data-testid="personnel-empty-lines">
                  Nenhum cargo neste planejamento.{" "}
                  {canEdit ? 'Use "Adicionar cargo" para começar.' : null}
                </p>
              ) : (
                <div className="po-table-wrap po-personnel-grid-wrap">
                  <table className="po-table po-personnel-grid">
                    <thead>
                      <tr>
                        <th>Cargo</th>
                        {HEADCOUNT_COLUMNS.map((col) => (
                          <th key={col.field}>{col.label}</th>
                        ))}
                        <th>Observações</th>
                        <th>Estado</th>
                        {canEdit ? <th>Ações</th> : null}
                      </tr>
                    </thead>
                    <tbody>
                      {rows.map((row) => (
                        <tr
                          key={row.localKey}
                          data-testid={`personnel-row-${row.localKey}`}
                          data-personnel-line-id={row.id ?? undefined}
                        >
                          <td data-label="Cargo">
                            <input
                              className="po-input"
                              value={row.position_name}
                              maxLength={POSITION_NAME_MAX_LENGTH}
                              readOnly={readOnly || row.versionConflict}
                              data-personnel-focus={row.localKey}
                              aria-label="Cargo"
                              onChange={(e) =>
                                patchRowField(row.localKey, "position_name", e.target.value)
                              }
                            />
                          </td>
                          {HEADCOUNT_COLUMNS.map((col) => (
                            <td data-label={col.label} key={col.field}>
                              <input
                                className="po-input po-input--narrow"
                                inputMode="numeric"
                                pattern="[0-9]*"
                                value={row[col.field]}
                                readOnly={readOnly || row.versionConflict}
                                aria-label={col.label}
                                onChange={(e) =>
                                  patchRowField(row.localKey, col.field, e.target.value)
                                }
                              />
                            </td>
                          ))}
                          <td data-label="Observações">
                            <input
                              className="po-input"
                              value={row.observations}
                              readOnly={readOnly || row.versionConflict}
                              aria-label="Observações"
                              onChange={(e) =>
                                patchRowField(row.localKey, "observations", e.target.value)
                              }
                            />
                          </td>
                          <td data-label="Estado de salvamento">
                            <span
                              className={`po-personnel-save po-personnel-save--${row.saveStatus}`}
                              data-testid={`personnel-save-${row.localKey}`}
                            >
                              {personnelSaveStatusLabel(row.saveStatus) || "—"}
                            </span>
                            {row.saveError ? (
                              <p className="po-field-error" role="alert">
                                {row.saveError}
                              </p>
                            ) : null}
                            {row.versionConflict ? (
                              <div className="po-personnel-conflict">
                                <p className="po-muted">
                                  Valores locais preservados para conferência.
                                </p>
                                <button
                                  type="button"
                                  className="po-btn po-btn--secondary po-btn--sm"
                                  onClick={() => void handleReloadRow(row.localKey)}
                                >
                                  <RefreshCw size={14} aria-hidden="true" />
                                  Recarregar a linha
                                </button>
                              </div>
                            ) : null}
                          </td>
                          {canEdit ? (
                            <td data-label="Ações">
                              <button
                                type="button"
                                className="po-btn po-btn--secondary po-btn--sm"
                                onClick={() => void handleArchive(row.localKey)}
                                aria-label="Arquivar linha"
                              >
                                <Archive size={14} aria-hidden="true" />
                                Arquivar
                              </button>
                            </td>
                          ) : null}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          ) : null}
        </SectionCard>
      ) : null}

      {!selectedCc && responsibilities.length > 0 && !bootLoading ? (
        <StateBox variant="default" dismissible={false}>
          Selecione um centro de custo acima para abrir a grade de headcount.
        </StateBox>
      ) : null}

      {selectedCc && !selectedResponsibility && !bootLoading && responsibilities.length > 0 ? (
        <StateBox variant="warning" dismissible={false}>
          O centro indicado na URL não está entre suas responsabilidades de Pessoal (verifique
          filial e código).
        </StateBox>
      ) : null}
    </PageShell>
  );
}
