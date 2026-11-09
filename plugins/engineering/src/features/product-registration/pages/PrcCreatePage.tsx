/** Nova solicitação PRC — wizard em 3 etapas:
 * 1) Identificação (criação × alteração + código/revisão-base em update)
 * 2) Ficha técnica (campos do catálogo + fornecedores)
 * 3) Revisão e envio idempotente via POST intake existente.
 * `requesterSubject` nunca é forjado — o backend deriva do JWT.
 * `source` vem da allowlist do reference-data ("portal-engineering"). */

import {
  Fragment,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { Plus, Search, Trash2, Undo2, X } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringFormActions,
  EngineeringIconButton,
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
import {
  PrcReasonEditor,
  PrcReasonField,
  PrcReasonToggle,
} from "../components/PrcReasonField";
import { PrcSupplierCellLookup } from "../components/PrcSupplierLookup";
import {
  buildCreateIntakeBody,
  buildUpdateIntakeBody,
  PRC_PORTAL_SOURCE,
} from "../prcIntakePayload";

const STEPS = [
  { id: "identify", label: "Identificação" },
  { id: "sheet", label: "Ficha técnica" },
  { id: "review", label: "Revisar e enviar" },
];

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
    return refData.sources.includes(PRC_PORTAL_SOURCE);
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
              supplierShortName: l.supplierShortName || "",
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

  /* D14-FIX — busca expansível por linha: no máximo uma aberta por
   * vez; o estado vive na própria linha e não desloca outras. */
  const toggleRowSearch = (index: number) =>
    setSuppliers((rows) =>
      rows.map((r, i) => ({
        ...r,
        searchOpen: i === index ? !r.searchOpen : false,
      })),
    );

  const closeRowSearch = (index: number) =>
    setSuppliers((rows) =>
      rows.map((r, i) =>
        i === index ? { ...r, searchOpen: false } : r,
      ),
    );

  const toggleSupplierReason = (
    index: number,
    flag: "pnReasonOpen" | "catReasonOpen" | "opReasonOpen",
  ) =>
    setSuppliers((rows) =>
      rows.map((r, i) => (i === index ? { ...r, [flag]: !r[flag] } : r)),
    );

  const setSupplierReason = (
    index: number,
    flag: "pnReason" | "catReason" | "opReason",
    v: string,
  ) =>
    setSuppliers((rows) =>
      rows.map((r, i) => (i === index ? { ...r, [flag]: v } : r)),
    );

  /* Nova linha nasce com busca fechada — só a lupa; o clique abre
   * a área colapsável (wireframe V2 / D14-FIX). */
  const addSupplierRow = () =>
    setSuppliers((rows) => [
      ...rows.map((r) => ({ ...r, searchOpen: false })),
      emptySupplierRow(),
    ]);

  const buildBody = (): PrcIntakeBody =>
    requestType === "create"
      ? buildCreateIntakeBody({ refData, values, reasons, suppliers })
      : buildUpdateIntakeBody({
          refData,
          officialCode,
          scalarDiff,
          linkOps,
          reasons,
          suppliers,
        });

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
    /* D14-FIX — justificativa só quando há alteração efetiva: UPDATE
     * usa o diff D13 contra o baseline; CREATE conta o preenchimento
     * como alteração (campo vazio não mostra o gatilho). */
    const reasonVisible =
      (requestType === "update" && changed) ||
      (requestType === "create" && (values[path] || "").trim() !== "");
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
            {reasonVisible ? (
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
          A origem «{PRC_PORTAL_SOURCE}» não está autorizada pela Engineering API.
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
                onClick={addSupplierRow}
              >
                <Plus size={15} aria-hidden /> Adicionar fornecedor
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
                          <th scope="col">Busca</th>
                          <th scope="col">Código</th>
                          <th scope="col">Loja</th>
                          <th scope="col">Razão social</th>
                          <th scope="col">Nome fantasia</th>
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
                          const baselineLink = isOfficial
                            ? (editCtx?.links || []).find(
                                (l) =>
                                  linkKeyOf(l.supplierCode, l.store) === key,
                              )
                            : undefined;
                          /* D14-FIX — UPDATE compara com o baseline SA5;
                           * linha nova (create/ADD) conta preenchimento
                           * como alteração efetiva do atributo. */
                          const pnChanged = isOfficial
                            ? row.partNumber.trim() !==
                              (baselineLink?.partNumber || "").trim()
                            : row.partNumber.trim() !== "";
                          const catChanged = isOfficial
                            ? row.catalogNumber.trim() !==
                              (baselineLink?.catalogNumber || "").trim()
                            : row.catalogNumber.trim() !== "";
                          /* Identidade de vínculo oficial SA5 nunca é
                           * substituída silenciosamente — troca real é
                           * remoção proposta + novo vínculo. */
                          const identityLocked = isOfficial;
                          const searchId = `prc-sup-search-${index}`;
                          const auxOpen = Boolean(
                            row.searchOpen ||
                              row.pnReasonOpen ||
                              row.catReasonOpen ||
                              row.opReasonOpen,
                          );
                          const rowClass = markedRemove
                            ? "engineering-prc__supplier-tr--remove"
                            : isOfficial && requestType === "update"
                              ? ""
                              : "engineering-prc__supplier-tr--added";
                          return (
                            <Fragment key={index}>
                              <tr
                                className={missing || dup ? "engineering-prc__supplier-tr--error" : rowClass}
                              >
                                <td
                                  data-label="Busca"
                                  className="engineering-prc__supplier-td--search"
                                >
                                  <span
                                    title={
                                      identityLocked
                                        ? "Identidade oficial do vínculo — para trocar o fornecedor, solicite a remoção e adicione um novo vínculo."
                                        : "Buscar por código, razão social ou nome fantasia"
                                    }
                                  >
                                    <EngineeringIconButton
                                      className="engineering-prc__search-toggle"
                                      aria-label={
                                        row.supplierCode
                                          ? `Alterar fornecedor da linha ${index + 1}`
                                          : `Buscar fornecedor da linha ${index + 1}`
                                      }
                                      aria-expanded={Boolean(row.searchOpen)}
                                      aria-controls={searchId}
                                      aria-haspopup="listbox"
                                      disabled={
                                        busy ||
                                        identityLocked ||
                                        markedRemove
                                      }
                                      onClick={() => toggleRowSearch(index)}
                                    >
                                      <Search size={15} aria-hidden />
                                    </EngineeringIconButton>
                                  </span>
                                </td>
                                <td data-label="Código">
                                  {row.supplierCode || "—"}
                                </td>
                                <td data-label="Loja">{row.store || "—"}</td>
                                <td data-label="Razão social">
                                  {row.supplierName || "—"}
                                  {missing ? (
                                    <span
                                      className="engineering-prc__cell-error"
                                      role="alert"
                                    >
                                      Selecione um fornecedor oficial.
                                    </span>
                                  ) : null}
                                  {dup && !missing ? (
                                    <span
                                      className="engineering-prc__cell-error"
                                      role="alert"
                                    >
                                      Vínculo duplicado (mesmo código e loja).
                                    </span>
                                  ) : null}
                                </td>
                                <td data-label="Nome fantasia">
                                  {row.supplierShortName || "—"}
                                </td>
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
                                  {isOfficial && pnChanged ? (
                                    <p className="engineering-prc__cell-diff">
                                      <span className="engineering-prc__diff-tag">
                                        Alterado
                                      </span>
                                      <span className="engineering-prc__muted">
                                        Anterior:{" "}
                                        <strong>
                                          {(baselineLink?.partNumber || "")
                                            .trim() || "vazio"}
                                        </strong>
                                      </span>
                                    </p>
                                  ) : null}
                                  {pnChanged ? (
                                    <PrcReasonToggle
                                      id={`prc-sup-pn-reason-${index}`}
                                      value={row.pnReason || ""}
                                      open={Boolean(row.pnReasonOpen)}
                                      disabled={busy}
                                      onToggle={() =>
                                        toggleSupplierReason(
                                          index,
                                          "pnReasonOpen",
                                        )
                                      }
                                    />
                                  ) : null}
                                </td>
                                <td data-label={PRC_SUPPLIER_LABELS.catalogNumber}>
                                  <input
                                    id={`prc-new-sup-cat-${index}`}
                                    type="text"
                                    className="engineering-prc__cell-input"
                                    aria-label={PRC_SUPPLIER_LABELS.catalogNumber}
                                    title={PRC_SUPPLIER_HELP.catalogHint}
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
                                  {isOfficial && catChanged ? (
                                    <p className="engineering-prc__cell-diff">
                                      <span className="engineering-prc__diff-tag">
                                        Alterado
                                      </span>
                                      <span className="engineering-prc__muted">
                                        Anterior:{" "}
                                        <strong>
                                          {(baselineLink?.catalogNumber || "")
                                            .trim() || "vazio"}
                                        </strong>
                                      </span>
                                    </p>
                                  ) : null}
                                  {catChanged ? (
                                    <PrcReasonToggle
                                      id={`prc-sup-cat-reason-${index}`}
                                      value={row.catReason || ""}
                                      open={Boolean(row.catReasonOpen)}
                                      disabled={busy}
                                      onToggle={() =>
                                        toggleSupplierReason(
                                          index,
                                          "catReasonOpen",
                                        )
                                      }
                                    />
                                  ) : null}
                                </td>
                                <td
                                  data-label="Ações"
                                  className="engineering-prc__supplier-td--actions"
                                >
                                  {requestType === "update" && isOfficial ? (
                                    markedRemove ? (
                                      <span title="Desfazer remoção">
                                        <EngineeringIconButton
                                          aria-label={`Desfazer remoção do vínculo ${row.supplierCode}/${row.store}`}
                                          disabled={busy}
                                          onClick={() =>
                                            setRemoveMarks((prev) => {
                                              const next = new Set(prev);
                                              next.delete(key);
                                              return next;
                                            })
                                          }
                                        >
                                          <Undo2 size={15} aria-hidden />
                                        </EngineeringIconButton>
                                      </span>
                                    ) : (
                                      <span title="Solicitar remoção">
                                        <EngineeringIconButton
                                          tone="danger"
                                          aria-label={`Solicitar remoção do vínculo ${row.supplierCode}/${row.store}`}
                                          disabled={busy}
                                          onClick={() =>
                                            setRemoveMarks((prev) =>
                                              new Set(prev).add(key),
                                            )
                                          }
                                        >
                                          <Trash2 size={15} aria-hidden />
                                        </EngineeringIconButton>
                                      </span>
                                    )
                                  ) : (
                                    <span title="Remover linha">
                                      <EngineeringIconButton
                                        tone="danger"
                                        aria-label={`Remover fornecedor da linha ${index + 1}`}
                                        disabled={busy}
                                        onClick={() =>
                                          setSuppliers((rows) =>
                                            rows.filter((_, i) => i !== index),
                                          )
                                        }
                                      >
                                        <Trash2 size={15} aria-hidden />
                                      </EngineeringIconButton>
                                    </span>
                                  )}
                                  {markedRemove ? (
                                    <>
                                      <p className="engineering-prc__remove-tag">
                                        Remoção solicitada — será proposta ao
                                        TOTVS.
                                      </p>
                                      <PrcReasonToggle
                                        id={`prc-sup-rm-reason-${index}`}
                                        value={row.opReason || ""}
                                        open={Boolean(row.opReasonOpen)}
                                        disabled={busy}
                                        onToggle={() =>
                                          toggleSupplierReason(
                                            index,
                                            "opReasonOpen",
                                          )
                                        }
                                      />
                                    </>
                                  ) : null}
                                  {!isOfficial && !missing ? (
                                    <>
                                      {requestType === "update" ? (
                                        <p className="engineering-prc__add-tag">
                                          Adicionado
                                        </p>
                                      ) : null}
                                      <PrcReasonToggle
                                        id={`prc-sup-add-reason-${index}`}
                                        value={row.opReason || ""}
                                        open={Boolean(row.opReasonOpen)}
                                        disabled={busy}
                                        label="Justificar inclusão"
                                        onToggle={() =>
                                          toggleSupplierReason(
                                            index,
                                            "opReasonOpen",
                                          )
                                        }
                                      />
                                    </>
                                  ) : null}
                                </td>
                              </tr>
                              {auxOpen ? (
                                <tr className="engineering-prc__supplier-aux">
                                  <td colSpan={8}>
                                    {row.searchOpen ? (
                                      <div
                                        id={searchId}
                                        className="engineering-prc__supplier-search"
                                        role="group"
                                        aria-label={`Busca de fornecedor da linha ${index + 1}`}
                                      >
                                        <div className="engineering-prc__supplier-search-head">
                                          <span className="engineering-prc__supplier-search-title">
                                            {row.supplierCode
                                              ? "Alterar seleção do fornecedor"
                                              : "Pesquisar fornecedor"}
                                          </span>
                                          <EngineeringIconButton
                                            aria-label="Fechar busca"
                                            onClick={() =>
                                              closeRowSearch(index)
                                            }
                                          >
                                            <X size={14} aria-hidden />
                                          </EngineeringIconButton>
                                        </div>
                                        <PrcSupplierCellLookup
                                          id={`prc-new-sup-${index}`}
                                          query={row.query}
                                          disabled={busy}
                                          onQueryChange={(v) =>
                                            setSuppliers((rows) =>
                                              rows.map((r, i) =>
                                                i === index
                                                  ? { ...r, query: v }
                                                  : r,
                                              ),
                                            )
                                          }
                                          onSelect={(hit) => {
                                            setSuppliers((rows) =>
                                              rows.map((r, i) =>
                                                i === index
                                                  ? {
                                                      ...r,
                                                      supplierCode: String(
                                                        hit.supplier_code ??
                                                          "",
                                                      ),
                                                      store: String(
                                                        hit.supplier_store ??
                                                          "",
                                                      ),
                                                      supplierName: String(
                                                        hit.supplier_name ??
                                                          "",
                                                      ),
                                                      supplierShortName:
                                                        String(
                                                          hit.supplier_short_name ??
                                                            "",
                                                        ),
                                                      query: "",
                                                      searchOpen: false,
                                                    }
                                                  : r,
                                              ),
                                            );
                                            /* Foco avança para o Part
                                             * Number da linha após a
                                             * seleção oficial. */
                                            window.requestAnimationFrame(
                                              () => {
                                                document
                                                  .getElementById(
                                                    `prc-new-sup-pn-${index}`,
                                                  )
                                                  ?.focus();
                                              },
                                            );
                                          }}
                                          onClose={() =>
                                            closeRowSearch(index)
                                          }
                                        />
                                        <p className="engineering-prc__muted">
                                          Ao escolher um resultado, código,
                                          loja e razão social são preenchidos
                                          automaticamente.
                                        </p>
                                      </div>
                                    ) : null}
                                    {pnChanged && row.pnReasonOpen ? (
                                      <PrcReasonEditor
                                        id={`prc-sup-pn-reason-${index}`}
                                        label={`Justificativa de ${PRC_SUPPLIER_LABELS.partNumber} (opcional)`}
                                        value={row.pnReason || ""}
                                        onChange={(v) =>
                                          setSupplierReason(
                                            index,
                                            "pnReason",
                                            v,
                                          )
                                        }
                                        disabled={busy}
                                        onCollapse={() =>
                                          toggleSupplierReason(
                                            index,
                                            "pnReasonOpen",
                                          )
                                        }
                                      />
                                    ) : null}
                                    {catChanged && row.catReasonOpen ? (
                                      <PrcReasonEditor
                                        id={`prc-sup-cat-reason-${index}`}
                                        label={`Justificativa de ${PRC_SUPPLIER_LABELS.catalogNumber} (opcional)`}
                                        value={row.catReason || ""}
                                        onChange={(v) =>
                                          setSupplierReason(
                                            index,
                                            "catReason",
                                            v,
                                          )
                                        }
                                        disabled={busy}
                                        onCollapse={() =>
                                          toggleSupplierReason(
                                            index,
                                            "catReasonOpen",
                                          )
                                        }
                                      />
                                    ) : null}
                                    {row.opReasonOpen &&
                                    (markedRemove ||
                                      (!isOfficial && !missing)) ? (
                                      <PrcReasonEditor
                                        id={`prc-sup-op-reason-${index}`}
                                        label={
                                          markedRemove
                                            ? "Justificativa da remoção (opcional)"
                                            : "Justificativa da inclusão (opcional)"
                                        }
                                        value={row.opReason || ""}
                                        onChange={(v) =>
                                          setSupplierReason(
                                            index,
                                            "opReason",
                                            v,
                                          )
                                        }
                                        disabled={busy}
                                        onCollapse={() =>
                                          toggleSupplierReason(
                                            index,
                                            "opReasonOpen",
                                          )
                                        }
                                      />
                                    ) : null}
                                  </td>
                                </tr>
                              ) : null}
                            </Fragment>
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
