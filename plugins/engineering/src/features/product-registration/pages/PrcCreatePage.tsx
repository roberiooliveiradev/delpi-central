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
import { Plus } from "lucide-react";

import { HomeApiError } from "../../../api/httpClient";
import { ENGINEERING_PORTAL_SCOPE } from "../../../ui/engineeringUi";
import {
  EngineeringActionButton,
  EngineeringAttachmentPreviewStrip,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringFileDropzone,
  EngineeringFilePreviewModal,
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
  searchPrcSuppliers,
  uploadPrcAttachment,
  type PrcEditContext,
  type PrcIntakeBody,
  type PrcReferenceData,
} from "../api/productRegistrationApi";
import {
  PRC_ATTACHMENT_ACCEPT,
  PRC_ATTACHMENT_MAX_COUNT,
  PRC_ATTACHMENT_MAX_MB,
  prcFormatSize,
} from "../prcAttachments";
import {
  addSupportFiles,
  removeSupportFile,
  type PrcSupportFile,
} from "../prcSupportFiles";
import {
  buildPrcQueueUrl,
  EMPTY_PRC_QUEUE_URL,
  navigatePrc,
  navigatePrcHref,
  PRC_PATHS,
} from "../prcNavigate";
import {
  PRC_COPY,
  prcFieldHelp,
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_HELP,
  PRC_SUPPLIER_LABELS,
  PRC_VALIDATION,
} from "../prcCopy";
import {
  computeLinkDiff,
  computeLinkDiffDetailed,
  computeScalarDiff,
} from "../prcDiff";
import {
  duplicateDraftRowIds,
  emptySupplierRow,
  officialSupplierRow,
  type SupplierRow,
} from "../prcSuppliers";
import {
  PrcReasonField,
  PrcSupplierTable,
} from "@delpi/plugin-ui/index";
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
  /** D14-FIX-02 — remoção oficial marcada por `rowId` (nunca pela
   * chave SA5, que pode coincidir com uma candidata duplicada). */
  const [removeMarks, setRemoveMarks] = useState<Set<string>>(new Set());

  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [supplierErrorsVisible, setSupplierErrorsVisible] = useState(false);
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
      const missingPn = suppliers.findIndex((r) => !r.partNumber.trim());
      if (missingPn >= 0) {
        setSupplierErrorsVisible(true);
        return `Fornecedor ${missingPn + 1}: ${PRC_SUPPLIER_HELP.partNumberRequired}`;
      }
      if (duplicateDraftRowIds(suppliers).size > 0) {
        return PRC_SUPPLIER_HELP.duplicateExisting;
      }
      if (requestType === "update" && editCtx) {
        const detailed = computeLinkDiffDetailed(
          editCtx.links || [],
          suppliers,
          removeMarks,
        );
        if (detailed.ambiguousOfficialKeys.length) {
          return "Há vínculos oficiais ambíguos para a mesma chave — operação bloqueada.";
        }
        if (detailed.conflictingKeys.length) {
          return PRC_SUPPLIER_HELP.duplicateExisting;
        }
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
          setRemoveMarks(new Set());
          setSuppliers((d.links || []).map((l) => officialSupplierRow(l)));
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

  /* D14-FIX / D14-FIX-02 — mutações por `rowId` (nunca índice). */
  /* Lookup SA2 compartilhado: o componente do kit recebe o fetcher do
   * MFE (Engineering API → api-delpi read-only). */
  const supplierSearchAdapter = (query: string, signal?: AbortSignal) =>
    searchPrcSuppliers(query, signal).then((env) => env.data?.items || []);

  const patchSupplierRow = (rowId: string, patch: Partial<SupplierRow>) =>
    setSuppliers((rows) =>
      rows.map((r) => (r.rowId === rowId ? { ...r, ...patch } : r)),
    );

  const toggleRowSearch = (rowId: string) =>
    setSuppliers((rows) =>
      rows.map((r) => ({
        ...r,
        searchOpen: r.rowId === rowId ? !r.searchOpen : false,
        selectionError:
          r.rowId === rowId ? undefined : r.selectionError,
      })),
    );

  const closeRowSearch = (rowId: string) =>
    patchSupplierRow(rowId, { searchOpen: false });

  const toggleSupplierReason = (
    rowId: string,
    flag: "pnReasonOpen" | "catReasonOpen" | "opReasonOpen",
  ) =>
    setSuppliers((rows) =>
      rows.map((r) =>
        r.rowId === rowId ? { ...r, [flag]: !r[flag] } : r,
      ),
    );

  const setSupplierReason = (
    rowId: string,
    flag: "pnReason" | "catReason" | "opReason",
    v: string,
  ) =>
    setSuppliers((rows) =>
      rows.map((r) => (r.rowId === rowId ? { ...r, [flag]: v } : r)),
    );

  /** Descartar candidata: remove só aquele `rowId`; nunca gera remove SA5. */
  const discardDraftRow = (rowId: string) => {
    setSuppliers((rows) => rows.filter((r) => r.rowId !== rowId));
    setRemoveMarks((prev) => {
      if (!prev.has(rowId)) return prev;
      const next = new Set(prev);
      next.delete(rowId);
      return next;
    });
  };

  /** Solicitar remoção oficial: marca só o `rowId` da linha official. */
  const markOfficialRemove = (rowId: string) =>
    setRemoveMarks((prev) => new Set(prev).add(rowId));

  const undoOfficialRemove = (rowId: string) =>
    setRemoveMarks((prev) => {
      const next = new Set(prev);
      next.delete(rowId);
      return next;
    });

  /* Nova linha draft nasce com busca fechada — só a lupa. */
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
          baselineFingerprint: editCtx?.fingerprint || null,
          editContextReadAt: editCtx?.readAt || null,
        });

  /* PRC-REF-023 — documentos opcionais: criado o caso (requestId real),
   * cada arquivo é enviado; falhas não derrubam a solicitação e ficam
   * retentáveis com o mesmo caseId preservado. Estados por arquivo:
   * selecionado → enviando → enviado | erro. Retry só reenvia os não
   * confirmados — nunca recria a solicitação. */
  const [supportFiles, setSupportFiles] = useState<PrcSupportFile[]>([]);
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({});
  const [uploadedIds, setUploadedIds] = useState<Set<string>>(new Set());
  const [createdRequestId, setCreatedRequestId] = useState<string | null>(
    null,
  );
  const [uploadSummary, setUploadSummary] = useState<string>("");
  const [previewFile, setPreviewFile] = useState<File | null>(null);

  const uploadSupportFiles = async (
    requestId: string,
    files: PrcSupportFile[],
  ) => {
    const failures: Record<string, string> = {};
    let ok = 0;
    for (const entry of files) {
      if (uploadedIds.has(entry.localId)) {
        ok += 1;
        continue;
      }
      try {
        await uploadPrcAttachment(requestId, entry.file);
        ok += 1;
        setUploadedIds((prev) => new Set(prev).add(entry.localId));
      } catch (e) {
        failures[entry.localId] = (e as Error).message || "Falha no upload.";
      }
    }
    return { ok, failures };
  };

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    setFieldErrors({});
    setUploadSummary("");
    try {
      const env = createdRequestId
        ? null
        : await prcIntakeSubmit(buildBody(), idemKey.current);
      const rid = createdRequestId || env!.data.requestId;
      if (!createdRequestId) setCreatedRequestId(rid);
      if (supportFiles.length) {
        const { ok, failures } = await uploadSupportFiles(rid, supportFiles);
        if (Object.keys(failures).length) {
          setFileErrors(failures);
          setUploadSummary(
            `Solicitação criada. ${ok} documento(s) anexado(s); ` +
              `${Object.keys(failures).length} falha(ram) — corrija e ` +
              "tente novamente sem recriar a solicitação.",
          );
          return;
        }
      }
      navigatePrc(PRC_PATHS.detail(rid), basePath);
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

  /* Miniaturas locais: object URL apenas para imagens; revogadas na
   * remoção/substituição/desmontagem (cleanup do effect). */
  const thumbUrls = useMemo(() => {
    const map = new Map<string, string>();
    supportFiles.forEach((entry) => {
      if ((entry.file.type || "").startsWith("image/")) {
        map.set(entry.localId, URL.createObjectURL(entry.file));
      }
    });
    return map;
  }, [supportFiles]);
  useEffect(
    () => () => {
      thumbUrls.forEach((url) => URL.revokeObjectURL(url));
    },
    [thumbUrls],
  );

  const downloadLocalFile = (f: File) => {
    const url = URL.createObjectURL(f);
    const a = document.createElement("a");
    a.href = url;
    a.download = f.name;
    a.rel = "noopener";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };

  const onPickSupportFiles = (list: File[] | FileList | null) => {
    const files = Array.from(list ?? []);
    if (!files.length) return;
    const { files: merged, errors } = addSupportFiles(
      supportFiles,
      files,
      PRC_ATTACHMENT_MAX_COUNT,
    );
    setSupportFiles(merged);
    setFileErrors(errors);
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
          : prcFieldHelp(path, spec?.note) || "Catálogo oficial TOTVS";
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
                hint={prcFieldHelp(path, spec.note)}
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
                hint={prcFieldHelp(path, spec?.note)}
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
                hint={prcFieldHelp("officialProductCode") || "Código atribuído ao produto no TOTVS. Preserve zeros à esquerda."}
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
            subtitle="Código + loja + nome + Part Number obrigatórios; Catálogo opcional"
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
                  <PrcSupplierTable
                    suppliers={suppliers}
                    removeMarks={removeMarks}
                    baselineLinks={editCtx?.links || []}
                    requestType={requestType}
                    busy={busy}
                    errorsVisible={supplierErrorsVisible}
                    partNumberLabel={PRC_SUPPLIER_LABELS.partNumber}
                    catalogLabel={PRC_SUPPLIER_LABELS.catalogNumber}
                    searchSuppliers={supplierSearchAdapter}
                    portalScopeClassName={ENGINEERING_PORTAL_SCOPE}
                    onPatchRow={patchSupplierRow}
                    onToggleSearch={toggleRowSearch}
                    onCloseSearch={closeRowSearch}
                    onToggleReason={toggleSupplierReason}
                    onSetReason={setSupplierReason}
                    onDiscardDraft={discardDraftRow}
                    onMarkRemove={markOfficialRemove}
                    onUndoRemove={undoOfficialRemove}
                  />
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

      {step === 1 ? (
        <EngineeringSectionCard
          title="Documentos de apoio (opcional)"
          subtitle={`Até ${PRC_ATTACHMENT_MAX_MB} MB por arquivo · máx. ${PRC_ATTACHMENT_MAX_COUNT} arquivos`}
        >
          <EngineeringFileDropzone
            disabled={busy}
            multiple
            accept={PRC_ATTACHMENT_ACCEPT}
            hideInput
            ariaLabel="Selecionar documentos de apoio"
            onFilesSelected={onPickSupportFiles}
            labels={{
              title: "Arraste arquivos ou clique para escolher",
              hint: `PDF ou imagens · até ${PRC_ATTACHMENT_MAX_MB} MB por arquivo · máx. ${PRC_ATTACHMENT_MAX_COUNT} arquivos`,
            }}
          />
          {supportFiles.length ? (
            <>
              <p className="engineering-prc__muted">
                Arquivos selecionados (ainda não enviados)
              </p>
              <EngineeringAttachmentPreviewStrip
                mode="manage"
                items={supportFiles.map((f) => ({
                  id: f.localId,
                  fileName: f.file.name,
                  contentType: f.file.type || null,
                  previewUrl: thumbUrls.get(f.localId) ?? null,
                  detail: `${prcFormatSize(f.file.size)} · ${
                    uploadedIds.has(f.localId)
                      ? "Enviado"
                      : busy
                        ? "Enviando…"
                        : fileErrors[f.localId]
                          ? `Erro — ${fileErrors[f.localId]}`
                          : "Selecionado"
                  }`,
                  busy,
                  removable: !uploadedIds.has(f.localId),
                }))}
                onOpen={(item) => {
                  const entry = supportFiles.find(
                    (f) => f.localId === item.id,
                  );
                  if (entry) setPreviewFile(entry.file);
                }}
                onRemove={(item) => {
                  setSupportFiles((s) => removeSupportFile(s, item.id));
                  setFileErrors((prev) => {
                    const next = { ...prev };
                    delete next[item.id];
                    return next;
                  });
                }}
              />
            </>
          ) : null}
          {uploadSummary ? (
            <EngineeringStateBanner variant="error">
              {uploadSummary}
            </EngineeringStateBanner>
          ) : null}
          {createdRequestId && uploadSummary ? (
            <EngineeringActionButton
              variant="primary"
              disabled={busy}
              onClick={() => void submit()}
            >
              Tentar enviar documentos novamente
            </EngineeringActionButton>
          ) : null}
          <EngineeringFilePreviewModal
            open={previewFile != null}
            title={previewFile?.name || "Documento"}
            source={previewFile}
            mimeType={previewFile?.type || null}
            fileName={previewFile?.name || null}
            metaItems={
              previewFile
                ? [
                    previewFile.type || null,
                    prcFormatSize(previewFile.size),
                    "Ainda não enviado",
                  ]
                : []
            }
            headerActions={
              previewFile ? (
                <EngineeringActionButton
                  variant="ghost"
                  onClick={() => previewFile && downloadLocalFile(previewFile)}
                >
                  Baixar
                </EngineeringActionButton>
              ) : null
            }
            onClose={() => setPreviewFile(null)}
          />
        </EngineeringSectionCard>
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
