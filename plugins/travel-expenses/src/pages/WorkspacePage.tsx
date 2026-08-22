import { useCallback, useEffect, useMemo, useRef, useState, type RefObject } from "react";
import { ActionButton, FilePreviewModal } from "@delpi/plugin-ui/index";
import { Camera, FilePlus2 } from "lucide-react";

import { TravelReportHero } from "../components/TravelReportHero";
import { TravelPixSection } from "../components/TravelPixSection";

import {
  addExpense,
  deleteExpense,
  deleteReceipt,
  fetchReceiptBlob,
  getReport,
  listAudit,
  listCategories,
  updateExpense,
  updateReport,
  uploadReceipt,
  type AuditEvent,
  type Category,
  type Expense,
  type Receipt,
  type ReportDetail,
  type TravelAccess,
} from "../api/travelExpensesApi";
import { CATEGORY_LABELS, formatBrl, formatDate } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { toInputDate } from "../utils/dates";
import {
  TravelAttachmentStrip,
  TravelDrawer,
  TravelFileDropzone,
  TravelFormActions,
  TravelFormGrid,
  TravelPageNotices,
  TravelSectionCard,
  TravelTimeline,
} from "../ui/travelUi";

const ACCEPT = "image/jpeg,image/png,image/webp,application/pdf";

type HeaderDraft = {
  destination: string;
  purpose: string;
  periodStart: string;
  periodEnd: string;
  costCenterCode: string;
  costCenterLabel: string;
};

function headerFromReport(report: ReportDetail): HeaderDraft {
  return {
    destination: report.destination || "",
    purpose: report.purpose || "",
    periodStart: toInputDate(report.periodStart),
    periodEnd: toInputDate(report.periodEnd),
    costCenterCode: report.costCenterCode || "",
    costCenterLabel: report.costCenterLabel || "",
  };
}

const AUDIT_TIMELINE_SKIP = new Set(["updated"]);

const AUDIT_LABELS: Record<string, string> = {
  created: "Prestação criada",
  updated: "Cabeçalho atualizado",
  expense_added: "Despesa incluída",
  receipt_added: "Cupom anexado",
  pix_added: "Chave PIX para ressarcimento informada",
};

