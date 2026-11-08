/** Nova solicitação PRC — wizard em 3 etapas:
 * 1) Identificação (criação × alteração + código/revisão-base em update)
 * 2) Ficha técnica (campos do catálogo + fornecedores)
 * 3) Revisão e envio idempotente via POST intake existente.
 * `requesterSubject` nunca é forjado — o backend deriva do JWT.
 * `source` vem da allowlist do reference-data ("portal-engineering"). */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringFormActions,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringProgressTracker,
  EngineeringSearchableSelect,
  EngineeringSectionCard,
  EngineeringSegmentToggle,
  EngineeringStateBanner,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import {
  enumOptions,
  PRC_CATALOG_KINDS,
  PrcCatalogStore,
  withSelectedOption,
  type PrcCatalogView,
} from "../prcCatalogs";
import {
  fetchPrcEditContext,
  fetchPrcReferenceData,
  prcIntakeSubmit,
  type PrcEditContext,
  type PrcIntakeBody,
  type PrcReferenceData,
  type PrcSupplierLinkChange,
} from "../api/productRegistrationApi";
import {
  buildPrcQueueUrl,
  EMPTY_PRC_QUEUE_URL,
  navigatePrc,
  navigatePrcHref,
  PRC_PATHS,
} from "../prcNavigate";
import {
  PRC_COPY,
  PRC_FIELD_HELP,
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_HELP,
  PRC_SUPPLIER_LABELS,
  PRC_VALIDATION,
} from "../prcCopy";
import {
  computeLinkDiff,
  computeScalarDiff,
  linkKeyOf,
} from "../prcDiff";
import {
  duplicateSupplierIndexes,
  emptySupplierRow,
  type SupplierRow,
} from "../prcSuppliers";
import { PrcReasonField } from "../components/PrcReasonField";
import { PrcSupplierCellLookup } from "../components/PrcSupplierLookup";

const STEPS = [
  { id: "identify", label: "Identificação" },
  { id: "sheet", label: "Ficha técnica" },
  { id: "review", label: "Revisar e enviar" },
];

const PORTAL_SOURCE = "portal-engineering";

const FIELD_GROUPS: { title: string; paths: string[] }[] = [
  {
    title: "Identificação e classificação",
    paths: ["description", "group", "productKind", "unit"],
  },
  {
    title: "Estoque e contabilidade",
    paths: [
      "defaultWarehouse",
      "accountingAccount",
      "thirdPartyProduct",
      "customerReference",
    ],
  },
];

function newIdemKey(): string {
  const uuid =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `prc-intake-${uuid}`;
}

