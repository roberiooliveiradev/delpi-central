/** PRC-REF-023-F03/F04 — formulário completo do solicitante de
 * matéria-prima/produto em Minhas Solicitações, em wizard de 3 etapas
 * com paridade funcional ao PrcCreatePage do Portal Engenharia:
 * Identificação → Ficha técnica → Revisar e enviar.
 *
 * Mesmo contrato PRC da Engineering API (ficha completa, CREATE/UPDATE,
 * fornecedores SA2/SA5, documentos opcionais). A autoridade de
 * validação, workflow e identificador é sempre o backend; este
 * componente apenas monta o payload oficial e acompanha o upload.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  FilePreviewModal,
  addSupportFiles,
  buildCreateIntakeBody,
  buildUpdateIntakeBody,
  catalogOptions,
  computeLinkDiff,
  computeLinkDiffDetailed,
  computeScalarDiff,
  duplicateDraftRowIds,
  emptySupplierRow,
  enumOptions,
  officialSupplierRow,
  PRC_ATTACHMENT_ACCEPT,
  PRC_ATTACHMENT_MAX_COUNT,
  PRC_ATTACHMENT_MAX_MB,
  PRC_CATALOG_KINDS,
  PRC_FIELD_HELP,
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_LABELS,
  prcFormatSize,
  removeSupportFile,
  supplierHitMain,
  supplierHitSecondary,
  supplierOfficialKey,
  withSelectedOption,
  type PrcReferenceData,
  type PrcSupportFile,
  type SupplierRow,
} from "@delpi/plugin-ui/index";

import { AppShell } from "../../components/AppShell";
import {
  fetchPrcCatalog,
  fetchPrcEditContext,
  fetchPrcReferenceData,
  prcIntakeSubmit,
  searchPrcSuppliers,
  uploadPrcAttachment,
  type PrcEditContext,
  type PrcSupplierHit,
} from "./prcApi";
import {
  DetailFields,
  MyRequestsAttachmentPreviewStrip,
  MyRequestsFileDropzone,
  MyRequestsFormActions,
  MyRequestsLoadingState,
  MyRequestsProgressTracker,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SegmentToggle,
  SelectField,
  TextField,
} from "../../ui/mrUi";

const PRC_SOURCE = "my-requests";

const STEPS = [
  { id: "identify", label: "Identificação" },
  { id: "sheet", label: "Ficha técnica" },
  { id: "review", label: "Revisar e enviar" },
];

/** Agrupamento da ficha — paridade com o wizard do Portal Engenharia. */
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

type Props = {
  onCancel: () => void;
  onDone: (requestId: string) => void;
};

