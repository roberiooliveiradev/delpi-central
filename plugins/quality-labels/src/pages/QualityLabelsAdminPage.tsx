import {
  Fragment,
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileSearch,
  FileText,
  Loader2,
  Power,
  Printer,
  QrCode,
  RefreshCw,
  Search,
  Tag,
  Trash2,
} from "lucide-react";

import { HttpRequestError } from "../api/httpClient";
import {
  createLabel,
  deleteLabel,
  fetchLabelQrBlob,
  getChecklistTemplate,
  listLabels,
  lookupOp,
  saveCertificate,
  searchOps,
  setLabelActive,
} from "../api/qualityLabelsApi";
import { printQualityLabel } from "../utils/labelPrint";
import {
  OPERATIONAL_UNIT_OPTIONS,
  formatOperationalUnit,
} from "../utils/operationalUnits";
import { UnitMultiSelect } from "../components/UnitMultiSelect";
import { AuditMetadataModal } from "../components/AuditMetadataModal";
import { CertificateEditor } from "../components/CertificateEditor";
import { CertificateFormFields } from "../components/CertificateFormFields";
import {
  QlNativeSelectField,
  QlNativeTextAreaField,
  QlNativeTextField,
} from "../components/qlFormFields";
import {
  buildEmptyDraft,
  formToSavePayload,
  syncDraftFromInspection,
} from "../utils/certificateFormUtils";
import type {
  CertificateFormState,
  OpLookup,
  OpSuggestion,
  QualityLabel,
  QualityLabelResult,
} from "../types/qualityLabels";

const RESULT_OPTIONS: { value: QualityLabelResult; label: string }[] = [
  { value: "approved", label: "Aprovado" },
  { value: "rejected", label: "Reprovado" },
  { value: "conditional", label: "Condicional" },
];

const RESULT_LABELS: Record<QualityLabelResult, string> = {
  approved: "Aprovado",
  rejected: "Reprovado",
  conditional: "Condicional",
};

function formatDate(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString("pt-BR");
}

