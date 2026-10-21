import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  ConfirmModalPanel,
  NativeSelectField,
  NativeTextAreaField,
  NativeTextField,
  ScreenLoading,
  StateBox,
} from "@delpi/plugin-ui/index";

import {
  createReport,
  deleteImage,
  exportPdf,
  getImage,
  getReport,
  putImage,
  updateReport,
  type ImageSlot,
} from "../api/metallographicReportsApi";
import { HttpRequestError } from "../api/httpClient";
import { MeasurementScheme } from "../components/MeasurementScheme";
import { MicrographSlot } from "../components/MicrographSlot";
import { METALOGRAPHY_HELP } from "../content/helpTooltips";
import { clearKey, idempotencyKey, readJson, writeJson } from "../domain/draftSession";
import { allows, METALOGRAPHY_PERMISSIONS } from "../domain/permissions";
import {
  emptyReportForm,
  formFromReport,
  formsEqual,
  MEASUREMENT_FIELDS,
  SAMPLE_FIELDS,
  toWritePayload,
  type ReportFormState,
  type ReportSnapshot,
} from "../domain/reportForm";
import {
  confirmClassNames,
  fieldClassNames,
  MetalographyDialog,
  ROOT_CLASS,
} from "../ui/metalographyUi";
import { editorPath, listPath, navigateMetalography } from "../utils/route";

type ReportEditorPageProps = {
  reportId?: string;
  readOnly: boolean;
  permissions?: readonly string[];
  isSuperadmin?: boolean;
};

function draftKey(reportId?: string): string {
  return `metalography:draft:${reportId ?? "new"}`;
}