export function PrcRequestPage({ onCancel, onDone }: Props) {
  const [step, setStep] = useState(0);
  const [refData, setRefData] = useState<PrcReferenceData | null>(null);
  const [loadError, setLoadError] = useState("");
  const [requestType, setRequestType] = useState<"create" | "update">(
    "create",
  );
  const [officialCode, setOfficialCode] = useState("");
  const [editCtx, setEditCtx] = useState<PrcEditContext | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [suppliers, setSuppliers] = useState<SupplierRow[]>([]);
  const [removeMarks, setRemoveMarks] = useState<Set<string>>(new Set());
  const [catalogs, setCatalogs] = useState<
    Record<string, { code: string; label?: string | null }[]>
  >({});
  const [hits, setHits] = useState<Record<string, PrcSupplierHit[]>>({});
  const [supportFiles, setSupportFiles] = useState<PrcSupportFile[]>([]);
  const [uploadedIds, setUploadedIds] = useState<Set<string>>(new Set());
  const [fileErrors, setFileErrors] = useState<Record<string, string>>({});
  const [previewFile, setPreviewFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>(
    {},
  );
  const [createdRequestId, setCreatedRequestId] = useState<string | null>(
    null,
  );
  const [uploadSummary, setUploadSummary] = useState("");
  const idemKey = useRef(`mr-prc-${crypto.randomUUID()}`);

  const specsByPath = useMemo(() => {
    const map = new Map<string, PrcReferenceData["fields"][number]>();
    for (const s of refData?.fields || []) map.set(s.path, s);
    return map;
  }, [refData]);

  const scalarPaths = useMemo(
    () =>
      (refData?.fields || [])
        .filter(
          (s) => s.kind !== "suppliers" && s.path !== "officialProductCode",
        )
        .map((s) => s.path),
    [refData],
  );

  useEffect(() => {
    const ac = new AbortController();
    fetchPrcReferenceData(ac.signal)
      .then((data) => {
        setRefData(data);
        const kinds = new Set(
          data.fields
            .filter((s) => PRC_CATALOG_KINDS[s.path])
            .map((s) => PRC_CATALOG_KINDS[s.path]),
        );
        return Promise.all(
          [...kinds].map((kind) =>
            fetchPrcCatalog(kind, "", ac.signal).then(
              (items) => [kind, items] as const,
            ),
          ),
        ).then((entries) => setCatalogs(Object.fromEntries(entries)));
      })
      .catch((e: Error) => setLoadError(e.message));
    return () => ac.abort();
  }, []);

  const set = (path: string, v: string) =>
    setValues((s) => ({ ...s, [path]: v }));
  const patchRow = (rowId: string, patch: Partial<SupplierRow>) =>
    setSuppliers((rows) =>
      rows.map((r) => (r.rowId === rowId ? { ...r, ...patch } : r)),
    );

  const loadEditContext = (): Promise<boolean> => {
    const code = officialCode.trim();
    if (!code) return Promise.resolve(false);
    setBusy(true);
    setError("");
    return fetchPrcEditContext(code)
      .then((ctx) => {
        setEditCtx(ctx);
        const next: Record<string, string> = {};
        for (const [path, f] of Object.entries(ctx.fields || {})) {
          next[path] = f?.value == null ? "" : String(f.value);
        }
        setValues(next);
        setSuppliers(
          (ctx.links || []).map((l) =>
            officialSupplierRow({
              supplierCode: l.supplierCode,
              store: l.store,
              supplierName: l.supplierName,
              partNumber: l.partNumber ?? undefined,
              catalogNumber: l.catalogNumber ?? undefined,
            }),
          ),
        );
        setRemoveMarks(new Set());
        return true;
      })
      .catch((e: Error) => {
        setError(e.message || "Falha ao consultar o cadastro oficial.");
        return false;
      })
      .finally(() => setBusy(false));
  };

  const scalarDiff = useMemo(() => {
    if (requestType !== "update" || !editCtx) return [];
    const baseline: Record<string, unknown> = {};
    for (const [path, f] of Object.entries(editCtx.fields || {})) {
      baseline[path] = f?.value;
    }
    return computeScalarDiff(baseline, values, scalarPaths);
  }, [requestType, editCtx, values, scalarPaths]);

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

  const linkOps = useMemo(() => {
    if (requestType !== "update" || !editCtx) return [];
    return computeLinkDiff(officialLinks, suppliers, removeMarks);
  }, [requestType, editCtx, officialLinks, suppliers, removeMarks]);

  const validateStep = (index: number): string => {
    if (index === 0) {
      if (requestType === "update" && !officialCode.trim()) {
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
          if (!v) {
            return `Preencha «${PRC_FIELD_LABELS[spec.path] || spec.path}».`;
          }
        }
      } else if (!scalarDiff.length && !linkOps.length) {
        return "Nenhuma alteração identificada — edite um campo, vínculo ou adicione um fornecedor.";
      }
      const bad = suppliers.findIndex(
        (r) => !r.supplierCode.trim() || !r.store.trim(),
      );
      if (bad >= 0) {
        return `Fornecedor ${bad + 1}: escolha um fornecedor oficial na busca.`;
      }
      const missingPn = suppliers.findIndex((r) => !r.partNumber.trim());
      if (missingPn >= 0) {
        return `Fornecedor ${missingPn + 1}: Part Number é obrigatório para vincular.`;
      }
      if (duplicateDraftRowIds(suppliers).size > 0) {
        return "Há fornecedores duplicados (mesmo código e loja).";
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
          return "Há fornecedores duplicados (mesmo código e loja).";
        }
      }
      return "";
    }
    return "";
  };

  const next = () => {
    const msg = validateStep(step);
    if (msg) {
      setError(msg);
      return;
    }
    setError("");
    if (requestType === "update" && step === 0 && !editCtx) {
      void loadEditContext().then((ok) => {
        if (ok) setStep((s) => Math.min(s + 1, STEPS.length - 1));
      });
      return;
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const back = () => {
    setError("");
    setStep((s) => Math.max(0, s - 1));
  };

  const uploadSupportFiles = async (requestId: string) => {
    const failures: Record<string, string> = {};
    let ok = 0;
    for (const entry of supportFiles) {
      if (uploadedIds.has(entry.localId)) {
        ok += 1;
        continue;
      }
      try {
        await uploadPrcAttachment(requestId, entry.file);
        ok += 1;
        setUploadedIds((prev) => new Set(prev).add(entry.localId));
      } catch (e) {
        failures[entry.localId] =
          (e as Error).message || "Falha no upload.";
      }
    }
    return { ok, failures };
  };

  const submit = async () => {
    if (busy) return;
    const msg = validateStep(1);
    if (msg) {
      setError(msg);
      setStep(1);
      return;
    }
    setBusy(true);
    setError("");
    setUploadSummary("");
    try {
      const body =
        requestType === "create"
          ? buildCreateIntakeBody({
              source: PRC_SOURCE,
              refData,
              values,
              reasons,
              suppliers,
            })
          : buildUpdateIntakeBody({
              source: PRC_SOURCE,
              refData,
              officialCode,
              scalarDiff,
              linkOps,
              reasons,
              suppliers,
              baselineFingerprint: editCtx?.fingerprint || null,
              editContextReadAt: editCtx?.readAt || null,
            });
      const env = createdRequestId
        ? null
        : await prcIntakeSubmit(body, idemKey.current);
      const rid = createdRequestId || env!.requestId;
      if (!createdRequestId) setCreatedRequestId(rid);
      if (supportFiles.length) {
        const { ok, failures } = await uploadSupportFiles(rid);
        if (Object.keys(failures).length) {
          setFileErrors(failures);
          setUploadSummary(
            `Solicitação criada. ${ok} documento(s) anexado(s); ` +
              `${Object.keys(failures).length} falha(ram) — corrija e ` +
              "tente novamente sem recriar a solicitação.",
          );
          setStep(1);
          return;
        }
      }
      onDone(rid);
    } catch (e) {
      const err = e as Error & { fields?: Record<string, string> };
      if (err.fields) setFieldErrors(err.fields);
      setError(err.message || "Falha ao enviar a solicitação.");
    } finally {
      setBusy(false);
    }
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

  const searchSuppliers = async (row: SupplierRow) => {
    const q = row.query.trim();
    if (q.length < 2) return;
    try {
      const items = await searchPrcSuppliers(q);
      setHits((s) => ({ ...s, [row.rowId]: items }));
    } catch (e) {
      patchRow(row.rowId, {
        selectionError: (e as Error).message,
      });
    }
  };

  const pickSupplier = (row: SupplierRow, hit: PrcSupplierHit) => {
    const code = String(hit.supplier_code || "").trim();
    const store = String(hit.supplier_store || "").trim();
    const clash = suppliers.some(
      (r) =>
        r.rowId !== row.rowId &&
        supplierOfficialKey(r.supplierCode, r.store) ===
          supplierOfficialKey(code, store),
    );
    if (clash) {
      patchRow(row.rowId, {
        selectionError:
          "Esse fornecedor já está na lista (mesmo código e loja).",
      });
      return;
    }
    patchRow(row.rowId, {
      supplierCode: code,
      store,
      supplierName: supplierHitMain(hit),
      supplierShortName: String(hit.supplier_short_name || ""),
      selectionError: undefined,
    });
    setHits((s) => ({ ...s, [row.rowId]: [] }));
  };

  if (loadError) {
    return (
      <AppShell title="Matéria-prima / produto">
        <MyRequestsStateBanner variant="error">
          {loadError}
        </MyRequestsStateBanner>
        <MyRequestsFormActions>
          <ActionButton variant="ghost" onClick={onCancel}>
            Voltar
          </ActionButton>
        </MyRequestsFormActions>
      </AppShell>
    );
  }
  if (!refData) {
    return (
      <AppShell title="Matéria-prima / produto">
        <MyRequestsLoadingState message="Carregando formulário…" />
      </AppShell>
    );
  }

  const renderField = (path: string) => {
    const spec = specsByPath.get(path);
    if (!spec) return null;
    const label = PRC_FIELD_LABELS[path] || path;
    const hint = PRC_FIELD_HELP[path] || undefined;
    const required =
      requestType === "create" && spec.requiredCreateIntake;
    const errMsg = fieldErrors[path];
    if (spec.kind === "text") {
      return (
        <TextField
          key={path}
          label={required ? `${label} *` : label}
          hint={hint}
          value={values[path] || ""}
          onChange={(v) => set(path, v)}
        />
      );
    }
    const options =
      spec.kind === "enum"
        ? enumOptions(path, spec.enumValues || [])
        : catalogOptions(
            catalogs[PRC_CATALOG_KINDS[path] || ""] || [],
          );
    return (
      <div key={path}>
        <SelectField
          label={required ? `${label} *` : label}
          hint={hint}
          options={withSelectedOption(options, values[path] || "")}
          value={values[path] || ""}
          onChange={(v) => set(path, v)}
          searchable
        />
        {errMsg ? (
          <MyRequestsStateBanner variant="error">
            {errMsg}
          </MyRequestsStateBanner>
        ) : null}
        {requestType === "update" &&
        scalarDiff.some((c) => c.path === path) ? (
          <TextField
            label={`Justificativa — ${label}`}
            value={reasons[path] || ""}
            onChange={(v) =>
              setReasons((s) => ({ ...s, [path]: v }))
            }
          />
        ) : null}
      </div>
    );
  };

  const linkLabel = (op: {
    operation: string;
    key: { supplierCode: string; store: string };
  }) => `${op.key.supplierCode}/${op.key.store}`;

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
          value: `${change.before || "vazio"} → ${change.after || "vazio"}${
            reasons[change.path] ? ` — ${reasons[change.path]}` : ""
          }`,
        }));

  return (
    <AppShell title="Matéria-prima / produto">
      <MyRequestsProgressTracker
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
          if (target >= 0 && target <= step) setStep(target);
        }}
      />

      {step === 0 ? (
        <MyRequestsSectionCard
          title="Tipo da solicitação"
          hint="Criação de novo item ou alteração de cadastro existente."
        >
          <SegmentToggle
            ariaLabel="Tipo da solicitação"
            options={[
              {
                value: "create" as const,
                label: "Criação de matéria-prima",
              },
              { value: "update" as const, label: "Alteração de produto" },
            ]}
            value={requestType}
            onChange={(v) => {
              setRequestType(v);
              setEditCtx(null);
              setError("");
            }}
          />
          {requestType === "update" ? (
            <div
              style={{
                display: "flex",
                gap: 8,
                alignItems: "end",
                marginTop: 12,
              }}
            >
              <TextField
                label={`${PRC_FIELD_LABELS.officialProductCode} *`}
                hint={PRC_FIELD_HELP.officialProductCode}
                value={officialCode}
                onChange={setOfficialCode}
              />
              <ActionButton
                variant="default"
                disabled={busy || !officialCode.trim()}
                onClick={() => void loadEditContext()}
              >
                {editCtx ? "Recarregar cadastro" : "Carregar cadastro"}
              </ActionButton>
            </div>
          ) : null}
          {requestType === "update" && editCtx ? (
            <MyRequestsStateBanner variant="default">
              Cadastro oficial de {officialCode.trim()} carregado —
              avance para editar os campos desejados.
            </MyRequestsStateBanner>
          ) : null}
        </MyRequestsSectionCard>
      ) : null}

      {step === 1 ? (
        <>
          {FIELD_GROUPS.map((group) => (
            <MyRequestsSectionCard key={group.title} title={group.title}>
              {group.paths.map(renderField)}
            </MyRequestsSectionCard>
          ))}

          <MyRequestsSectionCard
            title={PRC_FIELD_LABELS.suppliers}
            hint={PRC_FIELD_HELP.suppliers}
          >
            {fieldErrors.suppliers ? (
              <MyRequestsStateBanner variant="error">
                {fieldErrors.suppliers}
              </MyRequestsStateBanner>
            ) : null}
            {suppliers.map((row) => {
              const marked = removeMarks.has(row.rowId);
              return (
                <div
                  key={row.rowId}
                  style={{
                    border: "1px solid var(--delpi-border, #d5dce4)",
                    borderRadius: 8,
                    padding: 12,
                    marginBottom: 8,
                    opacity: marked ? 0.55 : 1,
                  }}
                >
                  {row.supplierCode ? (
                    <div>
                      <strong>
                        {row.supplierCode}/{row.store} — {row.supplierName}
                      </strong>
                      {row.supplierShortName ? (
                        <span> ({row.supplierShortName})</span>
                      ) : null}
                    </div>
                  ) : (
                    <div>
                      <div
                        style={{
                          display: "flex",
                          gap: 8,
                          alignItems: "end",
                        }}
                      >
                        <TextField
                          label="Buscar fornecedor"
                          value={row.query}
                          onChange={(v) =>
                            patchRow(row.rowId, { query: v })
                          }
                          placeholder="Razão social, código ou loja"
                        />
                        <ActionButton
                          variant="default"
                          disabled={row.query.trim().length < 2}
                          onClick={() => void searchSuppliers(row)}
                        >
                          Buscar
                        </ActionButton>
                      </div>
                      {(hits[row.rowId] || []).map((hit) => (
                        <ActionButton
                          key={`${hit.supplier_code}|${hit.supplier_store}`}
                          variant="ghost"
                          onClick={() => pickSupplier(row, hit)}
                        >
                          {supplierHitMain(hit)} —{" "}
                          {supplierHitSecondary(hit)}
                        </ActionButton>
                      ))}
                      {row.selectionError ? (
                        <MyRequestsStateBanner variant="error">
                          {row.selectionError}
                        </MyRequestsStateBanner>
                      ) : null}
                    </div>
                  )}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: 8,
                      marginTop: 8,
                    }}
                  >
                    <TextField
                      label={`${PRC_SUPPLIER_LABELS.partNumber} *`}
                      value={row.partNumber}
                      onChange={(v) =>
                        patchRow(row.rowId, { partNumber: v })
                      }
                      disabled={marked}
                    />
                    <TextField
                      label={PRC_SUPPLIER_LABELS.catalogNumber}
                      value={row.catalogNumber}
                      onChange={(v) =>
                        patchRow(row.rowId, { catalogNumber: v })
                      }
                      disabled={marked}
                    />
                  </div>
                  {row.origin === "official" ? (
                    <>
                      <div
                        style={{
                          display: "grid",
                          gridTemplateColumns: "1fr 1fr",
                          gap: 8,
                          marginTop: 8,
                        }}
                      >
                        <TextField
                          label="Justificativa — Part Number"
                          value={row.pnReason || ""}
                          onChange={(v) =>
                            patchRow(row.rowId, { pnReason: v })
                          }
                        />
                        <TextField
                          label="Justificativa — Catálogo"
                          value={row.catReason || ""}
                          onChange={(v) =>
                            patchRow(row.rowId, { catReason: v })
                          }
                        />
                      </div>
                      <TextField
                        label="Justificativa da operação (opcional)"
                        value={row.opReason || ""}
                        onChange={(v) =>
                          patchRow(row.rowId, { opReason: v })
                        }
                      />
                    </>
                  ) : null}
                  <MyRequestsFormActions>
                    {row.origin === "official" ? (
                      <ActionButton
                        variant="ghost"
                        onClick={() =>
                          setRemoveMarks((s) => {
                            const next = new Set(s);
                            if (next.has(row.rowId)) next.delete(row.rowId);
                            else next.add(row.rowId);
                            return next;
                          })
                        }
                      >
                        {marked
                          ? "Desfazer remoção"
                          : "Solicitar remoção do vínculo"}
                      </ActionButton>
                    ) : (
                      <ActionButton
                        variant="ghost"
                        onClick={() =>
                          setSuppliers((rows) =>
                            rows.filter((r) => r.rowId !== row.rowId),
                          )
                        }
                      >
                        Remover
                      </ActionButton>
                    )}
                  </MyRequestsFormActions>
                </div>
              );
            })}
            <ActionButton
              variant="default"
              onClick={() =>
                setSuppliers((rows) => [...rows, emptySupplierRow()])
              }
            >
              Adicionar fornecedor
            </ActionButton>
            {requestType === "update" && linkOps.length ? (
              <p>
                Operações de vínculo:{" "}
                {linkOps
                  .map((o) =>
                    o.operation === "add"
                      ? `+ ${linkLabel(o)}`
                      : o.operation === "remove"
                        ? `− ${linkLabel(o)}`
                        : `~ ${linkLabel(o)}`,
                  )
                  .join(" · ")}
              </p>
            ) : null}
          </MyRequestsSectionCard>

          <MyRequestsSectionCard
            title="Documentos de apoio (opcional)"
            hint={`PDF ou imagens · até ${PRC_ATTACHMENT_MAX_MB} MB por arquivo · máx. ${PRC_ATTACHMENT_MAX_COUNT} arquivos`}
          >
            <MyRequestsFileDropzone
              disabled={busy}
              multiple
              accept={PRC_ATTACHMENT_ACCEPT}
              ariaLabel="Selecionar documentos de apoio"
              onFilesSelected={onPickSupportFiles}
              labels={{
                title: "Arraste arquivos ou clique para escolher",
                hint: `PDF ou imagens · até ${PRC_ATTACHMENT_MAX_MB} MB por arquivo`,
              }}
            />
            {supportFiles.length ? (
              <MyRequestsAttachmentPreviewStrip
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
            ) : null}
            {uploadSummary ? (
              <MyRequestsStateBanner variant="error">
                {uploadSummary}
              </MyRequestsStateBanner>
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
          </MyRequestsSectionCard>
        </>
      ) : null}

      {step === 2 ? (
        <MyRequestsSectionCard
          title="Resumo da solicitação"
          hint="Confira os dados antes de enviar à Engenharia."
        >
          <DetailFields
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
                              if (o.operation === "add") return `+ ${k}`;
                              if (o.operation === "remove")
                                return `− ${k} (remoção solicitada)`;
                              return `~ ${k}`;
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
            <MyRequestsStateBanner variant="error">
              {Object.entries(fieldErrors)
                .map(([k, v]) => `${PRC_FIELD_LABELS[k] || k}: ${v}`)
                .join(" · ")}
            </MyRequestsStateBanner>
          ) : null}
        </MyRequestsSectionCard>
      ) : null}

      {error ? (
        <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
      ) : null}

      <MyRequestsFormActions align="end">
        <ActionButton variant="ghost" disabled={busy} onClick={onCancel}>
          Cancelar
        </ActionButton>
        {step > 0 ? (
          <ActionButton variant="default" disabled={busy} onClick={back}>
            Voltar
          </ActionButton>
        ) : null}
        {step < STEPS.length - 1 ? (
          <ActionButton variant="primary" disabled={busy} onClick={next}>
            Avançar
          </ActionButton>
        ) : (
          <ActionButton
            variant="primary"
            disabled={busy}
            onClick={() => void submit()}
          >
            Enviar solicitação
          </ActionButton>
        )}
      </MyRequestsFormActions>

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
        onClose={() => setPreviewFile(null)}
      />
    </AppShell>
  );
}
