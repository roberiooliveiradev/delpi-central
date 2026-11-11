/** PRC-REF-023-UI-FORM-UNIFICATION-05 — implementação única do
 * formulário PRC (wizard 3 etapas: Identificação → Ficha técnica →
 * Revisar e envio), consumida por Portal Engenharia e Minhas
 * Solicitações. A Engineering API permanece autoridade de dados,
 * workflow e validação final — este componente só monta a
 * experiência e o payload oficial via `PrcFormDataProvider` injetado
 * pelo MFE (não há URL/token/cliente HTTP no kit).
 *
 * Classes neutras `delpi-prc__*` (styles/delpi-prc.css) + componentes
 * genéricos do kit instanciados com prefixo `delpi-ui` — mesma
 * composição visual nos dois hosts. Shell, breadcrumb e navegação
 * pós-envio ficam no consumidor. */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { Plus } from "lucide-react";

import { ActionButton } from "../actions/ActionButton";
import { FilePreviewModal } from "../preview/FilePreviewModal";
import { createDashboardAttachmentPreviewStrip } from "../forms/AttachmentPreviewStrip";
import { createDashboardFileDropzone } from "../forms/FileDropzone";
import { createDashboardSegmentToggle } from "../forms/SegmentToggle";
import { createDashboardNativeFormFields } from "../forms/NativeFormFields";
import { createDashboardSelectField } from "../forms/SelectField";
import { createDashboardDetailCard } from "../layout/DetailCard";
import { createDashboardDetailFieldGrid } from "../layout/DetailFieldGrid";
import { createDashboardFormActions } from "../layout/FormActions";
import { createDashboardProgressTracker } from "../layout/ProgressTracker";
import { createDashboardSectionCard } from "../layout/SectionCard";
import { createDashboardLoadingActivityCard } from "../feedback/LoadingActivityCard";
import { createDashboardStateBanner } from "../feedback/StateBanner";
import { attachmentPreviewStripBemClasses } from "../forms/AttachmentPreviewStrip";
import { fileDropzoneBemClasses } from "../forms/FileDropzone";
import { formFieldShellBemClasses } from "../forms/FormFieldShell";
import { selectFieldPacClasses } from "../forms/SelectField";
import { detailCardRichBemClasses } from "../layout/DetailCard";
import { formActionsBemClasses } from "../layout/FormActions";
import { sectionCardPacBemClasses } from "../layout/SectionCard";
import { stateBannerBemClasses } from "../feedback/StateBanner";

import {
  addSupportFiles,
  applySupplierLinkOps,
  buildCreateIntakeBody,
  buildUpdateIntakeBody,
  computeLinkDiff,
  computeLinkDiffDetailed,
  computeScalarDiff,
  duplicateDraftRowIds,
  emptySupplierRow,
  enumOptions,
  officialSupplierRow,
  supplierRowsToPayload,
  toSupplierRows,
  PRC_ATTACHMENT_ACCEPT,
  PRC_ATTACHMENT_MAX_COUNT,
  PRC_ATTACHMENT_MAX_MB,
  PRC_CATALOG_KINDS,
  PRC_FIELD_GROUPS,
  PRC_FIELD_HELP,
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_LABELS,
  prcFormatSize,
  removeSupportFile,
  withSelectedOption,
  type PrcIntakeBody,
  type PrcReferenceData,
  type PrcSupportFile,
  type SupplierRow,
} from "../../utils/prcProductRegistration";
import {
  PrcCatalogStore,
  type PrcCatalogFetcher,
  type PrcCatalogView,
} from "../../utils/prcCatalogStore";
import {
  PRC_SUPPLIER_TEXT,
  PrcReasonField,
  PrcSupplierTable,
  type PrcSupplierSearchFn,
} from "./PrcSupplierForm";

/* ---------------- componentes neutros (mesmos nos dois hosts) ------ */

const PRC_UI_PREFIX = "delpi-ui";

const PrcSectionCard = createDashboardSectionCard({
  classNames: sectionCardPacBemClasses(PRC_UI_PREFIX),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});
