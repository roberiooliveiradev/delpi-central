/** Nova solicitação PRC — wizard em 3 etapas:
 * 1) Identificação (criação × alteração + código/revisão-base em update)
 * 2) Ficha técnica (campos do catálogo + fornecedores)
 * 3) Revisão e envio idempotente via POST intake existente.
 * `requesterSubject` nunca é forjado — o backend deriva do JWT.
 * `source` vem da allowlist do reference-data ("portal-engineering"). */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringCheckboxControl,
  EngineeringDetailCard,
  EngineeringDetailFieldGrid,
  EngineeringFieldLabel,
  EngineeringFormActions,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringProgressTracker,
  EngineeringSectionCard,
  EngineeringSegmentToggle,
  EngineeringSelectField,
  EngineeringStateBanner,
  EngineeringTextField,
} from "../../../ui/engineeringUi";
import {
  fetchPrcCatalog,
  fetchPrcReferenceData,
  prcIntakeSubmit,
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
  PRC_FIELD_LABELS,
  PRC_SUPPLIER_LABELS,
} from "../prcCopy";
import {
  duplicateSupplierIndexes,
  emptySupplierRow,
  type SupplierRow,
} from "../prcSuppliers";
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
  const CATALOG_KINDS: Record<string, string> = {
    group: "product-groups",
    unit: "units",
    defaultWarehouse: "warehouses",
    accountingAccount: "accounting-accounts",
  };

  const [refData, setRefData] = useState<PrcReferenceData | null>(null);
  const [catalogs, setCatalogs] = useState<
    Record<string, { value: string; label: string }[]>
  >({});
  const [catalogState, setCatalogState] = useState<
    Record<string, "loading" | "ready" | "error">
  >({});

  const loadCatalog = useCallback(
    async (path: string, signal?: AbortSignal) => {
      const kind = CATALOG_KINDS[path];
      if (!kind) return;
      setCatalogState((s) => ({ ...s, [path]: "loading" }));
      try {
        const env = await fetchPrcCatalog(kind, undefined, signal);
        setCatalogs((s) => ({
          ...s,
          [path]: env.data.items.map((i) => ({
            value: i.code,
            label: `${i.code} — ${i.label}`,
          })),
        }));
        setCatalogState((s) => ({ ...s, [path]: "ready" }));
      } catch {
        setCatalogState((s) => ({ ...s, [path]: "error" }));
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
  const [loadError, setLoadError] = useState("");
  const [step, setStep] = useState(0);

  const [requestType, setRequestType] = useState<"create" | "update">(
    "create",
  );
  const [officialCode, setOfficialCode] = useState("");

  const [values, setValues] = useState<Record<string, string>>({});
  const [suppliers, setSuppliers] = useState<SupplierRow[]>([]);
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [supplierReason, setSupplierReason] = useState("");

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
    /* Catálogos TOTVS via BFF — falha vira estado de erro explícito. */
    for (const path of Object.keys(CATALOG_KINDS)) {
      void loadCatalog(path, controller.signal);
    }
    return () => controller.abort();
  }, []);

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
        if (!selectedPaths.size && suppliers === null) {
          return "Selecione ao menos um campo para alterar.";
        }
        for (const path of selectedPaths) {
          if (!(reasons[path] || "").trim()) {
            return `Informe a justificativa para «${PRC_FIELD_LABELS[path] || path}».`;
          }
        }
      }
      const bad = suppliers.findIndex(
        (r) => !r.supplierCode.trim() || !r.store.trim() || !r.supplierName.trim(),
      );
      if (bad >= 0) {
        return `Fornecedor ${bad + 1}: selecione um fornecedor oficial pela busca (código, loja e nome).`;
      }
      if (duplicateSupplierIndexes(suppliers).size > 0) {
        return "Há fornecedores duplicados (mesmo código e loja) — remova uma das linhas.";
      }
      if (requestType === "update" && !supplierReason.trim() && supplierTouched) {
        return "Informe a justificativa da alteração de fornecedores.";
      }
      return "";
    }
    return "";
  };

  const supplierTouched =
    requestType === "create" ? false : suppliers.length > 0 || selectedPaths.has("suppliers");

  const next = () => {
    const msg = validateStep(step);
    if (msg) {
      setError(msg);
      return;
    }
    setError("");
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
    }> = [...selectedPaths]
      .filter((p) => p !== "suppliers")
      .map((path) => ({
        path,
        proposedValue: (values[path] || "").trim(),
        reason: (reasons[path] || "").trim(),
      }));
    if (selectedPaths.has("suppliers") || supplierTouched) {
      changes.push({
        path: "suppliers",
        proposedValue: suppliers.map((r) => ({
          supplierCode: r.supplierCode.trim(),
          store: r.store.trim(),
          supplierName: r.supplierName.trim(),
          partNumber: r.partNumber.trim() || "",
          catalogNumber: r.catalogNumber.trim() || null,
        })),
        reason: supplierReason.trim(),
      });
    }
    return {
      source: PORTAL_SOURCE,
      requestType: "update",
      productType: refData?.productTypes?.[0] || "raw_material",
      schemaVersion: refData?.schemaVersion || 1,
      officialProductCode: officialCode.trim(),
      changes,
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

  const renderSheetField = (path: string) => {
    const spec = specByPath.get(path);
    const label = PRC_FIELD_LABELS[path] || path;
    const selected =
      requestType === "create" ? true : selectedPaths.has(path);
    return (
      <div key={path} className="engineering-prc__edit-row">
        {requestType === "update" ? (
          <EngineeringCheckboxControl
            checked={selected}
            disabled={busy}
            onChange={(v) =>
              setSelectedPaths((prev) => {
                const next = new Set(prev);
                if (v) next.add(path);
                else next.delete(path);
                return next;
              })
            }
            label={label}
            hint={spec?.note || undefined}
          />
        ) : null}
        {selected ? (
          <div className="engineering-prc__edit-controls">
            {catalogState[path] === "error" ? (
              <div className="engineering-prc__catalog-error">
                <EngineeringFieldLabel
                  htmlFor={`prc-new-${path}`}
                  label={label}
                />
                <p className="engineering-prc__field-error" role="alert">
                  Catálogo oficial indisponível — tente novamente. Valor
                  selecionado é preservado.
                </p>
                <EngineeringActionButton
                  variant="ghost"
                  disabled={busy}
                  onClick={() => void loadCatalog(path)}
                >
                  Tentar novamente
                </EngineeringActionButton>
              </div>
            ) : CATALOG_KINDS[path] ? (
              <EngineeringSelectField
                id={`prc-new-${path}`}
                label={label}
                hint={
                  catalogState[path] === "loading"
                    ? "Carregando catálogo oficial TOTVS…"
                    : catalogs[path]?.length
                      ? spec?.note || "Catálogo oficial TOTVS"
                      : "Catálogo oficial sem itens disponíveis."
                }
                value={values[path] || ""}
                onChange={(v) => setValue(path, v)}
                options={catalogs[path] || []}
                placeholderOption={
                  catalogState[path] === "loading"
                    ? "Carregando catálogo…"
                    : catalogs[path]?.length
                      ? "Selecionar…"
                      : "Nenhum item no catálogo"
                }
                required={
                  requestType === "create" &&
                  Boolean(spec?.requiredCreateIntake)
                }
                disabled={busy || catalogState[path] !== "ready"}
              />
            ) : catalogs[path]?.length ? (
              <EngineeringSelectField
                id={`prc-new-${path}`}
                label={label}
                hint={spec?.note || "Catálogo oficial TOTVS"}
                value={values[path] || ""}
                onChange={(v) => setValue(path, v)}
                options={catalogs[path]}
                placeholderOption="Selecionar…"
                required={
                  requestType === "create" &&
                  Boolean(spec?.requiredCreateIntake)
                }
                disabled={busy}
              />
            ) : spec?.enumValues?.length ? (
              <EngineeringSelectField
                id={`prc-new-${path}`}
                label={label}
                hint={spec.note || undefined}
                value={values[path] || ""}
                onChange={(v) => setValue(path, v)}
                options={spec.enumValues.map((v) => ({
                  value: v,
                  label: v,
                }))}
                required={Boolean(spec.requiredCreateIntake)}
                disabled={busy}
              />
            ) : (
              <EngineeringTextField
                id={`prc-new-${path}`}
                label={label}
                hint={spec?.note || undefined}
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
              <EngineeringTextField
                id={`prc-new-reason-${path}`}
                label="Justificativa"
                value={reasons[path] || ""}
                onChange={(v) =>
                  setReasons((s) => ({ ...s, [path]: v }))
                }
                required
                maxLength={500}
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
      : [...selectedPaths]
          .filter((p) => p !== "suppliers")
          .map((path) => ({
            label: PRC_FIELD_LABELS[path] || path,
            value: `${values[path] || ""} — ${reasons[path] || ""}`,
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
            {requestType === "update" ? (
              <EngineeringCheckboxControl
                checked={selectedPaths.has("suppliers")}
                disabled={busy}
                onChange={(v) =>
                  setSelectedPaths((prev) => {
                    const next = new Set(prev);
                    if (v) next.add("suppliers");
                    else next.delete("suppliers");
                    return next;
                  })
                }
                label="Alterar vínculos de fornecedores"
                hint="A lista informada substitui os vínculos desta solicitação."
              />
            ) : null}
            {requestType === "create" || selectedPaths.has("suppliers") ? (
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
                          <th scope="col">Nome oficial</th>
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
                          return (
                            <tr
                              key={index}
                              className={missing || dup ? "engineering-prc__supplier-tr--error" : ""}
                            >
                              <td data-label="Fornecedor">
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
                              <td data-label="Nome oficial">{row.supplierName || "—"}</td>
                              <td data-label={PRC_SUPPLIER_LABELS.partNumber}>
                                <input
                                  id={`prc-new-sup-pn-${index}`}
                                  type="text"
                                  className="engineering-prc__cell-input"
                                  aria-label={`${PRC_SUPPLIER_LABELS.partNumber} (opcional)`}
                                  title="Opcional — pode ficar vazio quando a fonte oficial também está vazia."
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
                              </td>
                              <td data-label="Ações">
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
                {requestType === "update" ? (
                  <EngineeringTextField
                    id="prc-new-sup-reason"
                    label="Justificativa da alteração de fornecedores"
                    value={supplierReason}
                    onChange={setSupplierReason}
                    required
                    maxLength={500}
                    disabled={busy}
                  />
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
                ? [{ label: "Código oficial", value: officialCode }]
                : []),
              ...reviewItems,
              {
                label: "Fornecedores",
                value:
                  requestType === "create" ||
                  selectedPaths.has("suppliers")
                    ? `${suppliers.length} vínculo(s)`
                    : "Não alterado",
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
