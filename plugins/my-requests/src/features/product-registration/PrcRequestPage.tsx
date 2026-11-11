/** PRC-REF-023-F03 — formulário completo do solicitante de
 * matéria-prima/produto em Minhas Solicitações.
 *
 * Mesmo contrato PRC da Engineering API (ficha completa, CREATE/UPDATE,
 * fornecedores, documentos opcionais). A autoridade de validação,
 * workflow e identificador é sempre o backend; este componente apenas
 * monta o payload oficial e acompanha o upload de documentos.
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
  MyRequestsAttachmentPreviewStrip,
  MyRequestsFileDropzone,
  MyRequestsFormActions,
  MyRequestsLoadingState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  SegmentToggle,
  SelectField,
  TextField,
} from "../../ui/mrUi";

const PRC_SOURCE = "my-requests";
const FIELD_ORDER = [
  "description",
  "group",
  "productKind",
  "unit",
  "defaultWarehouse",
  "accountingAccount",
  "thirdPartyProduct",
  "customerReference",
];

type Props = {
  onCancel: () => void;
  onDone: (requestId: string) => void;
};

export function PrcRequestPage({ onCancel, onDone }: Props) {
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

  const fieldSpecs = useMemo(() => {
    const specs = (refData?.fields || []).filter(
      (s) => s.kind !== "suppliers" && s.path !== "officialProductCode",
    );
    return [...specs].sort(
      (a, b) => FIELD_ORDER.indexOf(a.path) - FIELD_ORDER.indexOf(b.path),
    );
  }, [refData]);

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

  const loadEditContext = () => {
    const code = officialCode.trim();
    if (!code || busy) return;
    setBusy(true);
    setError("");
    fetchPrcEditContext(code)
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
      })
      .catch((e: Error) =>
        setError(e.message || "Falha ao consultar o cadastro oficial."),
      )
      .finally(() => setBusy(false));
  };

  const scalarDiff = useMemo(() => {
    if (requestType !== "update" || !editCtx) return [];
    const baseline: Record<string, unknown> = {};
    for (const [path, f] of Object.entries(editCtx.fields || {})) {
      baseline[path] = f?.value;
    }
    return computeScalarDiff(
      baseline,
      values,
      fieldSpecs.map((s) => s.path),
    );
  }, [requestType, editCtx, values, fieldSpecs]);

  const linkOps = useMemo(() => {
    if (requestType !== "update" || !editCtx) return [];
    const official = (editCtx.links || []).map((l) => ({
      supplierCode: l.supplierCode,
      store: l.store,
      supplierName: l.supplierName,
      partNumber: l.partNumber ?? undefined,
      catalogNumber: l.catalogNumber ?? undefined,
    }));
    return computeLinkDiff(official, suppliers, removeMarks);
  }, [requestType, editCtx, suppliers, removeMarks]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (requestType === "update" && !editCtx) {
      setError("Carregue o cadastro oficial antes de solicitar a alteração.");
      return false;
    }
    for (const spec of fieldSpecs) {
      const v = (values[spec.path] || "").trim();
      if (requestType === "create") {
        if (spec.requiredCreateIntake && !v) {
          errs[spec.path] = "Campo obrigatório.";
        }
      }
    }
    if (requestType === "update" && !scalarDiff.length && !linkOps.length) {
      setError("Nenhuma alteração identificada em relação ao cadastro.");
      return false;
    }
    const complete = suppliers.filter(
      (r) => r.supplierCode.trim() && r.store.trim(),
    );
    if (!suppliers.length) {
      errs.suppliers = "Informe ao menos um fornecedor.";
    } else if (
      suppliers.some(
        (r) =>
          (!r.supplierCode.trim() || !r.store.trim()) &&
          (r.query.trim() || r.partNumber.trim() || r.supplierName.trim()),
      )
    ) {
      errs.suppliers = "Há linha de fornecedor incompleta.";
    } else if (complete.some((r) => !r.partNumber.trim())) {
      errs.suppliers =
        "Part Number é obrigatório em todo vínculo de fornecedor.";
    } else if (duplicateDraftRowIds(suppliers).size) {
      errs.suppliers =
        "Há fornecedores duplicados (mesmo código e loja).";
    }
    setFieldErrors(errs);
    return !Object.keys(errs).length;
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
    if (busy || !validate()) return;
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

  const linkLabel = (op: { operation: string; key: { supplierCode: string; store: string } }) =>
    `${op.key.supplierCode}/${op.key.store}`;

  return (
    <AppShell title="Matéria-prima / produto">
      <MyRequestsSectionCard
        title="Tipo da solicitação"
        hint="Criação de novo item ou alteração de cadastro existente."
      >
        <SegmentToggle
          ariaLabel="Tipo da solicitação"
          options={[
            { value: "create" as const, label: "Criação de matéria-prima" },
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
          <div style={{ display: "flex", gap: 8, alignItems: "end", marginTop: 12 }}>
            <TextField
              label={`${PRC_FIELD_LABELS.officialProductCode} *`}
              hint={PRC_FIELD_HELP.officialProductCode}
              value={officialCode}
              onChange={setOfficialCode}
            />
            <ActionButton
              variant="default"
              disabled={busy || !officialCode.trim()}
              onClick={loadEditContext}
            >
              {editCtx ? "Recarregar cadastro" : "Carregar cadastro"}
            </ActionButton>
          </div>
        ) : null}
      </MyRequestsSectionCard>

      {requestType === "update" && !editCtx ? (
        <MyRequestsSectionCard title="Ficha técnica">
          <MyRequestsStateBanner variant="default">
            Informe o código oficial e carregue o cadastro para alterar
            os campos desejados.
          </MyRequestsStateBanner>
        </MyRequestsSectionCard>
      ) : (
        <>
          <MyRequestsSectionCard
            title="Ficha técnica"
            hint={
              requestType === "update"
                ? "Somente os campos alterados serão enviados à Engenharia."
                : "Dados do novo produto/matéria-prima."
            }
          >
            {fieldSpecs.map((spec) => {
              const label =
                PRC_FIELD_LABELS[spec.path] || spec.path;
              const hint = PRC_FIELD_HELP[spec.path] || undefined;
              const required =
                requestType === "create" && spec.requiredCreateIntake;
              const errMsg = fieldErrors[spec.path];
              if (spec.kind === "text") {
                return (
                  <TextField
                    key={spec.path}
                    label={required ? `${label} *` : label}
                    hint={hint}
                    value={values[spec.path] || ""}
                    onChange={(v) => set(spec.path, v)}
                  />
                );
              }
              const options =
                spec.kind === "enum"
                  ? enumOptions(spec.path, spec.enumValues || [])
                  : catalogOptions(
                      catalogs[PRC_CATALOG_KINDS[spec.path] || ""] || [],
                    );
              return (
                <div key={spec.path}>
                  <SelectField
                    label={required ? `${label} *` : label}
                    hint={hint}
                    options={withSelectedOption(
                      options,
                      values[spec.path] || "",
                    )}
                    value={values[spec.path] || ""}
                    onChange={(v) => set(spec.path, v)}
                    searchable
                  />
                  {errMsg ? (
                    <MyRequestsStateBanner variant="error">
                      {errMsg}
                    </MyRequestsStateBanner>
                  ) : null}
                  {requestType === "update" &&
                  scalarDiff.some((c) => c.path === spec.path) ? (
                    <TextField
                      label={`Justificativa — ${label}`}
                      value={reasons[spec.path] || ""}
                      onChange={(v) =>
                        setReasons((s) => ({ ...s, [spec.path]: v }))
                      }
                    />
                  ) : null}
                </div>
              );
            })}
          </MyRequestsSectionCard>

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
      )}

      {error ? (
        <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
      ) : null}

      <MyRequestsFormActions>
        <ActionButton variant="ghost" disabled={busy} onClick={onCancel}>
          Cancelar
        </ActionButton>
        <ActionButton
          variant="primary"
          disabled={busy || (requestType === "update" && !editCtx)}
          onClick={() => void submit()}
        >
          Enviar solicitação
        </ActionButton>
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
