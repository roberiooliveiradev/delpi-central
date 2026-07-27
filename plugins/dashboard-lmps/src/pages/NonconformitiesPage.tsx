import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  ConfirmModalPanel,
  HelpTooltip,
  useConfirmDialogController,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";
import { Pencil, Plus, Trash2 } from "lucide-react";

import {
  createLmpNonconformity,
  deleteLmpNonconformity,
  fetchLmpNonconformities,
  updateLmpNonconformity,
} from "../api/lmpNonconformityApi";
import { DataTableSection } from "../components/DataTableSection";
import {
  FilterInputField,
  FilterSelectField,
  FiltersRow,
} from "../components/dashboardFiltersUi";
import { LmpsNav } from "../components/LmpsNav";
import type { DataTableColumn } from "../components/dataTableUi";
import {
  FormActions,
  HostContainedDialog,
  HostContainedFill,
  LMPS_CONFIRM_CLASSES,
  NativeTextField,
  SectionCard,
  SelectField,
  StatusBadge,
  TextAreaField,
  TextField,
} from "../components/ncUi";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  LmpNcStatus,
  LmpNonconformity,
  LmpNonconformityPayload,
} from "../types/lmpNonconformity";
import {
  LMP_NC_STATUS_OPTIONS,
  lmpNcStatusLabel,
} from "../types/lmpNonconformity";
import { readLmpsFilters } from "../utils/filterUrl";

const NC_HELP = LMPS_HELP_TOOLTIPS.nonconformities;

type Props = {
  pathname: string;
  canWrite?: boolean;
};

type FormState = {
  registered_at: string;
  status: LmpNcStatus;
  sale_number: string;
  branch_code: string;
  material_code: string;
  supplier_name: string;
  purchase_order: string;
  invoice_number: string;
  qty_received: string;
  qty_accepted: string;
  qty_rejected: string;
  defect_description: string;
  corrective_actions: string;
  technical_opinion: string;
  product_codes: string;
};

