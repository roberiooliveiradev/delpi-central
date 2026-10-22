import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { lockContainedModalScroll, printDelpiDocumentHtml, useContainedModalViewportStyle } from "@delpi/plugin-ui/index";

import font400Url from "../assets/delpi-sans-400.otf";
import font700Url from "../assets/delpi-sans-700.otf";
import diagramUrl from "../assets/measurement-scheme.png";
import { DelpiReportLogo } from "./DelpiReportLogo";
import {
  createReport,
  deleteReport,
  exportPdf,
  getImage,
  getReport,
  listReports,
  putImage,
  updateReport,
} from "../api/metallographicReportsApi";
import { HttpRequestError } from "../api/httpClient";
import { clearKey, idempotencyKey } from "../domain/draftSession";
import { retainModalFocus } from "../domain/modalFocus";
import { allows, METALOGRAPHY_PERMISSIONS } from "../domain/permissions";
import {
  copyReportForm,
  emptyReportForm,
  newReportForm,
  formFromReport,
  formsEqual,
  toWritePayload,
  type ReportFormState,
  type ReportSnapshot,
} from "../domain/reportForm";
import {
  metallographicPrintStylesheet,
  printIsolatedMetallographicSheet,
  readMetallographicStylesheet,
} from "../domain/metallographicPrint";
import { EMPTY_REPORT_FILTERS, reportMatches, type ReportListFilters } from "../domain/reportListFilter";
import { CropDialog } from "./CropDialog";
import { editorPath, listPath, navigateMetalography } from "../utils/route";

type SlotKey = "original" | "measured";

type SlotView = {
  previewUrl: string | null;
  fileName: string;
  pending: File | null;
};

const SLOT_HINT: Record<SlotKey, string> = {
  original: "Imagem óptica sem marcações",
  measured: "Imagem da seção com medições",
};

function emptySlots(): Record<SlotKey, SlotView> {
  return {
    original: { previewUrl: null, fileName: SLOT_HINT.original, pending: null },
    measured: { previewUrl: null, fileName: SLOT_HINT.measured, pending: null },
  };
}

function formatStamp(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function stopEscape(event: { key: string; stopPropagation: () => void }) {
  if (event.key === "Escape") event.stopPropagation();
}

async function loadImage(file: File): Promise<HTMLImageElement> {
  const url = await file.arrayBuffer().then((buffer) => URL.createObjectURL(new Blob([buffer], { type: file.type })));
  try {
    const image = new Image();
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("Não foi possível abrir essa imagem."));
      image.src = url;
    });
    return image;
  } finally {
    URL.revokeObjectURL(url);
  }
}