const PrcStateBanner = createDashboardStateBanner({
  classNames: stateBannerBemClasses(PRC_UI_PREFIX),
});
const PrcLoadingCard = createDashboardLoadingActivityCard({
  prefix: PRC_UI_PREFIX,
  labels: {
    progressRemaining: (percent) => `Faltam ${percent}%`,
    progressAriaDeterminate: (percent) =>
      `Carregamento: faltam ${percent} por cento`,
    progressAriaIndeterminate: "Carregamento em andamento",
  },
});
const PrcDetailCard = createDashboardDetailCard({
  classNames: detailCardRichBemClasses(PRC_UI_PREFIX),
  labels: { titleHelpAriaLabel: (title) => `Ajuda: ${title}` },
});
const PrcDetailFieldGrid = createDashboardDetailFieldGrid({
  prefix: PRC_UI_PREFIX,
  labels: {
    emptyMessage: "Sem dados.",
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  wrapLabels: true,
});
const PrcProgressTracker = createDashboardProgressTracker({
  prefix: PRC_UI_PREFIX,
});
const PrcSegmentToggle = createDashboardSegmentToggle(PRC_UI_PREFIX);
const PrcTextField = createDashboardNativeFormFields({
  classNames: formFieldShellBemClasses(PRC_UI_PREFIX),
}).TextField;
const selectClasses = selectFieldPacClasses(PRC_UI_PREFIX);
const PrcSelectField = createDashboardSelectField({
  ...selectClasses,
  labels: {
    placeholder: "Selecionar…",
    emptyLabel: "—",
    control: {
      searchPlaceholder: "Buscar…",
      emptyOptions: "Nenhuma opção encontrada.",
      searchAriaLabel: (label?: string) =>
        label ? `Buscar em ${label}` : "Buscar opções",
    },
  },
});
const PrcFormActions = createDashboardFormActions({
  classNames: formActionsBemClasses(PRC_UI_PREFIX),
});
const PrcFileDropzone = createDashboardFileDropzone({
  classNames: fileDropzoneBemClasses(PRC_UI_PREFIX, "file-dropzone"),
  labels: {
    title: "Arraste arquivos ou clique para escolher",
    hint: "PDF ou imagens",
  },
});
const PrcAttachmentStrip = createDashboardAttachmentPreviewStrip({
  classNames: attachmentPreviewStripBemClasses(PRC_UI_PREFIX),
  labels: {
    empty: "Nenhum arquivo selecionado.",
    openAriaLabel: (fileName: string) => `Abrir ${fileName}`,
    removeAriaLabel: (fileName: string) => `Remover ${fileName}`,
  },
});

/* ---------------- contrato do provider (porta da Engineering API) -- */

export type PrcFormEditContextLink = {
  supplierCode: string;
  store: string;
  supplierName?: string;
  supplierShortName?: string;
  partNumber?: string | null;
  catalogNumber?: string | null;
};

export type PrcFormEditContext = {
  /** `available` | `not_found` | outro — ausente equivale a `available`. */
  status?: string;
  officialCode?: string;
  readAt?: string;
  fingerprint?: string;
  fields: Record<string, { value: unknown; officialField?: string | null }>;
  links: PrcFormEditContextLink[];
  linksComplete?: boolean;
};

export type PrcFormDataProvider = {
  fetchReferenceData(signal?: AbortSignal): Promise<PrcReferenceData>;
  fetchCatalog: PrcCatalogFetcher;
  searchSuppliers: PrcSupplierSearchFn;
  fetchEditContext(officialCode: string): Promise<PrcFormEditContext>;
  submitIntake(
    body: PrcIntakeBody,
    idempotencyKey: string,
  ): Promise<{ requestId: string }>;
  uploadAttachment(requestId: string, file: File): Promise<unknown>;
  /** PRC-REF-023-EDIT-POLICY-FIX-08 — salva a ficha do próprio caso em
   * ``submitted`` (CAS + idempotência, mesmo requestId). */
  saveDraft?(
    requestId: string,
    expectedVersion: number,
    changes: Array<{
      path: string;
      proposedValue: unknown;
      reason: string;
    }>,
    idempotencyKey: string,
  ): Promise<unknown>;
};

/** Entrada do modo de edição pré-atendimento: o caso já existe na
 * Engineering API e o formulário edita o mesmo requestId. */
export type PrcCaseEditInput = {
  requestId: string;
  expectedVersion: number;
  requestType: "create" | "update";
  /** technicalDraft completo do caso (campos + suppliers +
   * supplierLinkChanges). */
  draft: Record<string, unknown>;
  /** Razões registradas no draft (changedPaths) — preenche os campos
   * de justificativa já existentes. */
  changedPaths?: Array<{ path: string; reason?: string }>;
};

export type PrcRequestFormProps = {
  /** Origem canônica registrada no intake ("portal-engineering" |
   * "my-requests") — deve constar da allowlist do reference-data. */
  source: string;
  dataProvider: PrcFormDataProvider;
  onCancel: () => void;
  onCompleted: (requestId: string) => void;
  /** Escopo do portal host para overlays (lookup SA2 / preview). */
  portalScopeClassName?: string;
  /** FIX-08 — edição livre do caso enviado (``submitted``) pelo
   * criador. Sem identify step; salva via PATCH de draft no mesmo
   * requestId. Autorização/estado/versão são decididos no backend. */
  editCase?: PrcCaseEditInput;
};

/* ---------------- constantes e helpers de cópia -------------------- */

const STEPS = [
  { id: "identify", label: "Identificação" },
  { id: "sheet", label: "Ficha técnica" },
  { id: "review", label: "Revisar e enviar" },
];

// Agrupamento canônico (``PRC_FIELD_GROUPS``) sem o código oficial —
// informado na etapa de identificação/conclusão, não na ficha.
const FIELD_GROUPS = PRC_FIELD_GROUPS.map((g) => ({
  title: g.title,
  paths: g.paths.filter((p) => p !== "officialProductCode"),
}));

const CATALOG_UNAVAILABLE =
  "Não foi possível consultar as opções oficiais no TOTVS. Tente novamente.";

const LEGACY_NOTE_RE = /\b(B1_|A5_|legado|legado\s*['"]|cta_contabil)\b/i;

/** Help funcional do path — nota técnica/legado nunca vaza na UI. */
function fieldHelp(path: string, fallbackNote?: string | null) {
  const head = path.split(".")[0];
  const fromCatalog = PRC_FIELD_HELP[head] || PRC_FIELD_HELP[path];
  if (fromCatalog) return fromCatalog;
  const note = (fallbackNote || "").trim();
  if (!note || LEGACY_NOTE_RE.test(note)) return undefined;
  return note;
}

/** Assinatura canônica da lista de vínculos — detecção de mudança na
 * edição de caso CREATE (linhas candidatas, sem diff de ops). */
function supplierListSignature(
  rows: ReturnType<typeof supplierRowsToPayload>,
): string {
  return rows
    .map(
      (r) =>
        `${r.supplierCode}|${r.store}|${r.supplierName}|` +
        `${r.partNumber}|${r.catalogNumber ?? ""}`,
    )
    .sort()
    .join("\n");
}

function newIdemKey(): string {
  const uuid =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `prc-intake-${uuid}`;
}

/* ---------------- formulário compartilhado ------------------------- */

export function PrcRequestForm({
  source,
  dataProvider,
  onCancel,
  onCompleted,
  portalScopeClassName,
  editCase,
}: PrcRequestFormProps) {
  const [refData, setRefData] = useState<PrcReferenceData | null>(null);
  /* Store estável por instância — fetcher injetado pelo MFE; estado dos
   * catálogos vive fora do React state (useSyncExternalStore). */
  const [catalogStore] = useState(
    () => new PrcCatalogStore(dataProvider.fetchCatalog),
  );
  const catalogViews = useSyncExternalStore(
    catalogStore.subscribe,
    catalogStore.getSnapshot,
  );
  const [loadError, setLoadError] = useState("");
  const [step, setStep] = useState(0);

  /* FIX-08 — `editCase`: edição livre do caso ``submitted`` no mesmo
   * requestId. O wizard pula a etapa de identificação, semeia a ficha
   * do technicalDraft oficial e difunde contra o próprio draft (o
   * baseline do diff é o caso, não o TOTVS). */
  const steps = useMemo(
    () =>
      editCase ? STEPS.filter((s) => s.id !== "identify") : STEPS,
    [editCase],
  );
  const stepId = steps[step]?.id;

  const [requestType, setRequestType] = useState<"create" | "update">(
    () => editCase?.requestType || "create",
  );
  const [officialCode, setOfficialCode] = useState(() =>
    editCase?.requestType === "update"
      ? String(editCase.draft?.officialProductCode || "")
      : "",
  );

  const [values, setValues] = useState<Record<string, string>>(() => {
    if (!editCase) return {};
    const out: Record<string, string> = {};
    for (const [k, v] of Object.entries(editCase.draft || {})) {
      if (
        k === "suppliers" ||
        k === "supplierLinkChanges" ||
        k === "officialProductCode"
      ) {
        continue;
      }
      out[k] = v === null || v === undefined ? "" : String(v);
    }
    return out;
  });
  const [suppliers, setSuppliers] = useState<SupplierRow[]>(() => {
    if (!editCase) return [];
    const draft = editCase.draft || {};
    if (editCase.requestType === "update") {
      /* Caso UPDATE: technical_data.suppliers é a base oficial e os
       * vínculos pedidos vivem em supplierLinkChanges — o formulário
       * exibe o estado-alvo materializado (linhas tratadas como
       * baseline do diff, mesma semântica dos vínculos oficiais). */
      return applySupplierLinkOps(
        draft.suppliers,
        draft.supplierLinkChanges,
      ).map((l) =>
        officialSupplierRow({
          supplierCode: String(l.supplierCode || ""),
          store: String(l.store || ""),
          supplierName: String(l.supplierName || ""),
          supplierShortName:
            l.supplierShortName == null
              ? ""
              : String(l.supplierShortName),
          partNumber:
            l.partNumber == null ? "" : String(l.partNumber),
          catalogNumber:
            l.catalogNumber == null ? "" : String(l.catalogNumber),
        }),
      );
    }
    return toSupplierRows(draft.suppliers);
  });
  const [reasons, setReasons] = useState<Record<string, string>>(() => {
    if (!editCase?.changedPaths) return {};
    const out: Record<string, string> = {};
    for (const c of editCase.changedPaths) {
      if (c?.path && c.reason) out[c.path] = c.reason;
    }
    return out;
  });
  const [editCtx, setEditCtx] = useState<PrcFormEditContext | null>(
    () => {
      if (!editCase || editCase.requestType !== "update") return null;
      const draft = editCase.draft || {};
      const fields: PrcFormEditContext["fields"] = {};
      for (const [k, v] of Object.entries(draft)) {
        if (k === "suppliers" || k === "supplierLinkChanges") continue;
        fields[k] = { value: v };
      }
      return {
        status: "available",
        officialCode: String(draft.officialProductCode || ""),
        fields,
        links: applySupplierLinkOps(
          draft.suppliers,
          draft.supplierLinkChanges,
        ).map((l) => ({
          supplierCode: String(l.supplierCode || ""),
          store: String(l.store || ""),
          supplierName: String(l.supplierName || ""),
          supplierShortName:
            l.supplierShortName == null
              ? ""
              : String(l.supplierShortName),
          partNumber:
            l.partNumber == null ? "" : String(l.partNumber),
          catalogNumber:
            l.catalogNumber == null ? "" : String(l.catalogNumber),
        })),
        linksComplete: true,
      };
    },
  );
  const [editCtxState, setEditCtxState] = useState<
    "idle" | "loading" | "error" | "not_found"
  >("idle");
  /* Remoção oficial marcada por `rowId` (nunca pela chave SA5, que pode
   * coincidir com uma candidata duplicada). */
  const [removeMarks, setRemoveMarks] = useState<Set<string>>(new Set());

  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [supplierErrorsVisible, setSupplierErrorsVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const idemKey = useRef(newIdemKey());

  useEffect(() => {
    const controller = new AbortController();
    dataProvider
      .fetchReferenceData(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setRefData(data);
      })
      .catch((e) => {
        if (!controller.signal.aborted) {
          setLoadError(
            (e as Error).message ||
              "Falha ao carregar os dados de referência.",
          );
        }
      });
    /* Catálogos TOTVS — idle → loading → success|empty|error; requests
     * obsoletas são abortadas e nunca gravam estado. */
    catalogStore.loadAll(Object.keys(PRC_CATALOG_KINDS), controller.signal);
    return () => {
      controller.abort();
      catalogStore.abortAll();
    };
  }, [catalogStore, dataProvider]);

  const specByPath = useMemo(
    () => new Map((refData?.fields || []).map((s) => [s.path, s] as const)),
    [refData],
  );

  const sourceAllowed = useMemo(() => {
    if (!refData) return true; // ainda carregando — o backend decide
    return refData.sources.includes(source);
  }, [refData, source]);

  const setValue = (path: string, v: string) =>
    setValues((s) => ({ ...s, [path]: v }));

  const baselineFields: Record<string, unknown> = {};
  if (editCase && !editCtx) {
    /* Edição de caso CREATE: o baseline do diff é o próprio draft. */
    for (const [k, v] of Object.entries(editCase.draft || {})) {
      if (k === "suppliers" || k === "supplierLinkChanges") continue;
      baselineFields[k] = v;
    }
  } else {
    Object.entries(editCtx?.fields || {}).forEach(([p, f]) => {
      baselineFields[p] = f?.value;
    });
  }
  const hasBaseline = Boolean(editCtx) || Boolean(editCase);
  const scalarPaths = (refData?.fields || [])
    .filter(
      (spec) =>
        spec.kind !== "suppliers" && spec.path !== "officialProductCode",
    )
    .map((spec) => spec.path);
  const scalarDiff = hasBaseline
    ? computeScalarDiff(baselineFields, values, scalarPaths)
    : [];
  const changedPaths = new Set(scalarDiff.map((c) => c.path));
  /* PrcOfficialLink usa `undefined` (não `null`) — normalizamos os
   * vínculos do contexto na fronteira do diff. */
  const officialLinks = useMemo(
    () =>
      (editCtx?.links || []).map((l) => ({
        supplierCode: l.supplierCode,
        store: l.store,
        supplierName: l.supplierName,
        partNumber: l.partNumber ?? undefined,
        catalogNumber: l.catalogNumber ?? undefined,
      })),
    [editCtx],
  );
  const linkOps =
    requestType === "update" && editCtx
      ? computeLinkDiff(officialLinks, suppliers, removeMarks)
      : [];

  /* Caso CREATE em edição: fornecedores são candidatos (origin draft)
   * — a mudança é detectada comparando o payload com o draft inicial. */
  const initialSupplierSig = useMemo(() => {
    if (!editCase || editCase.requestType !== "create") return "";
    return supplierListSignature(
      supplierRowsToPayload(toSupplierRows(editCase.draft?.suppliers)),
    );
  }, [editCase]);
  const suppliersChanged = editCase
    ? editCase.requestType === "update"
      ? linkOps.length > 0
      : supplierListSignature(supplierRowsToPayload(suppliers)) !==
        initialSupplierSig
    : false;

  const validateStep = (id: string): string => {
    if (id === "identify") {
      if (requestType === "update") {
        if (!officialCode.trim())
          return "Informe o código oficial do produto a alterar.";
      }
      return "";
    }
    if (id === "sheet") {
      if (requestType === "create") {
        for (const spec of refData?.fields || []) {
          if (!spec.requiredCreateIntake) continue;
          if (spec.kind === "suppliers") continue;
          const v = (values[spec.path] || "").trim();
          if (!v && spec.kind !== "text") {
            return `Preencha «${PRC_FIELD_LABELS[spec.path] || spec.path}».`;
          }
        }
        // CORRECTION-10 — CREATE exige ≥1 vínculo: lista vazia não
        // satisfaz requiredCreateIntake (o backend rejeita também).
        if (!suppliers.length) {
          const msg =
            "Adicione ao menos um fornecedor oficial (código + loja + Part Number).";
          setFieldErrors((s) => ({ ...s, suppliers: msg }));
          setSupplierErrorsVisible(true);
          return msg;
        }
      }
      if (
        (requestType === "update" || editCase) &&
        !scalarDiff.length &&
        !linkOps.length &&
        !suppliersChanged
      ) {
        return "Nenhuma alteração identificada — edite um campo, vínculo ou adicione um fornecedor.";
      }
      const bad = suppliers.findIndex(
        (r) =>
          !r.supplierCode.trim() ||
          !r.store.trim() ||
          !r.supplierName.trim(),
      );
      if (bad >= 0) {
        return `Fornecedor ${bad + 1}: ${PRC_SUPPLIER_TEXT.selectRequired}`;
      }
      const missingPn = suppliers.findIndex((r) => !r.partNumber.trim());
      if (missingPn >= 0) {
        setSupplierErrorsVisible(true);
        return `Fornecedor ${missingPn + 1}: ${PRC_SUPPLIER_TEXT.partNumberRequired}`;
      }
      if (duplicateDraftRowIds(suppliers).size > 0) {
        return PRC_SUPPLIER_TEXT.duplicateExisting;
      }
      if (requestType === "update" && editCtx) {
        const detailed = computeLinkDiffDetailed(
          officialLinks,
          suppliers,
          removeMarks,
        );
        if (detailed.ambiguousOfficialKeys.length) {
          return "Há vínculos oficiais ambíguos para a mesma chave — operação bloqueada.";
        }
        if (detailed.conflictingKeys.length) {
          return PRC_SUPPLIER_TEXT.duplicateExisting;
        }
      }
      return "";
    }
    return "";
  };

  const next = () => {
    if (editCtxState === "loading") return;
    const msg = validateStep(stepId || "");
    if (msg) {
      setError(msg);
      return;
    }
    setError("");
    if (!editCase && requestType === "update" && stepId === "identify") {
      setEditCtxState("loading");
      dataProvider
        .fetchEditContext(officialCode.trim())
        .then((d) => {
          if (d.status && d.status !== "available") {
            setEditCtx(null);
            setEditCtxState(
              d.status === "not_found" ? "not_found" : "error",
            );
            return;
          }
          setEditCtx(d);
          setEditCtxState("idle");
          /* Working copy semeada do baseline oficial: o usuário edita
           * os valores reais e o diff é automático. */
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
    setStep((s) => Math.min(s + 1, steps.length - 1));
  };

  const back = () => {
    setError("");
    setStep((s) => Math.max(0, s - 1));
  };

  /* Mutações por `rowId` (nunca índice). */
  const patchSupplierRow = (rowId: string, patch: Partial<SupplierRow>) =>
    setSuppliers((rows) =>
      rows.map((r) => (r.rowId === rowId ? { ...r, ...patch } : r)),
    );

  const toggleRowSearch = (rowId: string) =>
    setSuppliers((rows) =>
      rows.map((r) => ({
        ...r,
        searchOpen: r.rowId === rowId ? !r.searchOpen : false,
        selectionError: r.rowId === rowId ? undefined : r.selectionError,
      })),
    );

  const closeRowSearch = (rowId: string) =>
    patchSupplierRow(rowId, { searchOpen: false });

  const toggleSupplierReason = (
    rowId: string,
    flag: "pnReasonOpen" | "catReasonOpen" | "opReasonOpen",
  ) =>
    setSuppliers((rows) =>
      rows.map((r) => (r.rowId === rowId ? { ...r, [flag]: !r[flag] } : r)),
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

  const markOfficialRemove = (rowId: string) =>
    setRemoveMarks((prev) => new Set(prev).add(rowId));

  const undoOfficialRemove = (rowId: string) =>
    setRemoveMarks((prev) => {
      const next = new Set(prev);
      next.delete(rowId);
      return next;
    });

  const addSupplierRow = () =>
    setSuppliers((rows) => [
      ...rows.map((r) => ({ ...r, searchOpen: false })),
      emptySupplierRow(),
    ]);

  const buildBody = (): PrcIntakeBody =>
    requestType === "create"
      ? buildCreateIntakeBody({
          source,
          refData,
          values,
          reasons,
          suppliers,
        })
      : buildUpdateIntakeBody({
          source,
          refData,
          officialCode,
          scalarDiff,
          linkOps,
          reasons,
          suppliers,
          baselineFingerprint: editCtx?.fingerprint || null,
          editContextReadAt: editCtx?.readAt || null,
        });

  /* Documentos opcionais: criado o caso (requestId real), cada arquivo
   * é enviado; falhas não derrubam a solicitação e ficam retentáveis
   * com o mesmo caseId — retry só reenvia os não confirmados. */
  const [supportFiles, setSupportFiles] = useState<PrcSupportFile[]>([]);
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({});
  const [uploadedIds, setUploadedIds] = useState<Set<string>>(new Set());
  const [createdRequestId, setCreatedRequestId] = useState<string | null>(
    null,
  );
  const [uploadSummary, setUploadSummary] = useState<string>("");
  const [previewFile, setPreviewFile] = useState<File | null>(null);

  const uploadSupportFiles = useCallback(
    async (requestId: string, files: PrcSupportFile[]) => {
      const failures: Record<string, string> = {};
      let ok = 0;
      for (const entry of files) {
        if (uploadedIds.has(entry.localId)) {
          ok += 1;
          continue;
        }
        try {
          await dataProvider.uploadAttachment(requestId, entry.file);
          ok += 1;
          setUploadedIds((prev) => new Set(prev).add(entry.localId));
        } catch (e) {
          failures[entry.localId] =
            (e as Error).message || "Falha no upload.";
        }
      }
      return { ok, failures };
    },
    [dataProvider, uploadedIds],
  );

  const submit = async () => {
    if (busy) return;
    setBusy(true);
    setError("");
    setFieldErrors({});
    setUploadSummary("");
    try {
      let rid: string;
      if (editCase) {
        /* FIX-08 — salva o mesmo caso via PATCH /draft (CAS +
         * idempotência). Fornecedores vão como lista final desejada;
         * a API deriva supplierLinkChanges em casos UPDATE. */
        const draftChanges = [
          ...scalarDiff.map((c) => ({
            path: c.path,
            proposedValue: c.after,
            reason: (reasons[c.path] || "").trim(),
          })),
          ...(suppliersChanged
            ? [
                {
                  path: "suppliers",
                  proposedValue: supplierRowsToPayload(suppliers),
                  reason: suppliers
                    .map((r) => r.opReason || "")
                    .filter(Boolean)
                    .join("; ")
                    .slice(0, 240),
                },
              ]
            : []),
        ];
        if (!draftChanges.length) {
          setError(
            "Nenhuma alteração identificada — edite um campo, " +
              "vínculo ou adicione um fornecedor.",
          );
          return;
        }
        if (!dataProvider.saveDraft) {
          setError(
            "Edição de solicitação não está disponível neste portal.",
          );
          return;
        }
        await dataProvider.saveDraft(
          editCase.requestId,
          editCase.expectedVersion,
          draftChanges,
          idemKey.current,
        );
        rid = editCase.requestId;
      } else {
        const env = createdRequestId
          ? null
          : await dataProvider.submitIntake(buildBody(), idemKey.current);
        rid = createdRequestId || env!.requestId;
        if (!createdRequestId) setCreatedRequestId(rid);
      }
      if (supportFiles.length) {
        const { ok, failures } = await uploadSupportFiles(rid, supportFiles);
        if (Object.keys(failures).length) {
          setFileErrors(failures);
          setUploadSummary(
            `${editCase ? "Alterações salvas" : "Solicitação criada"}. ` +
              `${ok} documento(s) anexado(s); ` +
              `${Object.keys(failures).length} falha(ram) — corrija e ` +
              "tente novamente sem recriar a solicitação.",
          );
          return;
        }
      }
      onCompleted(rid);
    } catch (e) {
      const err = e as Error & { fields?: Record<string, string> };
      if (err.fields) setFieldErrors(err.fields);
      setError(err.message || "Falha ao enviar a solicitação.");
      /* Chave mantida — retry do usuário é replay seguro no backend. */
    } finally {
      setBusy(false);
    }
  };

  /* Miniaturas locais: object URL só para imagens; revogadas na
   * remoção/substituição/desmontagem. */
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
    const view: PrcCatalogView = catalogViews.get(path) ?? {
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
          : fieldHelp(path, spec?.note) || "Catálogo oficial TOTVS";
    return (
      <>
        <PrcSelectField
          id={`prc-new-${path}`}
          label={label}
          hint={hint}
          searchable
          value={selected}
          onChange={(v) => setValue(path, v)}
          options={options}
          placeholder={loading ? "Carregando catálogo…" : "Selecionar…"}
          required={
            requestType === "create" && Boolean(spec?.requiredCreateIntake)
          }
          disabled={
            busy ||
            loading ||
            view.status === "empty" ||
            (view.status === "error" && !options.length)
          }
        />
        {view.status === "error" ? (
          <div className="delpi-prc__catalog-error">
            <p className="delpi-prc__field-error" role="alert">
              {selected
                ? `${CATALOG_UNAVAILABLE} O valor selecionado foi preservado, mas ainda não foi revalidado.`
                : CATALOG_UNAVAILABLE}
            </p>
            <ActionButton
              variant="ghost"
              disabled={busy}
              onClick={() => catalogStore.retry(path)}
            >
              Tentar novamente
            </ActionButton>
          </div>
        ) : null}
        {view.hasMore ? (
          <p className="delpi-prc__muted">
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
    const changed = hasBaseline && changedPaths.has(path);
    const baseline = baselineFields[path];
    /* Justificativa só quando há alteração efetiva: UPDATE/edição de
     * caso usam o diff contra o baseline; CREATE novo conta o
     * preenchimento como alteração. */
    const reasonVisible =
      (hasBaseline && changed) ||
      (!hasBaseline &&
        requestType === "create" &&
        (values[path] || "").trim() !== "");
    return (
      <div
        key={path}
        className={`delpi-prc__edit-row${
          changed ? " delpi-prc__edit-row--changed" : ""
        }`}
      >
        {changed ? (
          <div className="delpi-prc__diff-badge">
            <span className="delpi-prc__diff-tag">Alterado</span>
            <span className="delpi-prc__muted">
              {editCase
                ? "Anterior na solicitação"
                : "Anterior no TOTVS"}
              : <strong>{String(baseline ?? "") || "vazio"}</strong>
            </span>
            <button
              type="button"
              className="delpi-prc__lookup-clear"
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
        <div className="delpi-prc__edit-controls">
          {PRC_CATALOG_KINDS[path] ? (
            renderCatalogField(path, spec, label)
          ) : spec?.enumValues?.length ? (
            <PrcSelectField
              id={`prc-new-${path}`}
              label={label}
              hint={fieldHelp(path, spec.note)}
              searchable
              value={values[path] || ""}
              onChange={(v) => setValue(path, v)}
              options={enumOptions(path, spec.enumValues)}
              placeholder="Selecionar…"
              required={
                requestType === "create" &&
                Boolean(spec.requiredCreateIntake)
              }
              disabled={busy}
            />
          ) : (
            <PrcTextField
              id={`prc-new-${path}`}
              label={label}
              hint={fieldHelp(path, spec?.note)}
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
            <p className="delpi-prc__field-error" role="alert">
              {fieldErrors[path]}
            </p>
          ) : null}
          {reasonVisible ? (
            <PrcReasonField
              id={`prc-new-reason-${path}`}
              value={reasons[path] || ""}
              onChange={(v) => setReasons((s) => ({ ...s, [path]: v }))}
              disabled={busy}
            />
          ) : null}
        </div>
      </div>
    );
  };

  const reviewItems =
    requestType === "create" && !editCase
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
      <div className="delpi-prc">
        <PrcStateBanner variant="error">{loadError}</PrcStateBanner>
        <ActionButton variant="primary" onClick={onCancel}>
          Voltar
        </ActionButton>
      </div>
    );
  }

  if (!refData) {
    return (
      <div className="delpi-prc">
        <PrcLoadingCard
          title="Preparando formulário"
          description="Carregando o catálogo de campos da Engineering API."
        />
      </div>
    );
  }

  return (
    <div className="delpi-prc">
      <PrcProgressTracker
        steps={steps.map((s, i) => ({
          id: s.id,
          label: s.label,
          state: i < step ? "complete" : i === step ? "current" : "available",
        }))}
        currentStepId={steps[step].id}
        interactive
        onStepChange={(id) => {
          const target = steps.findIndex((s) => s.id === id);
          if (target <= step) {
            setError("");
            setStep(target);
          }
        }}
        ariaLabel={
          editCase
            ? "Etapas da edição da solicitação"
            : "Etapas da nova solicitação"
        }
      />

      {!sourceAllowed ? (
        <PrcStateBanner variant="error">
          A origem «{source}» não está autorizada pela Engineering API.
          Contate o administrador da plataforma.
        </PrcStateBanner>
      ) : null}

      {stepId === "identify" ? (
        <PrcSectionCard
          title="O que precisa ser feito?"
          subtitle="Escolha o tipo de solicitação"
        >
          <PrcSegmentToggle
            ariaLabel="Tipo de solicitação"
            value={requestType}
            onChange={(v) => {
              setRequestType(v);
              setEditCtx(null);
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
            <div className="delpi-prc__edit-controls">
              <PrcTextField
                id="prc-new-official-code"
                label="Código oficial TOTVS"
                hint={
                  fieldHelp("officialProductCode") ||
                  "Código atribuído ao produto no TOTVS. Preserve zeros à esquerda."
                }
                value={officialCode}
                onChange={setOfficialCode}
                required
                disabled={busy}
              />
              <p className="delpi-prc__muted">
                A revisão técnica de referência é identificada
                automaticamente pela Engineering API — não é preciso
                informá-la.
              </p>
              {editCtxState === "loading" ? (
                <p className="delpi-prc__muted">
                  Consultando cadastro oficial…
                </p>
              ) : null}
              {editCtxState === "not_found" ? (
                <p className="delpi-prc__field-error" role="alert">
                  Cadastro oficial não encontrado para o código informado.
                </p>
              ) : null}
              {editCtxState === "error" ? (
                <p className="delpi-prc__field-error" role="alert">
                  Falha ao consultar o cadastro oficial — tente novamente.
                </p>
              ) : null}
            </div>
          ) : null}
        </PrcSectionCard>
      ) : null}

      {stepId === "sheet" ? (
        <>
          {FIELD_GROUPS.map((group) => (
            <PrcSectionCard key={group.title} title={group.title}>
              <div className="delpi-prc__form-grid">
                {group.paths.map((path) => (
                  <div
                    key={path}
                    className={
                      path === "description" || path === "officialProductCode"
                        ? "delpi-prc__form-grid--wide"
                        : ""
                    }
                  >
                    {renderSheetField(path)}
                  </div>
                ))}
              </div>
            </PrcSectionCard>
          ))}

          <PrcSectionCard
            title="Fornecedores"
            subtitle="Código + loja + nome + Part Number obrigatórios; Catálogo opcional"
            actions={
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={addSupplierRow}
              >
                <Plus size={15} aria-hidden /> Adicionar fornecedor
              </ActionButton>
            }
          >
            {requestType === "update" && editCtxState === "loading" ? (
              <p className="delpi-prc__muted">
                Consultando vínculos oficiais…
              </p>
            ) : null}
            {editCtx && editCtx.linksComplete === false ? (
              <p className="delpi-prc__field-error" role="alert">
                A lista de vínculos pode estar incompleta — revise antes
                de propor alterações.
              </p>
            ) : null}
            {fieldErrors.suppliers ? (
              <p className="delpi-prc__field-error" role="alert">
                {fieldErrors.suppliers}
              </p>
            ) : null}
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
                searchSuppliers={dataProvider.searchSuppliers}
                portalScopeClassName={portalScopeClassName}
                onPatchRow={patchSupplierRow}
                onToggleSearch={toggleRowSearch}
                onCloseSearch={closeRowSearch}
                onToggleReason={toggleSupplierReason}
                onSetReason={setSupplierReason}
                onDiscardDraft={discardDraftRow}
                onMarkRemove={markOfficialRemove}
                onUndoRemove={undoOfficialRemove}
              />
            ) : (
              <p className="delpi-prc__muted">
                {requestType === "create"
                  ? "Nenhum fornecedor adicionado — o cadastro de matéria-prima exige ao menos um fornecedor oficial válido."
                  : "Nenhum fornecedor adicionado."}
              </p>
            )}
          </PrcSectionCard>
        </>
      ) : null}

      {stepId === "sheet" ? (
        <PrcSectionCard
          title="Documentos de apoio (opcional)"
          subtitle={`Até ${PRC_ATTACHMENT_MAX_MB} MB por arquivo · máx. ${PRC_ATTACHMENT_MAX_COUNT} arquivos`}
        >
          <PrcFileDropzone
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
              <p className="delpi-prc__muted">
                Arquivos selecionados (ainda não enviados)
              </p>
              <PrcAttachmentStrip
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
            <PrcStateBanner variant="error">{uploadSummary}</PrcStateBanner>
          ) : null}
          {createdRequestId && uploadSummary ? (
            <ActionButton
              variant="primary"
              disabled={busy}
              onClick={() => void submit()}
            >
              Tentar enviar documentos novamente
            </ActionButton>
          ) : null}
          <FilePreviewModal
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
                <ActionButton
                  variant="ghost"
                  onClick={() => previewFile && downloadLocalFile(previewFile)}
                >
                  Baixar
                </ActionButton>
              ) : null
            }
            portalScopeClassName={portalScopeClassName}
            onClose={() => setPreviewFile(null)}
          />
        </PrcSectionCard>
      ) : null}

      {stepId === "review" ? (
        <PrcDetailCard
          title="Resumo da solicitação"
          hint={
            editCase
              ? "Confira as alterações antes de salvar no mesmo chamado."
              : "Confira os dados antes de enviar à Engenharia."
          }
        >
          <PrcDetailFieldGrid
            fields={[
              {
                label: "Tipo",
                value: editCase
                  ? "Edição da solicitação enviada"
                  : requestType === "create"
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
                              if (o.operation === "add") return `+ ${k}`;
                              if (o.operation === "remove")
                                return `− ${k} (remoção solicitada)`;
                              const parts = Object.keys(o.fields).join("+");
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
              {
                label: "Documentos",
                value: supportFiles.length
                  ? `${supportFiles.length} arquivo(s) selecionado(s)`
                  : "Nenhum documento anexado",
              },
            ]}
          />
          {Object.keys(fieldErrors).length ? (
            <PrcStateBanner variant="error">
              {Object.entries(fieldErrors)
                .map(([k, v]) => `${PRC_FIELD_LABELS[k] || k}: ${v}`)
                .join(" · ")}
            </PrcStateBanner>
          ) : null}
        </PrcDetailCard>
      ) : null}

      {error ? <PrcStateBanner variant="error">{error}</PrcStateBanner> : null}

      <PrcFormActions align="end">
        <ActionButton variant="ghost" softDisabled={busy} onClick={onCancel}>
          Cancelar
        </ActionButton>
        {step > 0 ? (
          <ActionButton variant="default" softDisabled={busy} onClick={back}>
            Voltar
          </ActionButton>
        ) : null}
        {step < steps.length - 1 ? (
          <ActionButton variant="primary" onClick={next}>
            Avançar
          </ActionButton>
        ) : (
          <ActionButton
            variant="primary"
            softDisabled={busy || !sourceAllowed}
            onClick={submit}
          >
            {editCase ? "Salvar alterações" : "Enviar solicitação"}
          </ActionButton>
        )}
      </PrcFormActions>
    </div>
  );
}