function toLocalDateTimeInput(iso: string | undefined): string {
  if (!iso) {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  }
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso.slice(0, 16);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalDateTimeInput(value: string): string {
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toISOString();
}

function emptyForm(): FormState {
  return {
    registered_at: toLocalDateTimeInput(undefined),
    status: "open",
    sale_number: "",
    branch_code: "",
    material_code: "",
    supplier_name: "",
    purchase_order: "",
    invoice_number: "",
    qty_received: "",
    qty_accepted: "",
    qty_rejected: "",
    defect_description: "",
    corrective_actions: "",
    technical_opinion: "",
    product_codes: "",
  };
}

function recordToForm(record: LmpNonconformity): FormState {
  return {
    registered_at: toLocalDateTimeInput(record.registered_at),
    status: (record.status as LmpNcStatus) || "open",
    sale_number: record.sale_number ?? "",
    branch_code: record.branch_code ?? "",
    material_code: record.material_code ?? "",
    supplier_name: record.supplier_name ?? "",
    purchase_order: record.purchase_order ?? "",
    invoice_number: record.invoice_number ?? "",
    qty_received: record.qty_received != null ? String(record.qty_received) : "",
    qty_accepted: record.qty_accepted != null ? String(record.qty_accepted) : "",
    qty_rejected: record.qty_rejected != null ? String(record.qty_rejected) : "",
    defect_description: record.defect_description ?? "",
    corrective_actions: record.corrective_actions ?? "",
    technical_opinion: record.technical_opinion ?? "",
    product_codes: (record.product_codes ?? []).join(", "),
  };
}

function parseOptionalNumber(value: string): number | null {
  const text = value.trim();
  if (!text) return null;
  const n = Number(text.replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

function formToPayload(form: FormState): LmpNonconformityPayload {
  return {
    registered_at: fromLocalDateTimeInput(form.registered_at),
    status: form.status,
    sale_number: form.sale_number.trim() || null,
    branch_code: form.branch_code.trim() || null,
    material_code: form.material_code.trim() || null,
    supplier_name: form.supplier_name.trim() || null,
    purchase_order: form.purchase_order.trim() || null,
    invoice_number: form.invoice_number.trim() || null,
    qty_received: parseOptionalNumber(form.qty_received),
    qty_accepted: parseOptionalNumber(form.qty_accepted),
    qty_rejected: parseOptionalNumber(form.qty_rejected),
    defect_description: form.defect_description.trim() || null,
    corrective_actions: form.corrective_actions.trim() || null,
    technical_opinion: form.technical_opinion.trim() || null,
    product_codes: form.product_codes
      .split(/[,;\s]+/)
      .map((c) => c.trim())
      .filter(Boolean),
  };
}

function statusVariant(status: string): StatusBadgeVariant {
  if (status === "done") return "success";
  if (status === "in_progress") return "info";
  return "warning";
}

function formatDisplayDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function NonconformitiesPage({ pathname, canWrite = true }: Props) {
  const filterState = readLmpsFilters();
  const [items, setItems] = useState<LmpNonconformity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [branch, setBranch] = useState("");
  const [saleNumber, setSaleNumber] = useState("");
  const [materialCode, setMaterialCode] = useState("");
  const [productCode, setProductCode] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<LmpNonconformity | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<LmpNonconformity | null>(null);
  const { confirm, pending, confirmPending, cancelPending } = useConfirmDialogController();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformities({
        status: status || undefined,
        branch: branch || undefined,
        sale_number: saleNumber || undefined,
        material_code: materialCode || undefined,
        product_code: productCode || undefined,
        start_date: dateStart || undefined,
        end_date: dateEnd || undefined,
        page,
        page_size: 50,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar NCs.");
    } finally {
      setLoading(false);
    }
  }, [
    status,
    branch,
    saleNumber,
    materialCode,
    productCode,
    dateStart,
    dateEnd,
    page,
  ]);

  useEffect(() => {
    void load();
  }, [load]);

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm());
    setFormError(null);
    setFormOpen(true);
  };

  const openEdit = (record: LmpNonconformity) => {
    setEditing(record);
    setForm(recordToForm(record));
    setFormError(null);
    setFormOpen(true);
  };

  const handleSave = async () => {
    if (!form.registered_at.trim()) {
      setFormError("Informe a data/hora do registro.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const payload = formToPayload(form);
      if (editing) {
        await updateLmpNonconformity(editing.id, payload);
      } else {
        await createLmpNonconformity(payload);
      }
      setFormOpen(false);
      await load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  };

  const requestDelete = async (record: LmpNonconformity) => {
    setPendingDelete(record);
    const ok = await confirm({
      title: "Excluir não conformidade",
      message: "Excluir esta não conformidade? Esta ação não pode ser desfeita.",
      confirmLabel: "Excluir",
      variant: "danger",
    });
    setPendingDelete(null);
    if (!ok) return;
    try {
      await deleteLmpNonconformity(record.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir.");
    }
  };

  const columns = useMemo<DataTableColumn<LmpNonconformity>[]>(() => {
    const cols: DataTableColumn<LmpNonconformity>[] = [
      {
        key: "registered_at",
        header: "Data",
        headerHint: NC_HELP.table.registeredAt,
        render: (row) => formatDisplayDate(row.registered_at),
      },
      {
        key: "sale_number",
        header: "OV",
        headerHint: NC_HELP.table.saleNumber,
        render: (row) => row.sale_number || "—",
      },
      {
        key: "material_code",
        header: "Material",
        headerHint: NC_HELP.table.material,
        render: (row) => row.material_code || "—",
      },
      {
        key: "supplier_name",
        header: "Fornecedor",
        headerHint: NC_HELP.table.supplier,
        render: (row) => row.supplier_name || "—",
      },
      {
        key: "purchase_order",
        header: "OC",
        headerHint: NC_HELP.table.purchaseOrder,
        render: (row) => row.purchase_order || "—",
      },
      {
        key: "invoice_number",
        header: "NF",
        headerHint: NC_HELP.table.invoice,
        render: (row) => row.invoice_number || "—",
      },
      {
        key: "qty_received",
        header: "Rec",
        headerHint: NC_HELP.table.qtyReceived,
        render: (row) => (row.qty_received != null ? String(row.qty_received) : "—"),
      },
      {
        key: "qty_accepted",
        header: "Ace",
        headerHint: NC_HELP.table.qtyAccepted,
        render: (row) => (row.qty_accepted != null ? String(row.qty_accepted) : "—"),
      },
      {
        key: "qty_rejected",
        header: "Rep",
        headerHint: NC_HELP.table.qtyRejected,
        render: (row) => (row.qty_rejected != null ? String(row.qty_rejected) : "—"),
      },
      {
        key: "status",
        header: "Status",
        headerHint: NC_HELP.table.status,
        render: (row) => (
          <StatusBadge
            label={lmpNcStatusLabel(String(row.status))}
            variant={statusVariant(String(row.status))}
          />
        ),
      },
    ];
    if (canWrite) {
      cols.push({
        key: "actions",
        header: "Ações",
        headerHint: NC_HELP.table.actions,
        render: (row) => (
          <div className="lmps-nc-actions">
            <button
              type="button"
              className="lmps-ghost-btn lmps-btn--sm"
              onClick={() => openEdit(row)}
              aria-label="Editar"
            >
              <Pencil size={14} />
            </button>
            <button
              type="button"
              className="lmps-ghost-btn lmps-btn--sm"
              onClick={() => void requestDelete(row)}
              aria-label="Excluir"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ),
      });
    }
    return cols;
  }, [canWrite]);

  const setField =
    (key: keyof FormState) =>
    (value: string) => {
      setForm((prev) => ({ ...prev, [key]: value }));
    };

  return (
    <div className="dashboard-page dashboard-lmps">
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <div className="lmps-page-header__title-row">
            <h1>Acompanhamento de LMPs</h1>
          </div>
          <span className="lmps-page-subtitle lmps-page-subtitle--with-help">
            Registro operacional de não conformidades
            <HelpTooltip
              content={NC_HELP.pageSubtitle}
              ariaLabel="Ajuda: escopo do registro de NCs"
              className="lmps-page-subtitle__help"
            />
          </span>
          <LmpsNav currentPath={pathname} filterState={filterState} />
        </div>
        <div className="lmps-header-actions">
          {canWrite ? (
            <div className="lmps-header-action">
              <ActionButton type="button" variant="primary" onClick={openCreate}>
                <Plus size={16} />
                Nova não conformidade
              </ActionButton>
              <HelpTooltip
                content={NC_HELP.newButton}
                ariaLabel="Ajuda: nova não conformidade"
                className="lmps-header-action__help"
              />
            </div>
          ) : null}
        </div>
      </header>

      <FiltersRow>
        <FilterSelectField
          id="lmps-nc-status"
          label="Status"
          hint={NC_HELP.filters.status}
          value={status}
          onChange={(v) => {
            setPage(1);
            setStatus(v);
          }}
          placeholderOption="Todos"
          options={LMP_NC_STATUS_OPTIONS.map((o) => ({
            value: o.value,
            label: o.label,
          }))}
        />
        <FilterSelectField
          id="lmps-nc-branch"
          label="Filial"
          hint={NC_HELP.filters.branch}
          value={branch}
          onChange={(v) => {
            setPage(1);
            setBranch(v);
          }}
          placeholderOption="Todas"
          options={[
            { value: "01", label: "01" },
            { value: "02", label: "02" },
          ]}
        />
        <FilterInputField
          label="OV"
          hint={NC_HELP.filters.saleNumber}
          type="text"
          value={saleNumber}
          onChange={(v) => {
            setPage(1);
            setSaleNumber(v);
          }}
        />
        <FilterInputField
          label="Material"
          hint={NC_HELP.filters.material}
          type="text"
          value={materialCode}
          onChange={(v) => {
            setPage(1);
            setMaterialCode(v);
          }}
        />
        <FilterInputField
          label="Produto"
          hint={NC_HELP.filters.product}
          type="text"
          value={productCode}
          onChange={(v) => {
            setPage(1);
            setProductCode(v);
          }}
        />
        <FilterInputField
          label="Data início"
          hint={NC_HELP.filters.dateStart}
          type="date"
          value={dateStart}
          onChange={(v) => {
            setPage(1);
            setDateStart(v);
          }}
        />
        <FilterInputField
          label="Data fim"
          hint={NC_HELP.filters.dateEnd}
          type="date"
          value={dateEnd}
          onChange={(v) => {
            setPage(1);
            setDateEnd(v);
          }}
        />
      </FiltersRow>

      {error ? (
        <div className="lmps-refreshing-banner" role="alert">
          {error}
        </div>
      ) : null}

      <DataTableSection
        title="Não conformidades"
        titleHint={NC_HELP.table.section}
        searchHint={NC_HELP.table.search}
        columns={columns}
        rows={items}
        rowKey={(row) => row.id}
        loading={loading}
        emptyMessage="Nenhuma não conformidade encontrada."
        serverPagination={{
          page,
          pageSize: 50,
          total,
          onPageChange: setPage,
        }}
      />

      <HostContainedFill
        open={formOpen}
        onClose={() => !saving && setFormOpen(false)}
        title={editing ? "Editar não conformidade" : "Nova não conformidade"}
      >
        <div className="lmps-nc-form">
          {formError ? (
            <div className="lmps-refreshing-banner" role="alert">
              {formError}
            </div>
          ) : null}

          <SectionCard
            title="Identificação"
            hint={NC_HELP.form.sectionIdentification}
          >
            <div className="lmps-nc-form-grid">
              <NativeTextField
                id="nc-registered-at"
                label="Data/hora registro"
                hint={NC_HELP.form.registeredAt}
                type="datetime-local"
                required
                value={form.registered_at}
                onChange={setField("registered_at")}
              />
              <SelectField
                id="nc-status"
                label="Status"
                hint={NC_HELP.form.status}
                required
                value={form.status}
                onChange={(v) => setForm((p) => ({ ...p, status: v as LmpNcStatus }))}
                options={LMP_NC_STATUS_OPTIONS.map((o) => ({
                  value: o.value,
                  label: o.label,
                }))}
              />
              <SelectField
                id="nc-branch"
                label="Filial"
                hint={NC_HELP.form.branch}
                value={form.branch_code}
                onChange={setField("branch_code")}
                allowEmpty
                emptyLabel="—"
                options={[
                  { value: "01", label: "01" },
                  { value: "02", label: "02" },
                ]}
              />
              <TextField
                id="nc-sale"
                label="OV (opcional)"
                hint={NC_HELP.form.saleNumber}
                value={form.sale_number}
                onChange={setField("sale_number")}
              />
            </div>
          </SectionCard>

          <SectionCard
            title="Documento / material"
            hint={NC_HELP.form.sectionDocument}
          >
            <div className="lmps-nc-form-grid">
              <TextField
                id="nc-material"
                label="Código material"
                hint={NC_HELP.form.material}
                value={form.material_code}
                onChange={setField("material_code")}
              />
              <TextField
                id="nc-supplier"
                label="Fornecedor"
                hint={NC_HELP.form.supplier}
                value={form.supplier_name}
                onChange={setField("supplier_name")}
              />
              <TextField
                id="nc-oc"
                label="Nº OC"
                hint={NC_HELP.form.purchaseOrder}
                value={form.purchase_order}
                onChange={setField("purchase_order")}
              />
              <TextField
                id="nc-nf"
                label="Nº NF"
                hint={NC_HELP.form.invoice}
                value={form.invoice_number}
                onChange={setField("invoice_number")}
              />
              <TextField
                id="nc-qty-rec"
                label="Qtde recebida"
                hint={NC_HELP.form.qtyReceived}
                value={form.qty_received}
                onChange={setField("qty_received")}
              />
              <TextField
                id="nc-qty-acc"
                label="Qtde aceita"
                hint={NC_HELP.form.qtyAccepted}
                value={form.qty_accepted}
                onChange={setField("qty_accepted")}
              />
              <TextField
                id="nc-qty-rej"
                label="Qtde reprovada"
                hint={NC_HELP.form.qtyRejected}
                value={form.qty_rejected}
                onChange={setField("qty_rejected")}
              />
            </div>
          </SectionCard>

          <SectionCard
            title="Produtos (opcional)"
            hint={NC_HELP.form.sectionProducts}
          >
            <TextField
              id="nc-products"
              label="Códigos de produto"
              hint={NC_HELP.form.productCodes}
              value={form.product_codes}
              onChange={setField("product_codes")}
            />
          </SectionCard>

          <SectionCard title="Descrição" hint={NC_HELP.form.sectionDescription}>
            <TextAreaField
              id="nc-defect"
              label="Descrição do defeito"
              hint={NC_HELP.form.defectDescription}
              value={form.defect_description}
              onChange={setField("defect_description")}
              rows={3}
            />
            <TextAreaField
              id="nc-actions"
              label="Ações / ação corretiva"
              hint={NC_HELP.form.correctiveActions}
              value={form.corrective_actions}
              onChange={setField("corrective_actions")}
              rows={3}
            />
            <TextAreaField
              id="nc-opinion"
              label="Parecer técnico"
              hint={NC_HELP.form.technicalOpinion}
              value={form.technical_opinion}
              onChange={setField("technical_opinion")}
              rows={3}
            />
          </SectionCard>

          <FormActions>
            <ActionButton
              type="button"
              variant="ghost"
              disabled={saving}
              onClick={() => setFormOpen(false)}
            >
              Cancelar
            </ActionButton>
            <ActionButton
              type="button"
              variant="primary"
              disabled={saving}
              onClick={() => void handleSave()}
            >
              {saving ? "Salvando…" : "Salvar"}
            </ActionButton>
          </FormActions>
        </div>
      </HostContainedFill>

      <HostContainedDialog
        open={pending !== null}
        onClose={cancelPending}
        title={pending?.title || "Confirmar"}
      >
        <ConfirmModalPanel
          message={
            pending?.message ??
            (pendingDelete
              ? "Excluir esta não conformidade?"
              : "Confirmar ação?")
          }
          confirmLabel={pending?.confirmLabel}
          cancelLabel={pending?.cancelLabel ?? "Cancelar"}
          variant={pending?.variant}
          onConfirm={confirmPending}
          onCancel={cancelPending}
          classNames={LMPS_CONFIRM_CLASSES}
        />
      </HostContainedDialog>
    </div>
  );
}
