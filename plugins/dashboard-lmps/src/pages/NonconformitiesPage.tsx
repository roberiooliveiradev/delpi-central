import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  ConfirmModalPanel,
  HelpTooltip,
  useConfirmDialogController,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";
import { Pencil, Plus, Trash2 } from "lucide-react";

import { getLmpBySaleNumber } from "../api/lmpApi";
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
  FormGrid,
  HostContainedDialog,
  HostContainedFill,
  LMPS_CONFIRM_CLASSES,
  SectionCard,
  SelectField,
  StatusBadge,
  TextAreaField,
  TextField,
} from "../components/ncUi";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  LmpNcProductLine,
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
  status: LmpNcStatus;
  sale_number: string;
  customer_name: string;
  launch_date: string;
  last_revision_date: string;
  executed_by: string;
  released_by: string;
  defect_description: string;
  corrective_actions: string;
  technical_opinion: string;
  products: LmpNcProductLine[];
  registered_at_display: string;
};

function toDateInput(iso: string | null | undefined): string {
  if (!iso) return "";
  return iso.slice(0, 10);
}

function formatDisplayDate(iso: string | null | undefined): string {
  if (!iso) return "—";
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

function formatDisplayDateOnly(iso: string | null | undefined): string {
  if (!iso) return "—";
  const text = iso.slice(0, 10);
  const [y, m, d] = text.split("-");
  if (!y || !m || !d) return iso;
  return `${d}/${m}/${y}`;
}

function emptyForm(): FormState {
  return {
    status: "open",
    sale_number: "",
    customer_name: "",
    launch_date: "",
    last_revision_date: "",
    executed_by: "",
    released_by: "",
    defect_description: "",
    corrective_actions: "",
    technical_opinion: "",
    products: [],
    registered_at_display: "",
  };
}

function recordToForm(record: LmpNonconformity): FormState {
  const products =
    record.products?.length
      ? record.products.map((p) => ({
          product_code: p.product_code ?? "",
          product_description: p.product_description ?? "",
        }))
      : (record.product_codes ?? []).map((code) => ({
          product_code: code,
          product_description: "",
        }));
  return {
    status: (record.status as LmpNcStatus) || "open",
    sale_number: record.sale_number ?? "",
    customer_name: record.customer_name ?? "",
    launch_date: toDateInput(record.launch_date),
    last_revision_date: toDateInput(record.last_revision_date),
    executed_by: record.executed_by ?? "",
    released_by: record.released_by ?? "",
    defect_description: record.defect_description ?? "",
    corrective_actions: record.corrective_actions ?? "",
    technical_opinion: record.technical_opinion ?? "",
    products,
    registered_at_display: formatDisplayDate(record.registered_at),
  };
}

function formToPayload(form: FormState): LmpNonconformityPayload {
  return {
    status: form.status,
    sale_number: form.sale_number.trim() || null,
    customer_name: form.customer_name.trim() || null,
    launch_date: form.launch_date.trim() || null,
    last_revision_date: form.last_revision_date.trim() || null,
    executed_by: form.executed_by.trim() || null,
    released_by: form.released_by.trim() || null,
    defect_description: form.defect_description.trim() || null,
    corrective_actions: form.corrective_actions.trim() || null,
    technical_opinion: form.technical_opinion.trim() || null,
    products: form.products
      .map((p) => ({
        product_code: p.product_code.trim(),
        product_description: (p.product_description ?? "").trim() || null,
      }))
      .filter((p) => p.product_code),
  };
}

function statusVariant(status: string): StatusBadgeVariant {
  if (status === "done") return "success";
  if (status === "in_progress") return "info";
  return "warning";
}

function productsSummary(row: LmpNonconformity): string {
  const codes =
    row.products?.map((p) => p.product_code).filter(Boolean) ??
    row.product_codes ??
    [];
  if (!codes.length) return "—";
  if (codes.length <= 2) return codes.join(", ");
  return `${codes.slice(0, 2).join(", ")} +${codes.length - 2}`;
}

export function NonconformitiesPage({ pathname, canWrite = true }: Props) {
  const filterState = readLmpsFilters();
  const [items, setItems] = useState<LmpNonconformity[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [saleNumber, setSaleNumber] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [productCode, setProductCode] = useState("");
  const [dateStart, setDateStart] = useState("");
  const [dateEnd, setDateEnd] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<LmpNonconformity | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [hydrating, setHydrating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<LmpNonconformity | null>(null);
  const { confirm, pending, confirmPending, cancelPending } = useConfirmDialogController();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformities({
        status: status || undefined,
        sale_number: saleNumber || undefined,
        customer_name: customerName || undefined,
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
  }, [status, saleNumber, customerName, productCode, dateStart, dateEnd, page]);

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

  const handleHydrateFromLmp = async () => {
    const ov = form.sale_number.trim();
    if (!ov) {
      setFormError("Informe o número da OV (= LMP) para buscar no TOTVS.");
      return;
    }
    setHydrating(true);
    setFormError(null);
    try {
      const lmp = await getLmpBySaleNumber(ov);
      const products: LmpNcProductLine[] = (lmp.list_products ?? []).map((p) => ({
        product_code: p.code ?? "",
        product_description: p.description ?? "",
      }));
      setForm((prev) => ({
        ...prev,
        sale_number: lmp.sale_number || ov,
        customer_name: lmp.costumer_name ?? prev.customer_name,
        launch_date: toDateInput(lmp.start_date) || prev.launch_date,
        last_revision_date:
          toDateInput(lmp.homolog_date) ||
          toDateInput(lmp.end_date) ||
          prev.last_revision_date,
        products: products.length ? products : prev.products,
      }));
    } catch (err) {
      setFormError(
        err instanceof Error ? err.message : "Erro ao buscar LMP no TOTVS.",
      );
    } finally {
      setHydrating(false);
    }
  };

  const handleSave = async () => {
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

  const updateProduct =
    (index: number, key: keyof LmpNcProductLine) =>
    (value: string) => {
      setForm((prev) => {
        const products = prev.products.map((row, i) =>
          i === index ? { ...row, [key]: value } : row,
        );
        return { ...prev, products };
      });
    };

  const addProductRow = () => {
    setForm((prev) => ({
      ...prev,
      products: [
        ...prev.products,
        { product_code: "", product_description: "" },
      ],
    }));
  };

  const removeProductRow = (index: number) => {
    setForm((prev) => ({
      ...prev,
      products: prev.products.filter((_, i) => i !== index),
    }));
  };

  const columns = useMemo<DataTableColumn<LmpNonconformity>[]>(() => {
    const cols: DataTableColumn<LmpNonconformity>[] = [
      {
        key: "registered_at",
        header: "Registro",
        headerHint: NC_HELP.table.registeredAt,
        render: (row) => formatDisplayDate(row.registered_at),
      },
      {
        key: "sale_number",
        header: "OV / LMP",
        headerHint: NC_HELP.table.saleNumber,
        render: (row) => row.sale_number || "—",
      },
      {
        key: "customer_name",
        header: "Cliente",
        headerHint: NC_HELP.table.customer,
        render: (row) => row.customer_name || "—",
      },
      {
        key: "launch_date",
        header: "Lançamento",
        headerHint: NC_HELP.table.launchDate,
        render: (row) => formatDisplayDateOnly(row.launch_date),
      },
      {
        key: "last_revision_date",
        header: "Últ. revisão",
        headerHint: NC_HELP.table.lastRevisionDate,
        render: (row) => formatDisplayDateOnly(row.last_revision_date),
      },
      {
        key: "executed_by",
        header: "Executou",
        headerHint: NC_HELP.table.executedBy,
        render: (row) => row.executed_by || "—",
      },
      {
        key: "released_by",
        header: "Liberou",
        headerHint: NC_HELP.table.releasedBy,
        render: (row) => row.released_by || "—",
      },
      {
        key: "products",
        header: "Produtos",
        headerHint: NC_HELP.table.products,
        render: (row) => productsSummary(row),
      },
      {
        key: "defect_description",
        header: "Problema",
        headerHint: NC_HELP.table.problem,
        render: (row) => {
          const text = (row.defect_description || "").trim();
          if (!text) return "—";
          return text.length > 48 ? `${text.slice(0, 48)}…` : text;
        },
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
            Registro de não conformidades de engenharia
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
        <FilterInputField
          label="OV / LMP"
          hint={NC_HELP.filters.saleNumber}
          type="text"
          value={saleNumber}
          onChange={(v) => {
            setPage(1);
            setSaleNumber(v);
          }}
        />
        <FilterInputField
          label="Cliente"
          hint={NC_HELP.filters.customer}
          type="text"
          value={customerName}
          onChange={(v) => {
            setPage(1);
            setCustomerName(v);
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
            <FormGrid>
              {editing ? (
                <div className="lmps-field lmps-field--readonly">
                  <span className="lmps-field__label">
                    Data/hora registro
                    <HelpTooltip
                      content={NC_HELP.form.registeredAt}
                      ariaLabel="Ajuda: data de registro"
                    />
                  </span>
                  <p className="lmps-field__readonly-value">
                    {form.registered_at_display || "—"}
                  </p>
                </div>
              ) : (
                <div className="lmps-field lmps-field--readonly">
                  <span className="lmps-field__label">
                    Data/hora registro
                    <HelpTooltip
                      content={NC_HELP.form.registeredAt}
                      ariaLabel="Ajuda: data de registro"
                    />
                  </span>
                  <p className="lmps-field__readonly-value">
                    Será definida automaticamente ao salvar
                  </p>
                </div>
              )}
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
              <TextField
                id="nc-sale"
                label="OV / LMP"
                hint={NC_HELP.form.saleNumber}
                value={form.sale_number}
                onChange={setField("sale_number")}
                fullWidth
              />
              <div className="lmps-nc-hydrate">
                <ActionButton
                  type="button"
                  variant="ghost"
                  disabled={hydrating || saving || !form.sale_number.trim()}
                  onClick={() => void handleHydrateFromLmp()}
                >
                  {hydrating ? "Buscando…" : "Buscar LMP"}
                </ActionButton>
                <HelpTooltip
                  content={NC_HELP.form.hydrateLmp}
                  ariaLabel="Ajuda: buscar LMP no TOTVS"
                />
              </div>
              <TextField
                id="nc-customer"
                label="Cliente"
                hint={NC_HELP.form.customer}
                value={form.customer_name}
                onChange={setField("customer_name")}
                fullWidth
              />
              <TextField
                id="nc-launch"
                label="Data lançamento"
                hint={NC_HELP.form.launchDate}
                type="date"
                value={form.launch_date}
                onChange={setField("launch_date")}
                fullWidth
              />
              <TextField
                id="nc-revision"
                label="Data última revisão"
                hint={NC_HELP.form.lastRevisionDate}
                type="date"
                value={form.last_revision_date}
                onChange={setField("last_revision_date")}
                fullWidth
              />
            </FormGrid>
          </SectionCard>

          <SectionCard title="Responsáveis" hint={NC_HELP.form.sectionPeople}>
            <FormGrid>
              <TextField
                id="nc-executed"
                label="Quem executou"
                hint={NC_HELP.form.executedBy}
                value={form.executed_by}
                onChange={setField("executed_by")}
                fullWidth
              />
              <TextField
                id="nc-released"
                label="Quem liberou"
                hint={NC_HELP.form.releasedBy}
                value={form.released_by}
                onChange={setField("released_by")}
                fullWidth
              />
            </FormGrid>
          </SectionCard>

          <SectionCard title="Produtos" hint={NC_HELP.form.sectionProducts}>
            <div className="lmps-nc-products">
              <table className="lmps-nc-products__table">
                <thead>
                  <tr>
                    <th>
                      Código material
                      <HelpTooltip
                        content={NC_HELP.form.productCode}
                        ariaLabel="Ajuda: código material"
                      />
                    </th>
                    <th>
                      Descrição
                      <HelpTooltip
                        content={NC_HELP.form.productDescription}
                        ariaLabel="Ajuda: descrição do produto"
                      />
                    </th>
                    <th aria-label="Ações" />
                  </tr>
                </thead>
                <tbody>
                  {form.products.length === 0 ? (
                    <tr>
                      <td colSpan={3} className="lmps-nc-products__empty">
                        Nenhum produto. Busque a LMP ou adicione linhas.
                      </td>
                    </tr>
                  ) : (
                    form.products.map((row, index) => (
                      <tr key={`nc-product-${index}`}>
                        <td>
                          <input
                            className="delpi-ui-native-control"
                            value={row.product_code}
                            onChange={(e) =>
                              updateProduct(index, "product_code")(e.target.value)
                            }
                            aria-label={`Código material linha ${index + 1}`}
                          />
                        </td>
                        <td>
                          <input
                            className="delpi-ui-native-control"
                            value={row.product_description ?? ""}
                            onChange={(e) =>
                              updateProduct(
                                index,
                                "product_description",
                              )(e.target.value)
                            }
                            aria-label={`Descrição linha ${index + 1}`}
                          />
                        </td>
                        <td>
                          <button
                            type="button"
                            className="lmps-ghost-btn lmps-btn--sm"
                            onClick={() => removeProductRow(index)}
                            aria-label={NC_HELP.form.removeProduct}
                            title={NC_HELP.form.removeProduct}
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
              <div className="lmps-nc-products__toolbar">
                <ActionButton
                  type="button"
                  variant="ghost"
                  onClick={addProductRow}
                >
                  <Plus size={14} />
                  Adicionar produto
                </ActionButton>
                <HelpTooltip
                  content={NC_HELP.form.addProduct}
                  ariaLabel="Ajuda: adicionar produto"
                />
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Descrição" hint={NC_HELP.form.sectionDescription}>
            <FormGrid className="lmps-form-grid--stack">
              <TextAreaField
                id="nc-defect"
                label="Problema identificado"
                hint={NC_HELP.form.defectDescription}
                value={form.defect_description}
                onChange={setField("defect_description")}
                rows={4}
                fullWidth
              />
              <TextAreaField
                id="nc-actions"
                label="Ações / ação corretiva"
                hint={NC_HELP.form.correctiveActions}
                value={form.corrective_actions}
                onChange={setField("corrective_actions")}
                rows={4}
                fullWidth
              />
              <TextAreaField
                id="nc-opinion"
                label="Parecer técnico"
                hint={NC_HELP.form.technicalOpinion}
                value={form.technical_opinion}
                onChange={setField("technical_opinion")}
                rows={4}
                fullWidth
              />
            </FormGrid>
          </SectionCard>

          <FormActions align="end">
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
              disabled={saving || hydrating}
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