export function WorkspacePage({
  reportId,
  access,
}: {
  reportId: string;
  access: TravelAccess;
}) {
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [audit, setAudit] = useState<AuditEvent[]>([]);
  const [header, setHeader] = useState<HeaderDraft | null>(null);
  const [savedHeader, setSavedHeader] = useState<HeaderDraft | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editing, setEditing] = useState<Expense | null>(null);
  const [preview, setPreview] = useState<{ expense: Expense; receipt: Receipt } | null>(null);
  const cameraRef = useRef<HTMLInputElement>(null);

  const reload = useCallback(async () => {
    const [detail, cats, events] = await Promise.all([
      getReport(reportId),
      listCategories(),
      listAudit(reportId),
    ]);
    setReport(detail);
    setCategories(cats);
    setAudit(events);
    const next = headerFromReport(detail);
    setHeader(next);
    setSavedHeader(next);
  }, [reportId]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    reload()
      .catch((err: Error) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reload]);

  const editable = report?.status === "draft" && access.canWrite;
  const missingIds = new Set(
    (report?.completeness.issues || [])
      .filter((issue) => issue.expenseId)
      .map((issue) => issue.expenseId as string),
  );

  async function saveHeader() {
    if (!header || !editable) return;
    setSaving(true);
    try {
      const updated = await updateReport(reportId, {
        destination: header.destination,
        purpose: header.purpose,
        periodStart: header.periodStart || null,
        periodEnd: header.periodEnd || null,
        costCenterCode: header.costCenterCode || null,
        costCenterLabel: header.costCenterLabel || null,
      });
      setReport(updated);
      const next = headerFromReport(updated);
      setHeader(next);
      setSavedHeader(next);
      setSuccess("Cabeçalho salvo.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível salvar.");
      throw err;
    } finally {
      setSaving(false);
    }
  }

  function cancelHeaderEdit() {
    if (savedHeader) setHeader(savedHeader);
  }

  function openNewExpense() {
    setEditing(null);
    setDrawerOpen(true);
  }

  function openExpense(expense: Expense) {
    setEditing(expense);
    setDrawerOpen(true);
  }

  async function onUpload(expense: Expense, files: File[]) {
    try {
      for (const file of files) {
        await uploadReceipt(reportId, expense.id, file);
      }
      await reload();
      setSuccess("Cupom anexado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível anexar o cupom.");
    }
  }

  if (loading || !report || !header) {
    return (
      <div className="te-page-stack te-page-stack--workspace">
        <p className="te-muted">Carregando prestação…</p>
      </div>
    );
  }

  const timelineEvents = audit.filter((event) => !AUDIT_TIMELINE_SKIP.has(event.eventType));

  return (
    <div className="te-page-stack te-page-stack--workspace">
      <TravelReportHero
        report={report}
        header={header}
        editable={editable}
        saving={saving}
        onHeaderChange={setHeader}
        onSaveHeader={() => saveHeader()}
        onCancelHeader={cancelHeaderEdit}
      />
      <TravelPageNotices
        error={error}
        success={success}
        onDismissError={() => setError(null)}
        onDismissSuccess={() => setSuccess(null)}
      />

      <TravelSectionCard
        title="Despesas"
        actions={
          editable ? (
            <ActionButton variant="primary" onClick={openNewExpense}>
              <FilePlus2 size={16} /> Nova despesa
            </ActionButton>
          ) : null
        }
      >
        <div className="te-expense-list">
          {report.expenses.length === 0 ? (
            <p className="te-muted">Nenhuma despesa lançada ainda.</p>
          ) : (
            report.expenses.map((expense) => {
              const alert = missingIds.has(expense.id) || expense.receipts.length === 0;
              return (
                <button
                  key={expense.id}
                  type="button"
                  className={alert ? "te-expense-row te-expense-row--alert" : "te-expense-row"}
                  onClick={() => openExpense(expense)}
                >
                  <span className="te-expense-row__date">{formatDate(expense.expenseDate)}</span>
                  <span className="te-expense-meta">
                    <strong>{CATEGORY_LABELS[expense.categoryId] || expense.categoryId}</strong>
                    <small>{expense.merchant || "Sem estabelecimento"}</small>
                  </span>
                  <span className="te-amount">{formatBrl(expense.amountBrl)}</span>
                  <span className="te-expense-row__receipt te-muted">
                    {expense.receipts.length ? `${expense.receipts.length} cupom` : "sem cupom"}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </TravelSectionCard>

      <TravelPixSection
        report={report}
        editable={editable}
        onChanged={reload}
        onError={setError}
        onSuccess={setSuccess}
      />

      <TravelSectionCard title="Linha do tempo">
        <div className="te-timeline-scroll">
          <TravelTimeline
            layout="linear"
            aria-label="Auditoria da prestação"
            items={timelineEvents.map((event) => ({
              id: event.id,
              title: AUDIT_LABELS[event.eventType] || event.eventType,
              occurredAt: event.createdAt,
              timeLabel: event.createdAt ? formatDate(event.createdAt) : "",
              detail: event.actorName || undefined,
            }))}
            emptyMessage="Nenhum evento registrado."
          />
        </div>
      </TravelSectionCard>

      <ExpenseDrawer
        open={drawerOpen}
        report={report}
        expense={editing}
        categories={categories}
        editable={editable}
        cameraRef={cameraRef}
        onClose={() => setDrawerOpen(false)}
        onSaved={async () => {
          await reload();
          setDrawerOpen(false);
          setEditing(null);
          setSuccess("Despesa salva.");
        }}
        onDeleted={async () => {
          await reload();
          setDrawerOpen(false);
          setSuccess("Despesa excluída.");
        }}
        onError={setError}
        onUpload={onUpload}
        onPreview={(receipt) => editing && setPreview({ expense: editing, receipt })}
        onRemoveReceipt={async (receipt) => {
          if (!editing) return;
          try {
            await deleteReceipt(reportId, editing.id, receipt.id);
            await reload();
          } catch (err) {
            setError(err instanceof Error ? err.message : "Não foi possível remover o cupom.");
          }
        }}
      />

      <FilePreviewModal
        open={Boolean(preview)}
        title={preview?.receipt.originalName || "Cupom"}
        onClose={() => setPreview(null)}
        source={
          preview
            ? () => fetchReceiptBlob(reportId, preview.expense.id, preview.receipt.id)
            : null
        }
        mimeType={preview?.receipt.mimeType}
        fileName={preview?.receipt.originalName}
        portalScopeClassName="dashboard-travel-expenses"
      />
    </div>
  );
}

function ExpenseDrawer({
  open,
  report,
  expense,
  categories,
  editable,
  cameraRef,
  onClose,
  onSaved,
  onDeleted,
  onError,
  onUpload,
  onPreview,
  onRemoveReceipt,
}: {
  open: boolean;
  report: ReportDetail;
  expense: Expense | null;
  categories: Category[];
  editable: boolean;
  cameraRef: RefObject<HTMLInputElement | null>;
  onClose: () => void;
  onSaved: (expense: Expense) => Promise<void>;
  onDeleted: () => Promise<void>;
  onError: (message: string) => void;
  onUpload: (expense: Expense, files: File[]) => Promise<void>;
  onPreview: (receipt: Receipt) => void;
  onRemoveReceipt: (receipt: Receipt) => Promise<void>;
}) {
  const [expenseDate, setExpenseDate] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [merchant, setMerchant] = useState("");
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const current = useMemo(
    () => (expense ? report.expenses.find((item) => item.id === expense.id) || expense : null),
    [expense, report.expenses],
  );

  useEffect(() => {
    setExpenseDate(toInputDate(expense?.expenseDate) || toInputDate(report.periodStart));
    setCategoryId(expense?.categoryId || categories[0]?.id || "other");
    setMerchant(expense?.merchant || "");
    setAmount(expense ? String(expense.amountBrl) : "");
    setNotes(expense?.notes || "");
  }, [expense, categories, report.periodStart, open]);

  async function save() {
    if (!editable) return;
    setBusy(true);
    try {
      const payload = {
        expenseDate,
        categoryId,
        merchant,
        amountBrl: Number(amount.replace(",", ".") || 0),
        notes,
      };
      const saved = expense
        ? await updateExpense(report.id, expense.id, payload)
        : await addExpense(report.id, payload);
      await onSaved(saved);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Não foi possível salvar a despesa.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <TravelDrawer
      open={open}
      title={expense ? "Editar despesa" : "Nova despesa"}
      description={helpTooltips.receipt}
      onClose={onClose}
      footer={
        <TravelFormActions>
          {expense && editable ? (
            <ActionButton
              variant="ghost"
              onClick={() => {
                if (!window.confirm("Excluir esta despesa e os cupons?")) return;
                void deleteExpense(report.id, expense.id)
                  .then(onDeleted)
                  .catch((err: Error) => onError(err.message));
              }}
            >
              Excluir
            </ActionButton>
          ) : null}
          <ActionButton variant="primary" onClick={() => void save()} disabled={!editable || busy}>
            Salvar despesa
          </ActionButton>
        </TravelFormActions>
      }
    >
      <TravelFormGrid>
        <label className="te-field">
          Data
          <input type="date" value={expenseDate} disabled={!editable} onChange={(event) => setExpenseDate(event.target.value)} />
        </label>
        <label className="te-field">
          Categoria
          <select value={categoryId} disabled={!editable} onChange={(event) => setCategoryId(event.target.value)}>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.label}
              </option>
            ))}
          </select>
        </label>
        <label className="te-field">
          Estabelecimento
          <input value={merchant} disabled={!editable} onChange={(event) => setMerchant(event.target.value)} />
        </label>
        <label className="te-field">
          Valor (BRL)
          <input value={amount} disabled={!editable} inputMode="decimal" onChange={(event) => setAmount(event.target.value)} />
        </label>
        <label className="te-field te-field--wide">
          Nota
          <textarea value={notes} disabled={!editable} onChange={(event) => setNotes(event.target.value)} rows={3} />
        </label>
      </TravelFormGrid>

      {current ? (
        <>
          <TravelAttachmentStrip
            heading="Cupons"
            mode={editable ? "manage" : "preview"}
            items={current.receipts.map((receipt) => ({
              id: receipt.id,
              fileName: receipt.originalName,
              contentType: receipt.mimeType,
            }))}
            onOpen={(item) => {
              const receipt = current.receipts.find((row) => row.id === item.id);
              if (receipt) onPreview(receipt);
            }}
            onRemove={(item) => {
              const receipt = current.receipts.find((row) => row.id === item.id);
              if (receipt) void onRemoveReceipt(receipt);
            }}
          />
          {editable ? (
            <div className="te-receipt-actions">
              <input
                ref={cameraRef}
                className="te-camera-input"
                type="file"
                accept="image/*"
                capture="environment"
                onChange={(event) => {
                  const files = Array.from(event.target.files || []);
                  event.target.value = "";
                  if (files.length) void onUpload(current, files);
                }}
              />
              <ActionButton variant="ghost" onClick={() => cameraRef.current?.click()}>
                <Camera size={16} /> Tirar foto
              </ActionButton>
              <TravelFileDropzone
                accept={ACCEPT}
                multiple
                onFilesSelected={(files) => void onUpload(current, files)}
                ariaLabel="Anexar cupom da galeria"
              />
            </div>
          ) : null}
        </>
      ) : (
        <p className="te-muted">Salve a despesa para anexar o cupom.</p>
      )}
    </TravelDrawer>
  );
}