export function QualityLabelsAdminPage() {
  const [op, setOp] = useState("");
  const [branch, setBranch] = useState("");
  const [result, setResult] = useState<QualityLabelResult>("approved");
  const [inspectedQuantity, setInspectedQuantity] = useState("");
  const [notes, setNotes] = useState("");
  const [lookup, setLookup] = useState<OpLookup | null>(null);

  const [suggestions, setSuggestions] = useState<OpSuggestion[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [searchingOps, setSearchingOps] = useState(false);
  const opFieldRef = useRef<HTMLDivElement>(null);
  const skipNextSearch = useRef(false);

  const [looking, setLooking] = useState(false);
  const [saving, setSaving] = useState(false);
  const [confirmExisting, setConfirmExisting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [labels, setLabels] = useState<QualityLabel[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [search, setSearch] = useState("");
  const [filterBranches, setFilterBranches] = useState<string[]>([]);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [auditLabel, setAuditLabel] = useState<QualityLabel | null>(null);
  const [expandedCertificateId, setExpandedCertificateId] = useState<string | null>(null);

  const [certificateExpanded, setCertificateExpanded] = useState(false);
  const [certificateDraft, setCertificateDraft] = useState<CertificateFormState | null>(null);
  const [certificateTemplateLoading, setCertificateTemplateLoading] = useState(false);

  const refreshList = useCallback(
    async (searchTerm: string, branches: string[], signal?: AbortSignal) => {
      setLoadingList(true);
      try {
        const page = await listLabels(
          {
            search: searchTerm || undefined,
            branches: branches.length > 0 ? branches : undefined,
            limit: 100,
          },
          signal,
        );
        setLabels(page.items);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar as etiquetas.");
        }
      } finally {
        setLoadingList(false);
      }
    },
    [],
  );

  // Carga inicial e reaplicação do filtro por unidade.
  useEffect(() => {
    const controller = new AbortController();
    void refreshList(search, filterBranches, controller.signal);
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterBranches, refreshList]);

  // Busca por proximidade da OP durante a digitação (debounce).
  useEffect(() => {
    const term = op.trim();
    if (skipNextSearch.current) {
      skipNextSearch.current = false;
      return;
    }
    if (term.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    const controller = new AbortController();
    setSearchingOps(true);
    const handle = window.setTimeout(async () => {
      try {
        const items = await searchOps(
          term,
          branch ? [branch] : undefined,
          controller.signal,
        );
        setSuggestions(items);
        setShowSuggestions(items.length > 0);
      } catch (err) {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setSuggestions([]);
        }
      } finally {
        setSearchingOps(false);
      }
    }, 350);
    return () => {
      controller.abort();
      window.clearTimeout(handle);
    };
  }, [op, branch]);

  useEffect(() => {
    if (!showSuggestions) return;
    function onClickOutside(event: MouseEvent) {
      if (opFieldRef.current && !opFieldRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [showSuggestions]);

  useEffect(() => {
    if (!certificateExpanded || certificateDraft) return;
    const controller = new AbortController();
    setCertificateTemplateLoading(true);
    getChecklistTemplate(controller.signal)
      .then((items) => {
        setCertificateDraft(
          buildEmptyDraft({
            templateItems: items,
            inspectedQuantity,
            lookup,
          }),
        );
      })
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar o checklist.");
        }
      })
      .finally(() => setCertificateTemplateLoading(false));
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [certificateExpanded]);

  useEffect(() => {
    if (!certificateDraft) return;
    setCertificateDraft((prev) =>
      prev ? syncDraftFromInspection(prev, { inspectedQuantity, lookup }) : prev,
    );
  }, [inspectedQuantity, lookup]);

  const runLookup = useCallback(async (opValue: string, branchValue: string) => {
    if (!opValue.trim()) return;
    setLooking(true);
    setError(null);
    setSuccess(null);
    setLookup(null);
    setConfirmExisting(false);
    try {
      const data = await lookupOp(opValue.trim(), branchValue.trim() || undefined);
      setLookup(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao consultar a OP.");
    } finally {
      setLooking(false);
    }
  }, []);

  function handleSelectSuggestion(item: OpSuggestion) {
    skipNextSearch.current = true;
    setOp(item.productionOrder);
    if (item.branch) setBranch(item.branch);
    setShowSuggestions(false);
    setSuggestions([]);
    void runLookup(item.productionOrder, item.branch ?? branch);
  }

  async function doRegister() {
    if (!op.trim()) return;

    if (lookup?.hasActiveInspection && !confirmExisting) {
      setConfirmExisting(true);
      setError(null);
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const label = await createLabel({
        productionOrder: op.trim(),
        branch: branch.trim() || null,
        result,
        notes: notes.trim() || null,
        inspectedQuantity: inspectedQuantity.trim()
          ? Math.max(0, Math.trunc(Number(inspectedQuantity)))
          : null,
      });

      let successMessage = `Etiqueta registrada para ${label.productCode}.`;
      if (certificateExpanded && certificateDraft) {
        await saveCertificate(label.id, formToSavePayload(certificateDraft, false));
        successMessage += " Certificado salvo como rascunho (auditoria registrada).";
        setExpandedCertificateId(label.id);
      }

      setSuccess(successMessage);
      setOp("");
      setBranch("");
      setNotes("");
      setResult("approved");
      setInspectedQuantity("");
      setLookup(null);
      setConfirmExisting(false);
      setSuggestions([]);
      setCertificateExpanded(false);
      setCertificateDraft(null);
      await refreshList(search, filterBranches);
    } catch (err) {
      if (err instanceof HttpRequestError && err.status === 404) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Erro ao registrar a etiqueta.");
      }
    } finally {
      setSaving(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void doRegister();
  }

  function toggleCertificateSection() {
    setCertificateExpanded((prev) => !prev);
  }

  function toggleRowCertificate(label: QualityLabel) {
    setExpandedCertificateId((prev) => (prev === label.id ? null : label.id));
  }

  async function handlePrint(label: QualityLabel) {
    setBusyId(label.id);
    setError(null);
    try {
      const blob = await fetchLabelQrBlob(label.id);
      await printQualityLabel(label, blob);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao imprimir a etiqueta.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDelete(label: QualityLabel) {
    const confirmed = window.confirm(
      `Excluir definitivamente a etiqueta da OP ${label.productionOrder} (${label.productCode})?\n\nEsta ação não pode ser desfeita. O registro sai da lista, mas o evento fica na auditoria.`,
    );
    if (!confirmed) return;
    setBusyId(label.id);
    setError(null);
    setSuccess(null);
    try {
      await deleteLabel(label.id);
      setLabels((prev) => prev.filter((item) => item.id !== label.id));
      setSuccess(`Etiqueta da OP ${label.productionOrder} excluída.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir a etiqueta.");
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggleActive(label: QualityLabel) {
    setBusyId(label.id);
    setError(null);
    try {
      const updated = await setLabelActive(label.id, !label.isActive);
      setLabels((prev) =>
        prev.map((item) =>
          item.id === label.id ? { ...item, isActive: updated.isActive } : item,
        ),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar a etiqueta.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
          {error && <div className="ql-state ql-state--error"><p>{error}</p></div>}
          {success && <div className="ql-state ql-state--success"><p>{success}</p></div>}

          <section className="ql-card">
            <div className="ql-card__accent" />
            <form className="ql-form" onSubmit={handleSubmit}>
              <div className="ql-form__grid">
                <label className="ql-field">
                  <span className="ql-label-text">Ordem de produção (OP)</span>
                  <div className="ql-op-row">
                    <div className="ql-op-search" ref={opFieldRef}>
                      <input
                        className="ql-input"
                        value={op}
                        onChange={(e) => setOp(e.target.value)}
                        onFocus={() => {
                          if (suggestions.length > 0) setShowSuggestions(true);
                        }}
                        placeholder="Digite a OP (busca automática)"
                        autoComplete="off"
                        required
                      />
                      {searchingOps && (
                        <Loader2 className="ql-icon ql-spin ql-op-search__spin" />
                      )}
                      {showSuggestions && suggestions.length > 0 && (
                        <ul className="ql-suggestions">
                          {suggestions.map((item) => (
                            <li key={`${item.productionOrder}-${item.branch ?? ""}`}>
                              <button
                                type="button"
                                className="ql-suggestion"
                                onClick={() => handleSelectSuggestion(item)}
                              >
                                <span className="ql-suggestion__op">
                                  OP {item.productionOrder}
                                </span>
                                <span className="ql-suggestion__product">
                                  {item.productCode} · {item.productDescription}
                                </span>
                                <span className="ql-suggestion__unit">
                                  {formatOperationalUnit(item.branch, "—")}
                                </span>
                              </button>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <button
                      type="button"
                      className="ql-btn ql-btn--ghost"
                      onClick={() => void runLookup(op, branch)}
                      disabled={looking || !op.trim()}
                    >
                      {looking ? <Loader2 className="ql-icon ql-spin" /> : <Search className="ql-icon" />}
                      Consultar
                    </button>
                  </div>
                </label>

                <QlNativeSelectField
                  id="ql-admin-branch"
                  label="Unidade (opcional)"
                  value={branch}
                  onChange={setBranch}
                  controlClassName="ql-input"
                  placeholderOption="Todas as unidades"
                  options={OPERATIONAL_UNIT_OPTIONS.map((opt) => ({
                    value: opt.value,
                    label: opt.label,
                  }))}
                />

                <QlNativeSelectField
                  id="ql-admin-result"
                  label="Resultado"
                  value={result}
                  onChange={(value) => setResult(value as QualityLabelResult)}
                  controlClassName="ql-input"
                  options={RESULT_OPTIONS}
                />

                <QlNativeTextField
                  id="ql-admin-inspected"
                  label="Peças inspecionadas (opcional)"
                  type="number"
                  min={0}
                  inputMode="numeric"
                  value={inspectedQuantity}
                  onChange={setInspectedQuantity}
                  placeholder="Ex.: 10"
                  controlClassName="ql-input"
                />
              </div>

              <QlNativeTextAreaField
                id="ql-admin-notes"
                label="Observações (opcional)"
                value={notes}
                onChange={setNotes}
                rows={2}
                span={false}
                placeholder="Notas da inspeção"
                controlClassName="ql-input ql-textarea"
              />

              {lookup && (
                <div className="ql-lookup">
                  <Tag className="ql-icon" />
                  <div>
                    <p className="ql-lookup__code">{lookup.productCode}</p>
                    <p className="ql-lookup__desc">{lookup.productDescription}</p>
                    <p className="ql-lookup__meta">
                      OP {lookup.productionOrder}
                      {lookup.branchName ? ` · ${lookup.branchName}` : ""}
                      {lookup.productUnit ? ` · ${lookup.productUnit}` : ""}
                    </p>
                  </div>
                </div>
              )}

              {lookup && lookup.existingLabels.length > 0 && (
                <div className="ql-warning">
                  <AlertTriangle className="ql-icon" />
                  <div>
                    <p className="ql-warning__title">
                      {lookup.hasActiveInspection
                        ? "Já existe inspeção ativa para esta OP."
                        : "Esta OP já teve inspeções registradas."}
                    </p>
                    <ul className="ql-warning__list">
                      {lookup.existingLabels.map((item) => (
                        <li key={item.id}>
                          {formatDate(item.inspectedAt)} · {item.inspectorName} ·{" "}
                          {RESULT_LABELS[item.result] ?? item.result}
                          {item.isActive ? " · Ativa" : " · Inativa"}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              <div className="ql-cert-collapse">
                <button
                  type="button"
                  className={`ql-btn ql-btn--ghost ql-cert-collapse__toggle ${
                    certificateExpanded ? "ql-cert-collapse__toggle--open" : ""
                  }`}
                  onClick={toggleCertificateSection}
                  aria-expanded={certificateExpanded}
                >
                  {certificateExpanded ? (
                    <ChevronUp className="ql-icon" />
                  ) : (
                    <ChevronDown className="ql-icon" />
                  )}
                  Certificado de qualidade
                </button>

                {certificateExpanded && (
                  <div className="ql-cert-collapse__body">
                    <p className="ql-info-note ql-info-note--compact">
                      Preencha o certificado antes ou junto com o registro. Ao registrar,
                      um rascunho é salvo automaticamente; edições posteriores ficam na
                      auditoria.
                    </p>
                    {certificateTemplateLoading || !certificateDraft ? (
                      <div className="ql-state">
                        <p>
                          <Loader2 className="ql-icon ql-spin" /> Carregando checklist...
                        </p>
                      </div>
                    ) : (
                      <CertificateFormFields
                        form={certificateDraft}
                        onChange={(partial) =>
                          setCertificateDraft((prev) =>
                            prev ? { ...prev, ...partial } : prev,
                          )
                        }
                        productionOrder={(lookup?.productionOrder ?? op.trim()) || undefined}
                        productCode={lookup?.productCode}
                        docRef="RQ-032 – Rev.00 – 21/01/2021"
                        disabled={saving}
                      />
                    )}
                  </div>
                )}
              </div>

              <div className="ql-form__actions">
                <button
                  type="submit"
                  className={`ql-btn ${confirmExisting ? "ql-btn--warning" : "ql-btn--primary"}`}
                  disabled={saving || !op.trim()}
                >
                  {saving ? <Loader2 className="ql-icon ql-spin" /> : <QrCode className="ql-icon" />}
                  {confirmExisting ? "Registrar mesmo assim" : "Registrar inspeção"}
                </button>
              </div>
            </form>
          </section>

          <section className="ql-list">
            <div className="ql-list__header">
              <h2 className="ql-list__title">Etiquetas registradas</h2>
              <div className="ql-list__filters">
                <UnitMultiSelect
                  value={filterBranches}
                  onChange={setFilterBranches}
                  placeholder="Todas as unidades"
                />
                <div className="ql-op-row">
                  <input
                    className="ql-input"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Buscar por OP, produto ou inspetor"
                    onKeyDown={(e) => {
                      if (e.key === "Enter") void refreshList(search, filterBranches);
                    }}
                  />
                  <button
                    type="button"
                    className="ql-btn ql-btn--ghost"
                    onClick={() => void refreshList(search, filterBranches)}
                  >
                    <RefreshCw className="ql-icon" /> Atualizar
                  </button>
                </div>
              </div>
            </div>

            {loadingList ? (
              <div className="ql-state"><p>Carregando etiquetas...</p></div>
            ) : labels.length === 0 ? (
              <div className="ql-state"><p>Nenhuma etiqueta registrada ainda.</p></div>
            ) : (
              <div className="ql-table-wrap">
                <table className="ql-table">
                  <thead>
                    <tr>
                      <th>Produto</th>
                      <th>OP</th>
                      <th>Unidade</th>
                      <th>Inspeção</th>
                      <th>Inspetor</th>
                      <th>Views</th>
                      <th>Situação</th>
                      <th className="ql-table__actions-col">Ações</th>
                    </tr>
                  </thead>
                  <tbody>
                    {labels.map((label) => (
                      <Fragment key={label.id}>
                        <tr key={label.id} className={label.isActive ? "" : "ql-row--inactive"}>
                          <td>
                            <span className="ql-cell-strong">{label.productCode}</span>
                            <span className="ql-cell-muted">{label.productDescription}</span>
                          </td>
                          <td>{label.productionOrder}</td>
                          <td>{label.branchName ?? formatOperationalUnit(label.branch)}</td>
                          <td>{formatDate(label.inspectedAt)}</td>
                          <td>{label.inspectorName}</td>
                          <td>{label.viewCount}</td>
                          <td>
                            <span className={`ql-badge ${label.isActive ? "ql-badge--on" : "ql-badge--off"}`}>
                              {label.isActive ? "Ativa" : "Inativa"}
                            </span>
                          </td>
                          <td>
                            <div className="ql-actions">
                              <button
                                type="button"
                                className="ql-icon-btn"
                                title="Ver auditoria (dados da OP/produto)"
                                onClick={() => setAuditLabel(label)}
                              >
                                <FileSearch className="ql-icon" />
                              </button>
                              <button
                                type="button"
                                className={`ql-icon-btn ${
                                  expandedCertificateId === label.id ? "ql-icon-btn--active" : ""
                                }`}
                                title="Certificado de qualidade"
                                onClick={() => toggleRowCertificate(label)}
                              >
                                <FileText className="ql-icon" />
                              </button>
                              <button
                                type="button"
                                className="ql-icon-btn"
                                title="Imprimir etiqueta"
                                onClick={() => void handlePrint(label)}
                                disabled={busyId === label.id}
                              >
                                <Printer className="ql-icon" />
                              </button>
                              <a
                                className="ql-icon-btn"
                                title="Abrir página pública"
                                href={label.publicUrl}
                                target="_blank"
                                rel="noreferrer"
                              >
                                <ExternalLink className="ql-icon" />
                              </a>
                              <button
                                type="button"
                                className="ql-icon-btn"
                                title={label.isActive ? "Desativar" : "Reativar"}
                                onClick={() => void handleToggleActive(label)}
                                disabled={busyId === label.id}
                              >
                                <Power className="ql-icon" />
                              </button>
                              <button
                                type="button"
                                className="ql-icon-btn ql-icon-btn--danger"
                                title="Excluir etiqueta"
                                onClick={() => void handleDelete(label)}
                                disabled={busyId === label.id}
                              >
                                <Trash2 className="ql-icon" />
                              </button>
                            </div>
                          </td>
                        </tr>
                        {expandedCertificateId === label.id && (
                          <tr key={`${label.id}-certificate`} className="ql-table__expand-row">
                            <td colSpan={8}>
                              <CertificateEditor
                                label={label}
                                onSaved={(message) => setSuccess(message)}
                                onError={(message) => setError(message)}
                              />
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

      {auditLabel && (
        <AuditMetadataModal label={auditLabel} onClose={() => setAuditLabel(null)} />
      )}
    </>
  );
}