export function ReportEditorPage({ reportId, readOnly, permissions, isSuperadmin }: ReportEditorPageProps) {
  const [form, setForm] = useState<ReportFormState>(emptyReportForm);
  const [saved, setSaved] = useState<ReportFormState>(emptyReportForm);
  const [report, setReport] = useState<ReportSnapshot | null>(null);
  const [etag, setEtag] = useState<string | null>(null);
  const [loading, setLoading] = useState(Boolean(reportId));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const [leaveOpen, setLeaveOpen] = useState(false);
  const [imageUrls, setImageUrls] = useState<Partial<Record<ImageSlot, string>>>({});

  const canEdit = !readOnly && allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.edit);
  const canCreate = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.create);
  const canDelete = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.delete);
  const canExport = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.export);
  const writable = reportId ? canEdit : canCreate;
  const dirty = useMemo(() => !formsEqual(form, saved), [form, saved]);

  const load = useCallback(async (signal?: AbortSignal) => {
    if (!reportId) {
      const stored = readJson<ReportFormState>(sessionStorage, draftKey());
      if (stored) {
        setForm(stored);
        setSaved(emptyReportForm());
      }
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await getReport(reportId, signal);
      const next = formFromReport(result.data);
      const stored = readJson<ReportFormState>(sessionStorage, draftKey(reportId));
      setReport(result.data);
      setEtag(result.etag ?? `"${result.data.version}"`);
      setSaved(next);
      setForm(stored && !formsEqual(stored, next) ? stored : next);
      setConflict(false);
    } catch (cause) {
      if ((cause as Error).name === "AbortError") return;
      if (cause instanceof HttpRequestError && (cause.status === 403 || cause.status === 404)) {
        setForbidden(cause.status === 403);
        setError(cause.message);
      } else {
        setError(cause instanceof Error ? cause.message : "Não foi possível abrir o relatório.");
      }
    } finally {
      setLoading(false);
    }
  }, [reportId]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  useEffect(() => {
    if (!dirty) return;
    writeJson(sessionStorage, draftKey(reportId), form);
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty, form, reportId]);

  useEffect(() => {
    if (!reportId || !report) return;
    let cancelled = false;
    const urls: string[] = [];
    void (async () => {
      const next: Partial<Record<ImageSlot, string>> = {};
      for (const slot of ["original", "measured"] as const) {
        if (!report.images[slot].present) continue;
        try {
          const file = await getImage(reportId, slot);
          const url = URL.createObjectURL(file.blob);
          urls.push(url);
          next[slot] = url;
        } catch {
          next[slot] = undefined;
        }
      }
      if (!cancelled) setImageUrls(next);
    })();
    return () => {
      cancelled = true;
      for (const url of urls) URL.revokeObjectURL(url);
    };
  }, [report, reportId]);

  function patchForm(next: ReportFormState) {
    setForm(next);
  }

  async function save() {
    if (!writable || saving) return;
    setSaving(true);
    setError(null);
    const payload = toWritePayload(form);
    try {
      if (!reportId) {
        const storageKey = "metalography:create-key";
        const key = idempotencyKey(sessionStorage, storageKey, () => crypto.randomUUID());
        const created = await createReport(payload, key);
        clearKey(sessionStorage, storageKey);
        clearKey(sessionStorage, draftKey());
        navigateMetalography(editorPath(created.data.id));
        return;
      }
      if (!etag) throw new HttpRequestError("A versão do relatório não foi enviada. Recarregue e tente de novo.", 428);
      const updated = await updateReport(reportId, payload, etag);
      clearKey(sessionStorage, draftKey(reportId));
      const next = formFromReport(updated.data);
      setReport(updated.data);
      setForm(next);
      setSaved(next);
      setEtag(updated.etag ?? `"${updated.data.version}"`);
      setConflict(false);
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 412) {
        setConflict(true);
      }
      setError(cause instanceof Error ? cause.message : "Não foi possível salvar o relatório.");
    } finally {
      setSaving(false);
    }
  }

  async function commitImage(slot: ImageSlot, file: File) {
    if (!reportId || !etag || saving) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await putImage(reportId, slot, file, file.type, etag);
      setEtag(`"${updated.data.version}"`);
      await load();
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 412) setConflict(true);
      setError(cause instanceof Error ? cause.message : "Não foi possível gravar a micrografia.");
    } finally {
      setSaving(false);
    }
  }

  async function removeImage(slot: ImageSlot) {
    if (!reportId || !etag || saving) return;
    setSaving(true);
    try {
      const updated = await deleteImage(reportId, slot, etag);
      setEtag(`"${updated.data.version}"`);
      await load();
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 412) setConflict(true);
      setError(cause instanceof Error ? cause.message : "Não foi possível remover a micrografia.");
    } finally {
      setSaving(false);
    }
  }

  async function downloadPdf() {
    if (!reportId) return;
    setSaving(true);
    try {
      const file = await exportPdf(reportId);
      const url = URL.createObjectURL(file.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${report?.report_number ?? "relatorio"}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível exportar o PDF.");
    } finally {
      setSaving(false);
    }
  }

  function requestLeave() {
    if (dirty) setLeaveOpen(true);
    else navigateMetalography(listPath());
  }

  return (
    <div className={`${ROOT_CLASS} dashboard-page`}>
      <article className="mg-sheet">
        <header className="mg-sheet__header">
          <p>DELPI</p>
          <h1>Relatório de Análise Metalográfica</h1>
          <ActionButton type="button" variant="ghost" onClick={requestLeave}>Voltar à lista</ActionButton>
        </header>
        {loading ? <ScreenLoading label="Carregando relatório" variant="embedded" /> : null}
        {forbidden ? <StateBox prefix="mg" variant="error">Você não tem permissão para abrir este relatório.</StateBox> : null}
        {error ? <StateBox prefix="mg" variant="error">{error}</StateBox> : null}
        {conflict ? <StateBox prefix="mg" variant="warning">{METALOGRAPHY_HELP.conflict}</StateBox> : null}
        {conflict ? (
          <ActionButton type="button" variant="ghost" onClick={() => void load()}>
            Recarregar versão do servidor
          </ActionButton>
        ) : null}
        <section aria-labelledby="mg-identification">
          <h2 id="mg-identification">Identificação do documento</h2>
          <p>{METALOGRAPHY_HELP.number}</p>
          <div className="mg-grid">
            <NativeTextField id="mg-number" label="Número do relatório" hint={METALOGRAPHY_HELP.number} classNames={fieldClassNames} value={report?.report_number ?? ""} onChange={() => undefined} readOnly />
            <NativeTextField id="mg-date" label="Data" type="date" classNames={fieldClassNames} value={form.reportDate} disabled={!writable} onChange={(value) => patchForm({ ...form, reportDate: value })} />
            <NativeTextField id="mg-revision" label="Revisão" hint={METALOGRAPHY_HELP.revision} maxLength={16} classNames={fieldClassNames} value={form.revision} disabled={!writable} onChange={(value) => patchForm({ ...form, revision: value })} />
          </div>
        </section>
        <section aria-labelledby="mg-sample">
          <h2 id="mg-sample">01 — Identificação da amostra</h2>
          <div className="mg-grid">
            {SAMPLE_FIELDS.map((field) => (
              <NativeTextField
                key={field.key}
                id={`mg-${field.key}`}
                label={field.label}
                maxLength={240}
                classNames={fieldClassNames}
                value={form.sample[field.key]}
                disabled={!writable}
                onChange={(value) => patchForm({ ...form, sample: { ...form.sample, [field.key]: value } })}
              />
            ))}
          </div>
        </section>
        <section aria-labelledby="mg-images">
          <h2 id="mg-images">02 — Análise da seção transversal</h2>
          <p>{METALOGRAPHY_HELP.images}</p>
          <div className="mg-grid">
            <MicrographSlot slot="original" title="Micrografia original" present={Boolean(report?.images.original.present)} remoteUrl={imageUrls.original ?? null} readOnly={!writable || !reportId} disabled={saving} onCommit={(file) => void commitImage("original", file)} onRemove={() => void removeImage("original")} />
            <MicrographSlot slot="measured" title="Micrografia com medições" present={Boolean(report?.images.measured.present)} remoteUrl={imageUrls.measured ?? null} readOnly={!writable || !reportId} disabled={saving} onCommit={(file) => void commitImage("measured", file)} onRemove={() => void removeImage("measured")} />
          </div>
        </section>
        <section aria-labelledby="mg-measurements">
          <h2 id="mg-measurements">03 — Resultados das medições</h2>
          <p>{METALOGRAPHY_HELP.measurements}</p>
          <MeasurementScheme />
          <div className="mg-table-wrap">
            <table className="mg-table">
              <thead>
                <tr>
                  <th>Parâmetro</th>
                  <th>Critério / tolerância</th>
                  <th>Valor medido</th>
                </tr>
              </thead>
              <tbody>
                {MEASUREMENT_FIELDS.map((field) => (
                  <tr key={field.key}>
                    <th scope="row">{field.label} — {field.code}</th>
                    <td>
                      <NativeTextField id={`mg-${field.key}-criterion`} label={`Critério ${field.code}`} maxLength={120} classNames={fieldClassNames} value={form.measurements[field.key].criterion} disabled={!writable} onChange={(value) => patchForm({ ...form, measurements: { ...form.measurements, [field.key]: { ...form.measurements[field.key], criterion: value } } })} />
                    </td>
                    <td>
                      <NativeTextField id={`mg-${field.key}-measured`} label={`Medido ${field.code}`} maxLength={40} classNames={fieldClassNames} value={form.measurements[field.key].measured} disabled={!writable} onChange={(value) => patchForm({ ...form, measurements: { ...form.measurements, [field.key]: { ...form.measurements[field.key], measured: value } } })} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        <section aria-labelledby="mg-conclusion">
          <h2 id="mg-conclusion">04 — Conclusão técnica</h2>
          <NativeSelectField
            id="mg-conclusion"
            label="Resultado"
            hint={METALOGRAPHY_HELP.conclusion}
            classNames={fieldClassNames}
            value={form.conclusionResult}
            disabled={!writable}
            options={[
              { value: "", label: "Sem conclusão" },
              { value: "conforming", label: "Conforme" },
              { value: "nonconforming", label: "Não conforme" },
            ]}
            onChange={(value) => patchForm({ ...form, conclusionResult: value === "conforming" || value === "nonconforming" ? value : "" })}
          />
          <NativeTextAreaField id="mg-notes" label="Observações" maxLength={4000} classNames={fieldClassNames} value={form.conclusionNotes} disabled={!writable} onChange={(value) => patchForm({ ...form, conclusionNotes: value })} />
        </section>
        <section aria-labelledby="mg-analyst">
          <h2 id="mg-analyst">05 — Responsável pela análise</h2>
          <NativeTextField id="mg-analyst-name" label="Analista" maxLength={160} classNames={fieldClassNames} value={form.analystName} disabled={!writable} onChange={(value) => patchForm({ ...form, analystName: value })} />
        </section>
        <footer className="mg-sheet__footer">
          <p>Documento de análise metalográfica. O PDF exportado segue o snapshot salvo no servidor.</p>
          <div className="mg-actions">
            {writable ? (
              <ActionButton type="button" variant="primary" disabled={saving || !dirty} onClick={() => void save()}>
                {saving ? "Salvando…" : "Salvar"}
              </ActionButton>
            ) : null}
            {canExport && reportId ? (
              <ActionButton type="button" variant="ghost" disabled={saving} title={METALOGRAPHY_HELP.pdf} onClick={() => void downloadPdf()}>
                Exportar PDF
              </ActionButton>
            ) : null}
            {canDelete && reportId ? (
              <ActionButton type="button" variant="ghost" disabled={saving || !etag} onClick={() => void deleteAndLeave()}>
                Excluir
              </ActionButton>
            ) : null}
          </div>
        </footer>
      </article>
      {leaveOpen ? (
        <MetalographyDialog open title="Alterações não salvas" onClose={() => setLeaveOpen(false)}>
          <ConfirmModalPanel
            classNames={confirmClassNames}
            message="Há dados ainda não salvos. Eles ficam neste navegador até você salvar ou descartar."
            confirmLabel="Continuar editando"
            secondaryLabel="Sair sem salvar"
            onConfirm={() => setLeaveOpen(false)}
            onCancel={() => setLeaveOpen(false)}
            onSecondary={() => {
              clearKey(sessionStorage, draftKey(reportId));
              navigateMetalography(listPath());
            }}
          />
        </MetalographyDialog>
      ) : null}
    </div>
  );

  async function deleteAndLeave() {
    if (!reportId || !etag) return;
    setSaving(true);
    try {
      const { deleteReport } = await import("../api/metallographicReportsApi");
      await deleteReport(reportId, etag);
      clearKey(sessionStorage, draftKey(reportId));
      navigateMetalography(listPath());
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 412) setConflict(true);
      setError(cause instanceof Error ? cause.message : "Não foi possível excluir o relatório.");
    } finally {
      setSaving(false);
    }
  }
}