export function PrcCreatePage({ basePath }: { basePath: string }) {
  const [refData, setRefData] = useState<PrcReferenceData | null>(null);
  /* Store estável por instância — init lazy via useState (nunca recriado
   * em re-render; o estado dos catálogos vive fora do React state). */
  const [catalogStore] = useState(() => new PrcCatalogStore());
  const catalogViews = useSyncExternalStore(
    catalogStore.subscribe,
    catalogStore.getSnapshot,
  );
  const [loadError, setLoadError] = useState("");
  const [step, setStep] = useState(0);

  const [requestType, setRequestType] = useState<"create" | "update">(
    "create",
  );
  const [officialCode, setOfficialCode] = useState("");

  const [values, setValues] = useState<Record<string, string>>({});
  const [suppliers, setSuppliers] = useState<SupplierRow[]>([]);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [editCtx, setEditCtx] = useState<PrcEditContext | null>(null);
  const [editCtxState, setEditCtxState] = useState<
    "idle" | "loading" | "error" | "not_found"
  >("idle");
  const [removeMarks, setRemoveMarks] = useState<Set<string>>(new Set());

  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const idemKey = useRef(newIdemKey());

  useEffect(() => {
    const controller = new AbortController();
    fetchPrcReferenceData(controller.signal)
      .then((env) => {
        if (!controller.signal.aborted) setRefData(env.data);
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setLoadError(
            (e as HomeApiError).message ||
              "Falha ao carregar os dados de referência.",
          );
        }
      });
    /* Catálogos TOTVS via BFF — `idle → loading → success|empty|error`;
     * requests obsoletas são abortadas no unmount e nunca gravam estado. */
    catalogStore.loadAll(Object.keys(PRC_CATALOG_KINDS), controller.signal);
    return () => {
      controller.abort();
      catalogStore.abortAll();
    };
  }, [catalogStore]);

  const specByPath = useMemo(
    () => new Map((refData?.fields || []).map((s) => [s.path, s] as const)),
    [refData],
  );

  const sourceAllowed = useMemo(() => {
    if (!refData) return true; // ainda carregando — o backend decide
    return refData.sources.includes(PORTAL_SOURCE);
  }, [refData]);

  const backToQueue = useCallback(() => {
    navigatePrcHref(buildPrcQueueUrl(basePath, EMPTY_PRC_QUEUE_URL));
  }, [basePath]);

  const setValue = (path: string, v: string) =>
    setValues((s) => ({ ...s, [path]: v }));

  const validateStep = (index: number): string => {
    if (index === 0) {
      if (requestType === "update") {
        if (!officialCode.trim())
          return "Informe o código oficial do produto a alterar.";
      }
      return "";
    }
    if (index === 1) {
      if (requestType === "create") {
        for (const spec of refData?.fields || []) {
          if (!spec.requiredCreateIntake) continue;
          if (spec.kind === "suppliers") continue;
          const v = (values[spec.path] || "").trim();
          if (!v && spec.kind !== "text") {
            return `Preencha «${PRC_FIELD_LABELS[spec.path] || spec.path}».`;
          }
        }
      } else {
        if (!scalarDiff.length && !linkOps.length) {
          return "Nenhuma alteração identificada — edite um campo, vínculo ou adicione um fornecedor.";
        }

      }
      const bad = suppliers.findIndex(
        (r) => !r.supplierCode.trim() || !r.store.trim() || !r.supplierName.trim(),
      );
      if (bad >= 0) {
        return `Fornecedor ${bad + 1}: ${PRC_SUPPLIER_HELP.selectRequired}`;
      }
      if (duplicateSupplierIndexes(suppliers).size > 0) {
        return PRC_SUPPLIER_HELP.duplicate;
      }

      return "";
    }
    return "";
  };

  const baselineFields: Record<string, unknown> = {};
  Object.entries(editCtx?.fields || {}).forEach(([p, f]) => {
    baselineFields[p] = f?.value;
  });
  const scalarPaths = (refData?.fields || [])
    .filter((spec) => spec.kind !== "suppliers" && spec.path !== "officialProductCode")
    .map((spec) => spec.path);
  const scalarDiff =
    requestType === "update" && editCtx
      ? computeScalarDiff(baselineFields, values, scalarPaths)
      : [];
  const changedPaths = new Set(scalarDiff.map((c) => c.path));
  const officialKeys = new Set(
    (editCtx?.links || []).map((l) => linkKeyOf(l.supplierCode, l.store)),
  );
  const linkOps =
    requestType === "update" && editCtx
      ? computeLinkDiff(editCtx.links || [], suppliers, removeMarks)
      : [];

  const next = () => {
    const msg = validateStep(step);
    if (msg) {
      setError(msg);
      return;
    }
    setError("");
    if (requestType === "update" && step === 0) {
      setEditCtxState("loading");
      fetchPrcEditContext(officialCode)
        .then((env) => {
          const d = env.data as PrcEditContext;
          if (d.status !== "available") {
            setEditCtx(null);
            setEditCtxState(
              d.status === "not_found" ? "not_found" : "error",
            );
            return;
          }
          setEditCtx(d);
          setEditCtxState("idle");
          /* D13 — working copy semeada do baseline oficial: o usuário
           * edita diretamente os valores reais, e o diff é automático. */
          setValues(
            Object.fromEntries(
              Object.entries(d.fields || {}).map(([path, f]) => [
                path,
                f?.value === null || f?.value === undefined
                  ? ""
                  : String(f.value),
              ]),
            ),
          );
          setSuppliers(
            (d.links || []).map((l) => ({
              ...emptySupplierRow(),
              supplierCode: l.supplierCode,
              store: l.store,
              supplierName: l.supplierName,
              partNumber: l.partNumber || "",
              catalogNumber: l.catalogNumber || "",
            })),
          );
        })
        .catch(() => {
          setEditCtx(null);
          setEditCtxState("error");
        });
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const back = () => {
    setError("");
    setStep((s) => Math.max(0, s - 1));
  };

  const buildBody = (): PrcIntakeBody => {
    if (requestType === "create") {
      const requestedData: Record<string, unknown> = {};
      for (const spec of refData?.fields || []) {
        if (spec.path === "suppliers") continue;
        const raw = (values[spec.path] || "").trim();
        if (raw || spec.requiredCreateIntake || spec.kind === "text") {
          requestedData[spec.path] = raw;
        }
      }
      requestedData.suppliers = suppliers.map((r) => ({
        supplierCode: r.supplierCode.trim(),
        store: r.store.trim(),
        supplierName: r.supplierName.trim(),
        partNumber: r.partNumber.trim() || "",
        catalogNumber: r.catalogNumber.trim() || null,
      }));
      return {
        source: PORTAL_SOURCE,
        requestType: "create",
        productType: refData?.productTypes?.[0] || "raw_material",
        schemaVersion: refData?.schemaVersion || 1,
        requestedData,
      };
    }
    const changes: Array<{
      path: string;
      proposedValue: unknown;
      reason: string;
    }> = scalarDiff.map((change) => ({
      path: change.path,
      proposedValue: change.after,
      reason: (reasons[change.path] || "").trim(),
    }));
    const rowByKey = new Map(
      suppliers.map((r) => [linkKeyOf(r.supplierCode, r.store), r]),
    );
    const supplierLinkChanges: PrcSupplierLinkChange[] = linkOps.map(
      (op) => {
        const row = rowByKey.get(
          linkKeyOf(op.key.supplierCode, op.key.store),
        );
        const fieldReasons: Record<string, string> = {};
        if (row?.pnReason?.trim())
          fieldReasons.partNumber = row.pnReason.trim();
        if (row?.catReason?.trim())
          fieldReasons.catalogNumber = row.catReason.trim();
        return {
          operation: op.operation,
          key: op.key,
          fields: op.operation === "remove" ? {} : op.fields,
          reason: (row?.opReason || "").trim(),
          ...(Object.keys(fieldReasons).length
            ? { fieldReasons }
            : {}),
        };
      },
    );
    return {
      source: PORTAL_SOURCE,
      requestType: "update",
      productType: refData?.productTypes?.[0] || "raw_material",
      schemaVersion: refData?.schemaVersion || 1,
      officialProductCode: officialCode.trim(),
      changes,
      supplierLinkChanges,
    };
  };

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    setFieldErrors({});
    try {
      const env = await prcIntakeSubmit(buildBody(), idemKey.current);
      navigatePrc(PRC_PATHS.detail(env.data.requestId), basePath);
    } catch (e) {
      const err = e as HomeApiError & {
        fields?: Record<string, string>;
      };
      if (err.fields) setFieldErrors(err.fields);
      setError(err.message || "Falha ao enviar a solicitação.");
      /* Chave mantida — retry do usuário é replay seguro no backend. */
    } finally {
      setBusy(false);
    }
  };

  const renderCatalogField = (
    path: string,
    spec: PrcReferenceData["fields"][number] | undefined,
    label: string,
  ) => {
    const view: PrcCatalogView =
      catalogViews.get(path) ?? {
        status: "idle",
        options: [],
        hasMore: false,
      };
    const selected = values[path] || "";
    const options = withSelectedOption(view.options, selected);
    const loading = view.status === "loading" || view.status === "idle";
    const hint = loading
      ? "Carregando catálogo oficial TOTVS…"
      : view.status === "empty"
        ? "Catálogo oficial sem itens disponíveis."
        : view.status === "error"
          ? "Falha ao consultar o catálogo oficial TOTVS."
          : PRC_FIELD_HELP[path] || spec?.note || "Catálogo oficial TOTVS";
    return (
      <>
        <EngineeringSearchableSelect
          id={`prc-new-${path}`}
          label={label}
          hint={hint}
          searchable
          value={selected}
          onChange={(v) => setValue(path, v)}
          options={options}
          placeholder={
            loading ? "Carregando catálogo…" : "Selecionar…"
          }
          required={
            requestType === "create" &&
            Boolean(spec?.requiredCreateIntake)
          }
          disabled={
            busy ||
            loading ||
            view.status === "empty" ||
            (view.status === "error" && !options.length)
          }
        />
        {view.status === "error" ? (
          <div className="engineering-prc__catalog-error">
            <p className="engineering-prc__field-error" role="alert">
              {selected
                ? `${PRC_VALIDATION.catalogUnavailable} O valor selecionado foi preservado, mas ainda não foi revalidado.`
                : PRC_VALIDATION.catalogUnavailable}
            </p>
            <EngineeringActionButton
              variant="ghost"
              disabled={busy}
              onClick={() => catalogStore.retry(path)}
            >
              Tentar novamente
            </EngineeringActionButton>
          </div>
        ) : null}
        {view.hasMore ? (
          <p className="engineering-prc__muted">
            Exibindo os primeiros {view.options.length} itens — refine
            pela busca.
          </p>
        ) : null}
      </>
    );
  };

  const renderSheetField = (path: string) => {
    const spec = specByPath.get(path);
    const label = PRC_FIELD_LABELS[path] || path;
    const selected = true;
    const changed = requestType === "update" && changedPaths.has(path);
    const baseline = baselineFields[path];
    return (
      <div
        key={path}
        className={`engineering-prc__edit-row${
          changed ? " engineering-prc__edit-row--changed" : ""
        }`}
      >
        {requestType === "update" && changed ? (
          <div className="engineering-prc__diff-badge">
            <span className="engineering-prc__diff-tag">Alterado</span>
            <span className="engineering-prc__muted">
              Anterior no TOTVS:{" "}
              <strong>{String(baseline ?? "") || "vazio"}</strong>
            </span>
            <button
              type="button"
              className="engineering-prc__lookup-clear"
              onClick={() =>
                setValue(
                  path,
                  baseline === null || baseline === undefined
                    ? ""
                    : String(baseline),
                )
              }
            >
              Desfazer
            </button>
          </div>
        ) : null}
        {selected ? (
          <div className="engineering-prc__edit-controls">
            {PRC_CATALOG_KINDS[path] ? (
              renderCatalogField(path, spec, label)
            ) : spec?.enumValues?.length ? (
              <EngineeringSearchableSelect
                id={`prc-new-${path}`}
                label={label}
                hint={PRC_FIELD_HELP[path] || spec.note || undefined}
                value={values[path] || ""}
                onChange={(v) => setValue(path, v)}
                options={enumOptions(path, spec.enumValues)}
                placeholder="Selecionar…"
                required={Boolean(spec.requiredCreateIntake)}
                disabled={busy}
              />
            ) : (
              <EngineeringTextField
                id={`prc-new-${path}`}
                label={label}
                hint={PRC_FIELD_HELP[path] || spec?.note || undefined}
                value={values[path] || ""}
                onChange={(v) => setValue(path, v)}
                required={
                  requestType === "create" &&
                  Boolean(spec?.requiredCreateIntake)
                }
                maxLength={spec?.maxLength}
                disabled={busy}
              />
            )}
            {fieldErrors[path] ? (
              <p className="engineering-prc__field-error" role="alert">
                {fieldErrors[path]}
              </p>
            ) : null}
            {requestType === "update" ? (
              <PrcReasonField
                id={`prc-new-reason-${path}`}
                value={reasons[path] || ""}
                onChange={(v) =>
                  setReasons((s) => ({ ...s, [path]: v }))
                }
                disabled={busy}
              />
            ) : null}
          </div>
        ) : (
          <span className="engineering-prc__muted">Não alterado</span>
        )}
      </div>
    );
  };

  const reviewItems =
    requestType === "create"
      ? Object.entries(values)
          .filter(([, v]) => v.trim())
          .map(([path, v]) => ({
            label: PRC_FIELD_LABELS[path] || path,
            value: v,
          }))
      : scalarDiff.map((change) => ({
            label: `${PRC_FIELD_LABELS[change.path] || change.path} (alterado)`,
            value: `${change.before || "vazio"} → ${change.after || "vazio"} — ${reasons[change.path] || ""}`,
          }));

  if (loadError) {
    return (
      <main className="engineering-prc">
        <EngineeringStateBanner variant="error">
          {loadError}
        </EngineeringStateBanner>
        <EngineeringActionButton variant="primary" onClick={backToQueue}>
          Voltar para a fila
        </EngineeringActionButton>
      </main>
    );
  }

  if (!refData) {
    return (
      <main className="engineering-prc">
        <EngineeringLoadingActivityCard
          title="Preparando formulário"
          description="Carregando o catálogo de campos da Engineering API."
        />
      </main>
    );
  }

  return (
    <main className="engineering-prc">
      <EngineeringPagePath
        back={{
          label: PRC_COPY.detailBreadcrumb,
          href: `${basePath}/${PRC_PATHS.queue}`,
          onNavigate: (event) => {
            event.preventDefault();
            backToQueue();
          },
        }}
        items={[]}
        current={PRC_COPY.newRequest}
      />

      <EngineeringPageHero
        eyebrow={PRC_COPY.breadcrumbRoot}
        title={PRC_COPY.newRequest}
        description={PRC_COPY.intakeNote}
      />

      <EngineeringProgressTracker
        steps={STEPS.map((s, i) => ({
          id: s.id,
          label: s.label,
          state:
            i < step ? "complete" : i === step ? "current" : "available",
        }))}
        currentStepId={STEPS[step].id}
        interactive
        onStepChange={(id) => {
          const target = STEPS.findIndex((s) => s.id === id);
          if (target <= step) {
            setError("");
            setStep(target);
          }
        }}
        ariaLabel="Etapas da nova solicitação"
      />

      {!sourceAllowed ? (
        <EngineeringStateBanner variant="error">
          A origem «{PORTAL_SOURCE}» não está autorizada pela Engineering API.
          Contate o administrador da plataforma.
        </EngineeringStateBanner>
      ) : null}

      {step === 0 ? (
        <EngineeringSectionCard
          title="O que precisa ser feito?"
          subtitle="Escolha o tipo de solicitação"
        >
          <EngineeringSegmentToggle
            ariaLabel="Tipo de solicitação"
            value={requestType}
            onChange={(v) => {
              setRequestType(v);
              setError("");
            }}
            options={[
              {
                value: "create",
                label: "Nova matéria-prima",
                ariaLabel: "Criar cadastro de matéria-prima",
              },
              {
                value: "update",
                label: "Alterar produto existente",
                ariaLabel: "Alterar produto existente",
              },
            ]}
            disabled={busy}
          />
          {requestType === "update" ? (
            <div className="engineering-prc__edit-controls">
              <EngineeringTextField
                id="prc-new-official-code"
                label="Código oficial TOTVS"
                hint="Código B1 do produto que será alterado."
                value={officialCode}
                onChange={setOfficialCode}
                required
                disabled={busy}
              />
              <p className="engineering-prc__muted">
                A revisão técnica de referência é identificada automaticamente
                pela Engineering API — não é preciso informá-la.
              </p>
            </div>
          ) : null}
        </EngineeringSectionCard>
      ) : null}

      {step === 1 ? (
        <>
          {FIELD_GROUPS.map((group) => (
            <EngineeringSectionCard key={group.title} title={group.title}>
              <div className="engineering-prc__form-grid">
                {group.paths.map((path) => (
                  <div
                    key={path}
                    className={
                      path === "description" || path === "officialProductCode"
                        ? "engineering-prc__form-grid--wide"
                        : ""
                    }
                  >
                    {renderSheetField(path)}
                  </div>
                ))}
              </div>
            </EngineeringSectionCard>
          ))}

          <EngineeringSectionCard
            title="Fornecedores"
            subtitle="Código + loja + nome obrigatórios; Part Number e catálogo opcionais"
            actions={
              <EngineeringActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setSuppliers((rows) => [...rows, emptySupplierRow()])}
              >
                + Adicionar fornecedor
              </EngineeringActionButton>
            }
          >
            {requestType === "update" && editCtxState === "loading" ? (
              <p className="engineering-prc__muted">
                Consultando vínculos oficiais…
              </p>
            ) : null}
            {editCtx && editCtx.linksComplete === false ? (
              <p className="engineering-prc__field-error" role="alert">
                A lista de vínculos pode estar incompleta — revise
                antes de propor alterações.
              </p>
            ) : null}
            {requestType === "create" || requestType === "update" ? (
              <>
                {suppliers.length ? (
                  <div className="engineering-prc__supplier-table-wrap">
                    <table className="engineering-prc__supplier-table">
                      <caption className="engineering-prc__sr-only">
                        Vínculos de fornecedores do produto
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Fornecedor</th>
                          <th scope="col">Loja</th>
                          <th scope="col">Razão social</th>
                          <th scope="col">{PRC_SUPPLIER_LABELS.partNumber}</th>
                          <th scope="col">{PRC_SUPPLIER_LABELS.catalogNumber}</th>
                          <th scope="col">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {suppliers.map((row, index) => {
                          const missing =
                            !row.supplierCode.trim() ||
                            !row.store.trim() ||
                            !row.supplierName.trim();
                          const dup =
                            duplicateSupplierIndexes(suppliers).has(index);
                          const key = linkKeyOf(row.supplierCode, row.store);
                          const isOfficial = officialKeys.has(key);
                          const markedRemove = removeMarks.has(key);
                          const rowClass = markedRemove
                            ? "engineering-prc__supplier-tr--remove"
                            : isOfficial && requestType === "update"
                              ? ""
                              : "engineering-prc__supplier-tr--added";
                          return (
                            <tr
                              key={index}
                              className={missing || dup ? "engineering-prc__supplier-tr--error" : rowClass}
                            >
                              <td data-label="Fornecedor">
                                {row.supplierCode ? (
                                  <span>{row.supplierCode}</span>
                                ) : row.searchOpen ? (
                                <PrcSupplierCellLookup
                                  id={`prc-new-sup-${index}`}
                                  displayValue={
                                    row.supplierCode
                                      ? `${row.supplierCode} / ${row.store} — ${row.supplierName}`
                                      : ""
                                  }
                                  query={row.query}
                                  disabled={busy}
                                  onQueryChange={(v) =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index ? { ...r, query: v } : r,
                                      ),
                                    )
                                  }
                                  onSelect={(hit) =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index
                                          ? {
                                              ...r,
                                              supplierCode: String(
                                                hit.supplier_code ?? "",
                                              ),
                                              store: String(
                                                hit.supplier_store ?? "",
                                              ),
                                              supplierName: String(
                                                hit.supplier_name ?? "",
                                              ),
                                              query: "",
                                              searchOpen: false,
                                            }
                                          : r,
                                      ),
                                    )
                                  }
                                  onClear={() =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index
                                          ? {
                                              ...r,
                                              supplierCode: "",
                                              store: "",
                                              supplierName: "",
                                              query: "",
                                            }
                                          : r,
                                      ),
                                    )
                                  }
                                />
                                ) : (
                                  <button
                                    type="button"
                                    className="engineering-prc__lookup-clear"
                                    aria-label="Buscar fornecedor por código, razão social ou nome fantasia"
                                    onClick={() =>
                                      setSuppliers((rows) =>
                                        rows.map((r, i) =>
                                          i === index
                                            ? { ...r, searchOpen: true }
                                            : r,
                                        ),
                                      )
                                    }
                                  >
                                    🔍
                                  </button>
                                )}
                                {missing ? (
                                  <span className="engineering-prc__field-error" role="alert">
                                    Selecione um fornecedor oficial.
                                  </span>
                                ) : null}
                                {dup && !missing ? (
                                  <span className="engineering-prc__field-error" role="alert">
                                    Vínculo duplicado (mesmo código e loja).
                                  </span>
                                ) : null}
                              </td>
                              <td data-label="Loja">{row.store || "—"}</td>
                              <td data-label="Razão social">{row.supplierName || "—"}</td>
                              <td data-label={PRC_SUPPLIER_LABELS.partNumber}>
                                <input
                                  id={`prc-new-sup-pn-${index}`}
                                  type="text"
                                  className="engineering-prc__cell-input"
                                  aria-label={`${PRC_SUPPLIER_LABELS.partNumber} (opcional)`}
                                  title={PRC_SUPPLIER_HELP.partNumberHint}
                                  value={row.partNumber}
                                  disabled={busy}
                                  onChange={(e) =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index
                                          ? { ...r, partNumber: e.target.value }
                                          : r,
                                      ),
                                    )
                                  }
                                />
                                <PrcReasonField
                                  id={`prc-sup-pn-reason-${index}`}
                                  value={row.pnReason || ""}
                                  onChange={(v) =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index ? { ...r, pnReason: v } : r,
                                      ),
                                    )
                                  }
                                  disabled={busy}
                                />
                              </td>
                              <td data-label={PRC_SUPPLIER_LABELS.catalogNumber}>
                                <input
                                  id={`prc-new-sup-cat-${index}`}
                                  type="text"
                                  className="engineering-prc__cell-input"
                                  aria-label={PRC_SUPPLIER_LABELS.catalogNumber}
                                  value={row.catalogNumber}
                                  disabled={busy}
                                  onChange={(e) =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index
                                          ? {
                                              ...r,
                                              catalogNumber: e.target.value,
                                            }
                                          : r,
                                      ),
                                    )
                                  }
                                />
                                <PrcReasonField
                                  id={`prc-sup-cat-reason-${index}`}
                                  value={row.catReason || ""}
                                  onChange={(v) =>
                                    setSuppliers((rows) =>
                                      rows.map((r, i) =>
                                        i === index ? { ...r, catReason: v } : r,
                                      ),
                                    )
                                  }
                                  disabled={busy}
                                />
                              </td>
                              <td data-label="Ações">
                                {requestType === "update" && isOfficial ? (
                                  markedRemove ? (
                                    <EngineeringActionButton
                                      variant="ghost"
                                      disabled={busy}
                                      onClick={() =>
                                        setRemoveMarks((prev) => {
                                          const next = new Set(prev);
                                          next.delete(key);
                                          return next;
                                        })
                                      }
                                    >
                                      Desfazer remoção
                                    </EngineeringActionButton>
                                  ) : (
                                    <EngineeringActionButton
                                      variant="ghost"
                                      disabled={busy}
                                      aria-label={`Solicitar remoção do vínculo ${row.supplierCode}/${row.store}`}
                                      onClick={() =>
                                        setRemoveMarks((prev) =>
                                          new Set(prev).add(key),
                                        )
                                      }
                                    >
                                      Remover
                                    </EngineeringActionButton>
                                  )
                                ) : (
                                  <EngineeringActionButton
                                    variant="ghost"
                                    disabled={busy}
                                    onClick={() =>
                                      setSuppliers((rows) =>
                                        rows.filter((_, i) => i !== index),
                                      )
                                    }
                                  >
                                    Remover
                                  </EngineeringActionButton>
                                )}
                                {markedRemove ? (
                                  <>
                                    <p className="engineering-prc__remove-tag">
                                      Remoção solicitada — será proposta ao
                                      TOTVS.
                                    </p>
                                    <PrcReasonField
                                      id={`prc-sup-rm-reason-${index}`}
                                      value={row.opReason || ""}
                                      onChange={(v) =>
                                        setSuppliers((rows) =>
                                          rows.map((r, i) =>
                                            i === index
                                              ? { ...r, opReason: v }
                                              : r,
                                          ),
                                        )
                                      }
                                      disabled={busy}
                                    />
                                  </>
                                ) : null}
                                {!isOfficial &&
                                requestType === "update" ? (
                                  <p className="engineering-prc__add-tag">
                                    Adicionado
                                  </p>
                                ) : null}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ) : null}
                {!suppliers.length ? (
                  <p className="engineering-prc__muted">
                    Nenhum fornecedor adicionado.
                  </p>
                ) : null}

              </>
            ) : (
              <p className="engineering-prc__muted">
                Vínculos de fornecedores não serão alterados.
              </p>
            )}
          </EngineeringSectionCard>
        </>
      ) : null}

      {step === 2 ? (
        <EngineeringDetailCard
          title="Resumo da solicitação"
          hint={PRC_COPY.intakeNote}
        >
          <EngineeringDetailFieldGrid
            fields={[
              {
                label: "Tipo",
                value:
                  requestType === "create"
                    ? "Criação de matéria-prima"
                    : "Alteração de produto",
              },
              ...(requestType === "update"
                ? [
                    { label: "Código oficial", value: officialCode },
                    {
                      label: "Operações de vínculo",
                      value: linkOps.length
                        ? linkOps
                            .map((o) => {
                              const k = `${o.key.supplierCode}/${o.key.store}`;
                              if (o.operation === "add")
                                return `+ ${k}`;
                              if (o.operation === "remove")
                                return `− ${k} (remoção solicitada)`;
                              const parts = Object.keys(o.fields)
                                .join("+");
                              return `~ ${k} (${parts})`;
                            })
                            .join(" · ")
                        : "Não alterado",
                    },
                  ]
                : []),
              ...reviewItems,
              {
                label: "Fornecedores",
                value:
                  requestType === "create"
                    ? `${suppliers.length} vínculo(s)`
                    : `${linkOps.length} operação(ões)`,
              },
            ]}
          />
          {Object.keys(fieldErrors).length ? (
            <EngineeringStateBanner variant="error">
              {Object.entries(fieldErrors)
                .map(
                  ([k, v]) =>
                    `${PRC_FIELD_LABELS[k] || k}: ${v}`,
                )
                .join(" · ")}
            </EngineeringStateBanner>
          ) : null}
        </EngineeringDetailCard>
      ) : null}

      {error ? (
        <EngineeringStateBanner variant="error">{error}</EngineeringStateBanner>
      ) : null}

      <EngineeringFormActions align="end">
        <EngineeringActionButton
          variant="ghost"
          softDisabled={busy}
          onClick={backToQueue}
        >
          Cancelar
        </EngineeringActionButton>
        {step > 0 ? (
          <EngineeringActionButton
            variant="default"
            softDisabled={busy}
            onClick={back}
          >
            Voltar
          </EngineeringActionButton>
        ) : null}
        {step < STEPS.length - 1 ? (
          <EngineeringActionButton variant="primary" onClick={next}>
            Avançar
          </EngineeringActionButton>
        ) : (
          <EngineeringActionButton
            variant="primary"
            softDisabled={busy || !sourceAllowed}
            onClick={submit}
          >
            Enviar solicitação
          </EngineeringActionButton>
        )}
      </EngineeringFormActions>
    </main>
  );
}