export function MetallographicWorkspace({
  editing,
  reportId,
  readOnly = false,
  permissions,
  isSuperadmin,
}: {
  editing: boolean;
  reportId?: string;
  readOnly?: boolean;
  permissions?: readonly string[];
  isSuperadmin?: boolean;
}) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const actionLock = useRef(false);
  const [hostNode, setHostNode] = useState<HTMLDivElement | null>(null);
  const [reports, setReports] = useState<ReportSnapshot[]>([]);
  const [filters, setFilters] = useState<ReportListFilters>(EMPTY_REPORT_FILTERS);
  const [hint, setHint] = useState("Carregando os relatórios salvos no servidor.");
  const [hintError, setHintError] = useState(false);
  const [forbidden, setForbidden] = useState(false);
  const [form, setForm] = useState<ReportFormState>(emptyReportForm);
  const [savedForm, setSavedForm] = useState<ReportFormState>(emptyReportForm);
  const [number, setNumber] = useState("");
  const [etag, setEtag] = useState<string | null>(null);
  const [slots, setSlots] = useState(emptySlots);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState("");
  const [crop, setCrop] = useState<{ slot: SlotKey; image: HTMLImageElement; fileName: string } | null>(null);
  const [confirm, setConfirm] = useState<"leave" | "delete" | "copy" | null>(null);
  const [pendingReport, setPendingReport] = useState<ReportSnapshot | null>(null);
  const [dialogError, setDialogError] = useState("");
  const modalActive = Boolean(confirm) || Boolean(crop);
  const overlay = useContainedModalViewportStyle(modalActive, hostNode);
  const canCreate = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.create);
  const canEdit = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.edit);
  const canDelete = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.delete);
  const canExport = allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.export);
  const writable = !readOnly && canEdit;
  const dirty = !formsEqual(form, savedForm) || slots.original.pending !== null || slots.measured.pending !== null;

  const showToast = useCallback((message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 4800);
  }, []);

  const bindHost = useCallback((node: HTMLDivElement | null) => {
    hostRef.current = node;
    setHostNode(node);
  }, []);

  useEffect(() => {
    if (!modalActive || !hostNode) return undefined;
    return lockContainedModalScroll(hostNode);
  }, [modalActive, hostNode]);

  useEffect(() => {
    if (!modalActive || !hostNode) return undefined;
    const dialog = hostNode.querySelector<HTMLElement>(".return-home-modal.open [role='dialog'], .crop-modal.open [role='dialog']");
    if (!dialog) return undefined;
    return retainModalFocus(dialog);
  }, [modalActive, confirm, crop, hostNode]);

  const loadList = useCallback(async () => {
    if (!allows(permissions, isSuperadmin, METALOGRAPHY_PERMISSIONS.view)) {
      setForbidden(true);
      setHint("Você não tem permissão para consultar os relatórios.");
      setHintError(true);
      return;
    }
    setHintError(false);
    try {
      const collected: ReportSnapshot[] = [];
      let page = 1;
      let hasNext = true;
      while (hasNext && page <= 20) {
        const result = await listReports({ page, pageSize: 100, sort: "created_at_desc" });
        collected.push(...result.data.items);
        hasNext = result.data.has_next;
        page += 1;
      }
      setReports(collected);
      setForbidden(false);
      setHint("Os relatórios ficam armazenados no servidor do Minha DELPI.");
    } catch (cause) {
      setHintError(true);
      setHint(cause instanceof HttpRequestError ? cause.message : "Não foi possível carregar os relatórios.");
    }
  }, [isSuperadmin, permissions]);

  useEffect(() => {
    if (!editing) void loadList();
  }, [editing, loadList]);

  useEffect(() => {
    if (!editing || !reportId) return undefined;
    const controller = new AbortController();
    void (async () => {
      try {
        const result = await getReport(reportId, controller.signal);
        const next = formFromReport(result.data);
        setForm(next);
        setSavedForm(next);
        setNumber(result.data.report_number);
        setEtag(result.etag);
        const nextSlots = emptySlots();
        for (const slot of ["original", "measured"] as const) {
          if (!result.data.images[slot].present) continue;
          const image = await getImage(reportId, slot);
          nextSlots[slot] = { previewUrl: URL.createObjectURL(image.blob), fileName: SLOT_HINT[slot], pending: null };
        }
        setSlots(nextSlots);
      } catch (cause) {
        if ((cause as Error).name === "AbortError") return;
        showToast(cause instanceof HttpRequestError ? cause.message : "Não foi possível abrir o relatório.");
      }
    })();
    return () => controller.abort();
  }, [editing, reportId, showToast]);

  useEffect(() => {
    if (!dirty || !editing) return undefined;
    const onLeave = (event: BeforeUnloadEvent) => {
      event.preventDefault();
    };
    window.addEventListener("beforeunload", onLeave);
    return () => window.removeEventListener("beforeunload", onLeave);
  }, [dirty, editing]);

  const visible = reports.filter((report) => reportMatches(report, filters));
  const filtersActive = Object.values(filters).some((value) => value.trim() !== "");
  const total = reports.length;

  async function createBlank() {
    if (!canCreate || busy) return;
    setBusy(true);
    try {
      const key = idempotencyKey(sessionStorage, "metalography:create-key", () => crypto.randomUUID());
      const created = await createReport(toWritePayload(newReportForm()), key);
      clearKey(sessionStorage, "metalography:create-key");
      navigateMetalography(editorPath(created.data.id));
    } catch (cause) {
      showToast(cause instanceof HttpRequestError ? cause.message : "Não foi possível gerar o número do relatório.");
    } finally {
      setBusy(false);
    }
  }

  function patchForm(change: Partial<ReportFormState>) {
    setForm((current) => ({ ...current, ...change }));
  }

  async function chooseImage(slot: SlotKey, file: File | undefined) {
    if (!file || !writable) return;
    if (!file.type.startsWith("image/")) {
      showToast("Selecione um arquivo de imagem.");
      return;
    }
    if (file.type !== "image/jpeg" && file.type !== "image/png") {
      showToast("A API aceita apenas JPEG ou PNG.");
      return;
    }
    try {
      const image = await loadImage(file);
      setCrop({ slot, image, fileName: file.name });
    } catch (cause) {
      showToast(cause instanceof Error ? cause.message : "Não foi possível abrir essa imagem.");
    }
  }

  async function save() {
    if (!writable || busy) return;
    setBusy(true);
    try {
      let currentId = reportId;
      let currentEtag = etag;
      const payload = toWritePayload(form);
      if (!currentId) {
        const key = idempotencyKey(sessionStorage, "metalography:create-key", () => crypto.randomUUID());
        const created = await createReport(payload, key);
        clearKey(sessionStorage, "metalography:create-key");
        currentId = created.data.id;
        currentEtag = created.etag;
        setNumber(created.data.report_number);
      } else if (currentEtag) {
        const updated = await updateReport(currentId, payload, currentEtag);
        currentEtag = updated.etag;
      } else {
        showToast("Recarregue o relatório antes de salvar. A versão do servidor não foi confirmada.");
        return;
      }
      for (const slot of ["original", "measured"] as const) {
        const pending = slots[slot].pending;
        if (!pending || !currentEtag) continue;
        const stored = await putImage(currentId, slot, pending, pending.type || "image/jpeg", currentEtag);
        currentEtag = stored.etag ?? currentEtag;
      }
      setEtag(currentEtag);
      setSavedForm(form);
      setSlots((current) => ({
        original: { ...current.original, pending: null },
        measured: { ...current.measured, pending: null },
      }));
      showToast("Relatório salvo. Ele já está disponível na tela inicial.");
      if (currentId !== reportId) navigateMetalography(editorPath(currentId));
    } catch (cause) {
      if (cause instanceof HttpRequestError && cause.status === 412) {
        showToast("O relatório foi alterado por outra pessoa. Recarregue a versão do servidor antes de salvar de novo. O que você digitou permanece nesta tela.");
      } else {
        showToast(cause instanceof HttpRequestError ? cause.message : "Não foi possível salvar.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function downloadPdf() {
    if (!reportId || !canExport) return;
    try {
      const exported = await exportPdf(reportId);
      const url = URL.createObjectURL(exported.blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `metalografia-${number || reportId}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      showToast(cause instanceof HttpRequestError ? cause.message : "Não foi possível exportar o PDF.");
    }
  }

  async function confirmDelete() {
    if (!pendingReport?.version || actionLock.current) return;
    actionLock.current = true;
    setBusy(true);
    setDialogError("");
    try {
      const current = await getReport(pendingReport.id);
      await deleteReport(pendingReport.id, current.etag ?? `"${pendingReport.version}"`);
      setConfirm(null);
      setPendingReport(null);
      showToast("Relatório excluído permanentemente.");
      await loadList();
    } catch (cause) {
      setDialogError(cause instanceof HttpRequestError ? cause.message : "Não foi possível excluir.");
    } finally {
      actionLock.current = false;
      setBusy(false);
    }
  }

  async function confirmCopy() {
    if (!pendingReport || !canCreate || actionLock.current) return;
    actionLock.current = true;
    setBusy(true);
    try {
      const copy = copyReportForm(formFromReport(pendingReport));
      const key = idempotencyKey(sessionStorage, `metalography:copy:${pendingReport.id}`, () => crypto.randomUUID());
      const created = await createReport(toWritePayload(copy), key);
      clearKey(sessionStorage, `metalography:copy:${pendingReport.id}`);
      setConfirm(null);
      navigateMetalography(editorPath(created.data.id));
    } catch (cause) {
      showToast(cause instanceof HttpRequestError ? cause.message : "Não foi possível criar a cópia.");
    } finally {
      actionLock.current = false;
      setBusy(false);
    }
  }

  function field(id: string, label: string, value: string, onChange: (value: string) => void, placeholder: string, readOnlyField = false) {
    return (
      <div className="field-card">
        <label className="label" htmlFor={id}>{label}</label>
        <input id={id} className="entry" type="text" placeholder={placeholder} value={value} readOnly={readOnlyField || !writable} aria-readonly={readOnlyField || !writable} onChange={(event) => onChange(event.target.value)} />
      </div>
    );
  }

  function imageCard(slot: SlotKey, title: string, caption: string, placeholder: string, detail: string) {
    const view = slots[slot];
    return (
      <article className="image-card">
        <div className="image-title">{title}</div>
        <div className="image-caption">{caption}</div>
        <div className="image-frame">
          <img className="preview" alt={title} src={view.previewUrl ?? undefined} style={{ display: view.previewUrl ? "block" : "none", objectFit: "contain", background: "#fff" }} />
          <div className="image-placeholder" style={{ display: view.previewUrl ? "none" : undefined }}><strong>{placeholder}</strong>{detail}</div>
        </div>
        <div className="upload-row">
          <span className="hint">{view.fileName}</span>
          <div className="upload-actions">
            <label htmlFor={`${slot}-file`}>Selecionar imagem</label>
            <input id={`${slot}-file`} type="file" accept="image/*" disabled={!writable || !reportId} onChange={(event) => { void chooseImage(slot, event.target.files?.[0]); event.target.value = ""; }} />
            <button className="adjust-btn" type="button" disabled={!writable || !view.previewUrl} onClick={() => {
              if (!view.previewUrl) return;
              const image = new Image();
              image.onload = () => setCrop({ slot, image, fileName: view.fileName });
              image.src = view.previewUrl;
            }}>Recortar / centralizar</button>
          </div>
        </div>
      </article>
    );
  }

  const countLabel = filtersActive ? `${visible.length} de ${total} ${total === 1 ? "relatório" : "relatórios"}` : `${total} ${total === 1 ? "relatório" : "relatórios"}`;

  function printSheet() {
    const sheet = hostRef.current?.querySelector("main.sheet");
    if (!(sheet instanceof HTMLElement)) return;
    const stylesheet = metallographicPrintStylesheet(
      readMetallographicStylesheet(),
      font400Url,
      font700Url,
    );
    if (!stylesheet.includes(".dashboard-metalography")) {
      setToast("Não foi possível preparar a folha para impressão.");
      return;
    }
    const opened = printIsolatedMetallographicSheet(
      sheet,
      stylesheet,
      (html, title) => printDelpiDocumentHtml(html, { iframeTitle: title }),
    );
    if (!opened) setToast("Não foi possível abrir a impressão.");
  }

  return (
    <div ref={bindHost} className={editing ? "dashboard-metalography dashboard-page editor-active" : "dashboard-metalography dashboard-page"}>
      <section className="home-screen" aria-label="Tela inicial de relatórios">
        <div className="home-shell">
          <header className="home-header">
            <div className="home-brand">
              <div className="home-logo-wrap"><DelpiReportLogo id="home-logo" alt="DELPI" /></div>
              <div className="home-brand-copy"><div className="home-kicker">ENGENHARIA · QUALIDADE</div><h1>Análises metalográficas</h1><p>Relatórios de crimpagem de terminais</p></div>
            </div>
            <button className="home-new" type="button" disabled={!canCreate || busy || forbidden} onClick={() => { void createBlank(); }}><span className="home-plus"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg></span><span>Novo Relatório</span></button>
          </header>
          <section className="home-hero"><div><span className="home-eyebrow">CONTROLE DE ANÁLISES</span><h2>Seus relatórios em um só lugar</h2><p>Abra uma análise salva para continuar editando ou inicie um novo relatório.</p></div><div className="home-stat"><strong id="home-count">{total}</strong><span>relatórios salvos</span></div></section>
          <section className="reports-panel" aria-labelledby="reports-heading">
            <div className="reports-panel-head"><div><h2 id="reports-heading">Relatórios salvos</h2><p>Acesse e edite as análises registradas no Metalografia DELPI.</p></div><span id="report-count" className="report-count">{countLabel}</span></div>
            <section id="report-filters" className="report-filter-box" aria-label="Filtros dos relatórios salvos">
              <div className="report-filter-top"><div className="report-filter-title"><strong>Filtrar relatórios</strong><span>Combine período e identificação da amostra; os critérios preenchidos são aplicados juntos. Se a data do relatório estiver vazia, usa-se a data de criação.</span></div><button id="clear-report-filters" className="filter-clear" type="button" disabled={!filtersActive} onClick={() => setFilters(EMPTY_REPORT_FILTERS)}>Limpar filtros</button></div>
              <div className="report-filter-grid">
                <label className="filter-field"><span>Data inicial</span><input id="filter-date-from" type="date" aria-label="Data inicial do período" value={filters.from} onChange={(event) => setFilters({ ...filters, from: event.target.value })} /></label>
                <label className="filter-field"><span>Data final</span><input id="filter-date-to" type="date" aria-label="Data final do período" value={filters.to} onChange={(event) => setFilters({ ...filters, to: event.target.value })} /></label>
                <label className="filter-field"><span>Terminal</span><input type="search" placeholder="Código DELPI" value={filters.terminal} onChange={(event) => setFilters({ ...filters, terminal: event.target.value })} /></label>
                <label className="filter-field"><span>Part number do terminal</span><input type="search" placeholder="Número da peça" value={filters.part} onChange={(event) => setFilters({ ...filters, part: event.target.value })} /></label>
                <label className="filter-field"><span>Produto ou chicote</span><input type="search" placeholder="Código / revisão" value={filters.product} onChange={(event) => setFilters({ ...filters, product: event.target.value })} /></label>
                <label className="filter-field"><span>Cabo</span><input type="search" placeholder="Código / descrição" value={filters.cable} onChange={(event) => setFilters({ ...filters, cable: event.target.value })} /></label>
                <label className="filter-field"><span>Seção do condutor</span><input type="search" placeholder="mm² / AWG" value={filters.section} onChange={(event) => setFilters({ ...filters, section: event.target.value })} /></label>
                <label className="filter-field"><span>Aplicador / ferramenta</span><input type="search" placeholder="Identificação" value={filters.applicator} onChange={(event) => setFilters({ ...filters, applicator: event.target.value })} /></label>
                <label className="filter-field"><span>Prensa / equipamento</span><input type="search" placeholder="Identificação" value={filters.press} onChange={(event) => setFilters({ ...filters, press: event.target.value })} /></label>
                <label className="filter-field"><span>Lote / ordem de produção</span><input type="search" placeholder="Número do lote" value={filters.lot} onChange={(event) => setFilters({ ...filters, lot: event.target.value })} /></label>
                <label className="filter-field"><span>Amostra analisada</span><input type="search" placeholder="Identificação da amostra" value={filters.sample} onChange={(event) => setFilters({ ...filters, sample: event.target.value })} /></label>
              </div>
              <p id="filter-result-count" className="filter-note" aria-live="polite">{filtersActive ? `Encontrados ${visible.length} de ${total} relatórios. Os critérios preenchidos são combinados.` : `${countLabel}. Preencha um ou mais campos para filtrar.`}</p>
            </section>
            <div id="reports-list" className="reports-list" aria-live="polite">
              {visible.map((report) => {
                const result = report.conclusion.result;
                const badge = result === "conforming" ? "is-conforme" : result === "nonconforming" ? "is-nao-conforme" : "is-pending";
                const label = result === "conforming" ? "CONFORME" : result === "nonconforming" ? "NÃO CONFORME" : "RESULTADO PENDENTE";
                return (
                  <article className="saved-report" key={report.id}>
                    <div className="saved-leading"><div className="saved-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h8l5 5v13H6zM14 3v6h5M9 13h7M9 17h7" /></svg></div><div className="saved-heading"><strong>{report.report_number || "Relatório sem número"}</strong><span>{report.report_date ? `Data: ${report.report_date.split("-").reverse().join("/")}` : `Salvo em ${formatStamp(report.updated_at)}`}</span></div></div>
                    <div className="saved-details"><strong>{report.sample.terminal_code || "Terminal não identificado"}</strong><span>{`Part number: ${report.sample.terminal_part_number || "—"} · Produto: ${report.sample.product_harness || "—"}`}</span></div>
                    <div className="saved-status"><span className={`result-badge ${badge}`}>{label}</span><small>{`Atualizado ${formatStamp(report.updated_at)}`}</small></div>
                    <div className="saved-actions">
                      <button type="button" className="report-open" onClick={() => navigateMetalography(editorPath(report.id, readOnly || !canEdit))}>Abrir / editar</button>
                      <button type="button" className="report-copy" disabled={!canCreate} aria-label={`Criar cópia de ${report.report_number}`} onClick={() => { setPendingReport(report); setConfirm("copy"); }}>Criar cópia</button>
                      <button type="button" className="report-delete" disabled={!canDelete} aria-label={`Excluir ${report.report_number}`} onClick={() => { setPendingReport(report); setDialogError(""); setConfirm("delete"); }}>Excluir</button>
                    </div>
                  </article>
                );
              })}
            </div>
            <div id="empty-state" className="empty-state" hidden={visible.length > 0}>
              <div className="empty-icon"><svg viewBox="0 0 48 48" aria-hidden="true"><path d="M14 6h14l9 9v27H14zM28 6v10h9M20 25h11M20 31h11M20 37h7" /></svg></div>
              <strong>{total === 0 ? "Nenhum relatório salvo ainda" : "Nenhum relatório encontrado"}</strong>
              <span>{total === 0 ? "Quando você salvar uma análise, ela aparecerá nesta lista." : "Ajuste os critérios ou clique em “Limpar filtros” para ver todos os relatórios."}</span>
            </div>
            <div id="storage-hint" className={hintError ? "storage-hint error" : "storage-hint"} role="status">{hint}</div>
          </section>
          <footer className="home-footer"><span>DELPI · Relatórios de análise metalográfica</span><span>Os relatórios ficam armazenados no servidor do Minha DELPI.</span></footer>
        </div>
      </section>
      <div className="toolbar">
        <div className="toolbar-note"><strong>Relatório editável — A4.</strong> Salve para continuar a análise depois; os relatórios salvos ficam disponíveis na tela inicial.</div>
        <div className="actions">
          <button className="secondary toolbar-back" type="button" title="Voltar à página inicial" onClick={() => { if (dirty) setConfirm("leave"); else navigateMetalography(listPath()); }}>← Página inicial</button>
          <button id="save-report" className="save-button" type="button" disabled={!writable || busy} onClick={() => { void save(); }}>{busy ? "Salvando…" : "Salvar relatório"}</button>
          <button id="export-pdf" className="primary" type="button" disabled={!canExport || !reportId} onClick={() => { void downloadPdf(); }}>Exportar PDF</button>
          <button className="secondary" type="button" onClick={printSheet}>Imprimir</button>
        </div>
      </div>
      <main className="sheet" aria-label="Relatório de análise metalográfica de crimpagem">
        <header className="report-head">
          <div className="logo-wrap"><DelpiReportLogo alt="Delpi — conexões elétricas" /></div>
          <div className="title-block"><h1>ANÁLISE METALOGRÁFICA<br />DE CRIMPAGEM</h1><p>Avaliação da seção transversal do terminal</p></div>
          <div className="meta-card">
            <div className="meta-field report-no"><label className="label" htmlFor="report-number">Relatório nº</label><input id="report-number" className="entry" type="text" placeholder="000001" value={number} readOnly aria-readonly="true" title="Número sequencial gerado automaticamente" /></div>
            <div className="meta-field"><label className="label" htmlFor="report-date">Data</label><input id="report-date" className="entry" type="text" placeholder="DD/MM/AAAA" value={form.reportDate} readOnly={!writable} onChange={(event) => patchForm({ reportDate: event.target.value })} /></div>
            <div className="meta-field"><label className="label" htmlFor="report-rev">Rev.</label><input id="report-rev" className="entry" type="text" placeholder="—" value={form.revision === "00" ? "" : form.revision} readOnly={!writable} onChange={(event) => patchForm({ revision: event.target.value || "00" })} /></div>
          </div>
        </header>
        <section className="sec">
          <div className="sec-heading"><span className="sec-number">01</span><h2>Identificação da amostra</h2><p className="sub">Preencha os dados do terminal, cabo e processo avaliados.</p></div>
          <div className="id-grid">
            {field("terminal", "Terminal", form.sample.terminal_code, (value) => patchForm({ sample: { ...form.sample, terminal_code: value } }), "Código DELPI")}
            {field("terminal-pn", "Part number do terminal", form.sample.terminal_part_number, (value) => patchForm({ sample: { ...form.sample, terminal_part_number: value } }), "Número da peça")}
            {field("product", "Produto ou chicote", form.sample.product_harness, (value) => patchForm({ sample: { ...form.sample, product_harness: value } }), "Código / revisão")}
            {field("cable", "Cabo", form.sample.cable, (value) => patchForm({ sample: { ...form.sample, cable: value } }), "Código DELPI / descrição")}
            {field("section", "Seção do condutor", form.sample.conductor_section, (value) => patchForm({ sample: { ...form.sample, conductor_section: value } }), "mm² / AWG")}
            {field("applicator", "Aplicador / ferramenta", form.sample.applicator_tool, (value) => patchForm({ sample: { ...form.sample, applicator_tool: value } }), "Identificação")}
            {field("press", "Prensa / equipamento", form.sample.press_equipment, (value) => patchForm({ sample: { ...form.sample, press_equipment: value } }), "Identificação")}
            {field("lot", "Lote / ordem de produção", form.sample.batch_production_order, (value) => patchForm({ sample: { ...form.sample, batch_production_order: value } }), "Código / nº")}
            {field("sample", "Amostra analisada", form.sample.sample_identification, (value) => patchForm({ sample: { ...form.sample, sample_identification: value } }), "Nº da amostra / total")}
          </div>
        </section>
        <section className="sec">
          <div className="sec-heading"><span className="sec-number">02</span><h2>Análise da seção transversal</h2><p className="sub">Registre a micrografia original e a seção com análise visual.</p></div>
          <div className="image-grid">
            {imageCard("original", "Micrografia original", "Imagem óptica sem marcações", "INSERIR MICROGRAFIA", "Selecione a imagem obtida no microscópio")}
            {imageCard("measured", "Seção com medições", "Área avaliada e dimensões indicadas pelo software", "INSERIR IMAGEM DAS MEDIÇÕES", "Selecione a imagem com áreas e cotas identificadas")}
          </div>
        </section>
        <section className="sec">
          <div className="sec-heading"><span className="sec-number">03</span><h2>Resultados da medição</h2><p className="sub">Registre o critério aplicável e o valor obtido para cada característica.</p></div>
          <div className="measure-layout">
            <div className="measure-table" role="table" aria-label="Resultados de medição">
              <div className="th" role="columnheader">Parâmetro</div><div className="th" role="columnheader">Critério / tolerância</div><div className="th" role="columnheader">Valor medido</div>
              {([
                ["Altura de crimpagem (CH) [mm]", "crimp_height_ch", "crit-ch", "val-ch", "Critério altura de crimpagem", "Valor altura de crimpagem", "mín. – máx.", "mm"],
                ["Largura de crimpagem (CB) [mm]", "crimp_width_cb", "crit-cb", "val-cb", "Critério largura de crimpagem", "Valor largura de crimpagem", "mín. – máx.", "mm"],
                ["Porcentagem de vazios (AV) [%]", "void_area_av", "crit-av", "val-av", "Critério porcentagem de vazios", "Valor porcentagem de vazios", "máx. %", "%"],
                ["Altura da rebarba esquerda (GH-E) [mm]", "left_burr_gh_e", "crit-ghe", "val-ghe", "Critério altura da rebarba esquerda", "Valor altura da rebarba esquerda", "máx. mm", "mm"],
                ["Altura da rebarba direita (GH-D) [mm]", "right_burr_gh_d", "crit-ghd", "val-ghd", "Critério altura da rebarba direita", "Valor altura da rebarba direita", "máx. mm", "mm"],
              ] as const).map(([label, key, critId, valId, critLabel, valLabel, critPlaceholder, valPlaceholder]) => (
                <Fragment key={key}>
                  <div className="cell param">{label}</div>
                  <div className="cell"><input id={critId} aria-label={critLabel} className="entry" type="text" placeholder={critPlaceholder} value={form.measurements[key].criterion} readOnly={!writable} onChange={(event) => patchForm({ measurements: { ...form.measurements, [key]: { ...form.measurements[key], criterion: event.target.value } } })} /></div>
                  <div className="cell"><input id={valId} aria-label={valLabel} className="entry" type="text" placeholder={valPlaceholder} value={form.measurements[key].measured} readOnly={!writable} onChange={(event) => patchForm({ measurements: { ...form.measurements, [key]: { ...form.measurements[key], measured: event.target.value } } })} /></div>
                </Fragment>
              ))}
            </div>
            <figure className="diagram-card"><img src={diagramUrl} alt="Esquema genérico da seção do terminal com cotas CH, CB, AV, GH-E e GH-D" /><figcaption className="diagram-caption">Esquema de referência das cotas</figcaption></figure>
          </div>
        </section>
        <section className="sec">
          <div className="sec-heading"><span className="sec-number">04</span><h2>Conclusão técnica</h2><p className="sub">Selecione o resultado final e registre observações ou desvios.</p></div>
          <div className="verdict-card">
            <div><div className="verdict-title">Resultado geral</div><div className="choices">
              <label className="choice"><input type="radio" name="result" value="conforme" checked={form.conclusionResult === "conforming"} disabled={!writable} onChange={() => patchForm({ conclusionResult: "conforming" })} /><span>Conforme</span></label>
              <label className="choice"><input type="radio" name="result" value="nao-conforme" checked={form.conclusionResult === "nonconforming"} disabled={!writable} onChange={() => patchForm({ conclusionResult: "nonconforming" })} /><span>Não conforme</span></label>
            </div></div>
            <div><div className="obs-label">Observações / desvios</div><textarea id="observations" aria-label="Observações ou desvios" placeholder="Registre observações relevantes, desvios e/ou justificativas do resultado." value={form.conclusionNotes} readOnly={!writable} onChange={(event) => patchForm({ conclusionNotes: event.target.value })} /></div>
          </div>
        </section>
        <section className="sec">
          <div className="sec-heading"><span className="sec-number">05</span><h2>Responsável pela análise</h2></div>
          <div className="analyst-card"><label className="label" htmlFor="analyst">Análise realizada por</label><input id="analyst" className="entry" type="text" placeholder="Nome do responsável pela análise" value={form.analystName} readOnly={!writable} onChange={(event) => patchForm({ analystName: event.target.value })} /></div>
        </section>
        <footer className="footer"><div><strong>DELPI&nbsp;&nbsp;|&nbsp;&nbsp;RELATÓRIO DE ANÁLISE METALOGRÁFICA</strong><small>Resultados referentes às amostras descritas neste documento.</small></div><div className="page">1 / 1</div></footer>
      </main>
      <CropDialog
        open={Boolean(crop)}
        title={crop ? `Ajustar: ${crop.slot === "original" ? "Micrografia original" : "Seção com medições"}` : "Ajustar imagem"}
        image={crop?.image ?? null}
        box={overlay}
        onCancel={() => setCrop(null)}
        onApply={(file, previewUrl) => {
          if (!crop) return;
          setSlots((current) => ({ ...current, [crop.slot]: { previewUrl, fileName: crop.fileName, pending: file } }));
          setCrop(null);
        }}
      />
      <div id="app-toast" className={toast ? "app-toast show" : "app-toast"} role="status" aria-live="polite">{toast}</div>
      <div className={confirm === "leave" ? "return-home-modal open" : "return-home-modal"} style={confirm === "leave" ? overlay : undefined} aria-hidden={confirm === "leave" ? "false" : "true"} onKeyDown={stopEscape}>
        <div className="return-home-dialog" role="dialog" aria-modal="true" aria-labelledby="return-home-title">
          <h2 id="return-home-title">Voltar à página inicial?</h2>
          <p id="return-home-message">As alterações que ainda não foram salvas neste relatório serão perdidas. Os relatórios já salvos continuarão disponíveis na página inicial.</p>
          <div className="return-home-actions">
            <button id="return-home-cancel" className="secondary" type="button" onClick={() => setConfirm(null)}>Continuar editando</button>
            <button className="primary" type="button" onClick={() => { setConfirm(null); navigateMetalography(listPath()); }}>Voltar à página inicial</button>
          </div>
        </div>
      </div>
      <div className={confirm === "delete" ? "return-home-modal open" : "return-home-modal"} style={confirm === "delete" ? overlay : undefined} aria-hidden={confirm === "delete" ? "false" : "true"} onKeyDown={stopEscape}>
        <div className="return-home-dialog" role="dialog" aria-modal="true" aria-labelledby="delete-report-title">
          <h2 id="delete-report-title">Excluir relatório?</h2>
          <p id="delete-report-message">{pendingReport ? `Tem certeza de que deseja excluir permanentemente o relatório nº ${pendingReport.report_number}? Os dados e as imagens serão removidos. Esta ação não pode ser desfeita.` : "Esta ação não pode ser desfeita."}</p>
          <p id="delete-report-error" className="delete-report-error" role="alert" hidden={!dialogError}>{dialogError}</p>
          <div className="return-home-actions">
            <button id="delete-report-cancel" className="secondary" type="button" onClick={() => setConfirm(null)}>Cancelar</button>
            <button id="delete-report-confirm" className="delete-confirm-button" type="button" disabled={busy} onClick={() => { void confirmDelete(); }}>{busy ? "Excluindo…" : "Excluir permanentemente"}</button>
          </div>
        </div>
      </div>
      <div className={confirm === "copy" ? "return-home-modal open" : "return-home-modal"} style={confirm === "copy" ? overlay : undefined} aria-hidden={confirm === "copy" ? "false" : "true"} onKeyDown={stopEscape}>
        <div className="return-home-dialog" role="dialog" aria-modal="true" aria-labelledby="copy-report-title">
          <h2 id="copy-report-title">Criar cópia do relatório?</h2>
          <p id="copy-report-message">{pendingReport ? `Criar uma cópia do relatório nº ${pendingReport.report_number}? Os dados do terminal, processo e critérios serão copiados. O número original será substituído por uma numeração automática e a data será a do dia da cópia. Lote, amostra, medições, conclusão, observações, responsável e imagens serão limpos para a nova análise. O original permanecerá inalterado.` : "Será aberto um novo rascunho com os dados reutilizáveis deste relatório. O original permanecerá inalterado."}</p>
          <div className="return-home-actions">
            <button id="copy-report-cancel" className="secondary" type="button" onClick={() => setConfirm(null)}>Cancelar</button>
            <button id="copy-report-confirm" className="primary" type="button" disabled={busy} onClick={() => { void confirmCopy(); }}>{busy ? "Criando cópia…" : "Criar cópia"}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
