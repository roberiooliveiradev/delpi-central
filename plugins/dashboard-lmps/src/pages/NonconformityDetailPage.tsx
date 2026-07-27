import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import {
  ActionButton,
  ConfirmModalPanel,
  HelpTooltip,
  useConfirmDialogController,
  type StatusBadgeVariant,
} from "@delpi/plugin-ui/index";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

import { getLmpBySaleNumber } from "../api/lmpApi";
import {
  createLmpNonconformity,
  deleteLmpNonconformity,
  fetchLmpNonconformity,
  updateLmpNonconformity,
} from "../api/lmpNonconformityApi";
import {
  searchProducts,
  type ProductSearchItem,
} from "../api/productApi";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { NcChangeHistory } from "../components/NcChangeHistory";
import { NcProblemTagsField } from "../components/NcProblemTagsField";
import {
  EditableSectionCard,
  FormActions,
  FormGrid,
  HostContainedDialog,
  LMPS_CONFIRM_CLASSES,
  ReadOnlyField,
  ReadOnlyGrid,
  SectionCard,
  SelectField,
  StatusBadge,
  TextAreaField,
  TextField,
} from "../components/ncUi";
import { LMPS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { buildNcDetailPath, LMPS_ROUTES } from "../constants/routes";
import { useNcSectionEdit } from "../hooks/useNcSectionEdit";
import type {
  LmpNcProductLine,
  LmpNcStatus,
  LmpNonconformity,
} from "../types/lmpNonconformity";
import {
  LMP_NC_STATUS_OPTIONS,
  lmpNcStatusLabel,
} from "../types/lmpNonconformity";
import { GHOST_BTN } from "../ui/ghostChrome";
import {
  emptyNcForm,
  formatDisplayDate,
  formatDisplayDateOnly,
  looksLikeOvCode,
  ncFormToPayload,
  recordToNcForm,
  toDateInput,
  type NcFormState,
} from "../utils/ncFormModel";
import { navigateLmps, navigateLmpsBack } from "../utils/navigation";

const NC_HELP = LMPS_HELP_TOOLTIPS.nonconformities;

type NcSectionKey = "identification" | "people" | "products" | "description";

type Props = {
  mode: "create" | "detail";
  recordId?: string;
  canWrite?: boolean;
};

function statusVariant(status: string): StatusBadgeVariant {
  if (status === "done") return "success";
  if (status === "in_progress") return "info";
  return "warning";
}

function ProductsReadContent({ form }: { form: NcFormState }) {
  if (!form.products.length) {
    return <p className="lmps-muted">Nenhum produto.</p>;
  }
  return (
    <ul className="lmps-nc-products-read">
      {form.products.map((row, index) => (
        <li key={`nc-product-read-${index}`}>
          <strong>{row.product_code || "—"}</strong>
          {row.product_description?.trim()
            ? ` — ${row.product_description.trim()}`
            : ""}
        </li>
      ))}
    </ul>
  );
}

export function NonconformityDetailPage({
  mode,
  recordId,
  canWrite = true,
}: Props) {
  const isCreate = mode === "create";
  const { isEditing, startEdit, stopEdit, stopAll } = useNcSectionEdit();
  const { confirm, pending, confirmPending, cancelPending } =
    useConfirmDialogController();

  const [record, setRecord] = useState<LmpNonconformity | null>(null);
  const [form, setForm] = useState<NcFormState>(emptyNcForm);
  const [baseline, setBaseline] = useState<NcFormState>(emptyNcForm);
  const [loading, setLoading] = useState(!isCreate);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [historyReloadKey, setHistoryReloadKey] = useState(0);
  const [hydrating, setHydrating] = useState(false);
  const [productQuery, setProductQuery] = useState("");
  const [productHits, setProductHits] = useState<ProductSearchItem[]>([]);
  const [productSearching, setProductSearching] = useState(false);
  const [lmpProductCandidates, setLmpProductCandidates] = useState<
    LmpNcProductLine[]
  >([]);

  const hydrateAbortRef = useRef<AbortController | null>(null);
  const hydrateTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const productSearchAbortRef = useRef<AbortController | null>(null);
  const productSearchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const lastHydratedOvRef = useRef<string>("");
  const lmpProductCandidatesRef = useRef(lmpProductCandidates);
  lmpProductCandidatesRef.current = lmpProductCandidates;

  const load = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchLmpNonconformity(id);
      const next = recordToNcForm(data);
      setRecord(data);
      setForm(next);
      setBaseline(next);
      lastHydratedOvRef.current = (data.sale_number ?? "").trim();
      setLmpProductCandidates([]);
      setProductQuery("");
      setProductHits([]);
      stopAll();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Erro ao carregar não conformidade.",
      );
      setRecord(null);
    } finally {
      setLoading(false);
    }
  }, [stopAll]);

  useEffect(() => {
    if (isCreate) {
      setRecord(null);
      setForm(emptyNcForm());
      setBaseline(emptyNcForm());
      setLoading(false);
      setError(null);
      setFormError(null);
      lastHydratedOvRef.current = "";
      setLmpProductCandidates([]);
      setProductQuery("");
      setProductHits([]);
      return;
    }
    if (!recordId) {
      setError("Identificador da não conformidade ausente.");
      setLoading(false);
      return;
    }
    void load(recordId);
  }, [isCreate, recordId, load]);

  useEffect(() => {
    return () => {
      if (hydrateTimerRef.current) clearTimeout(hydrateTimerRef.current);
      hydrateAbortRef.current?.abort();
    };
  }, []);

  const applyLmpHydration = useCallback(
    (ov: string, lmp: Awaited<ReturnType<typeof getLmpBySaleNumber>>) => {
      const products: LmpNcProductLine[] = (lmp.list_products ?? [])
        .map((p) => ({
          product_code: (p.code ?? "").trim(),
          product_description: p.description ?? "",
        }))
        .filter((p) => p.product_code);
      setLmpProductCandidates(products);
      lastHydratedOvRef.current = (lmp.sale_number || ov).trim();
      setForm((prev) => ({
        ...prev,
        sale_number: lmp.sale_number || ov,
        customer_name: lmp.costumer_name?.trim()
          ? lmp.costumer_name
          : prev.customer_name,
        launch_date: toDateInput(lmp.start_date) || prev.launch_date,
        last_revision_date:
          toDateInput(lmp.homolog_date) ||
          toDateInput(lmp.end_date) ||
          prev.last_revision_date,
        products: products.length ? products : prev.products,
      }));
    },
    [],
  );

  const handleHydrateFromLmp = useCallback(
    async (ovRaw?: string, opts?: { silent?: boolean }) => {
      const ov = (ovRaw ?? form.sale_number).trim();
      if (!ov) {
        if (!opts?.silent) {
          setFormError("Informe o número da OV (= LMP) para buscar no TOTVS.");
        }
        return;
      }
      if (ov === lastHydratedOvRef.current && opts?.silent) {
        return;
      }
      hydrateAbortRef.current?.abort();
      const controller = new AbortController();
      hydrateAbortRef.current = controller;
      setHydrating(true);
      if (!opts?.silent) setFormError(null);
      try {
        const lmp = await getLmpBySaleNumber(ov, {}, controller.signal);
        if (controller.signal.aborted) return;
        applyLmpHydration(ov, lmp);
      } catch (err) {
        if (controller.signal.aborted) return;
        if (!opts?.silent) {
          setFormError(
            err instanceof Error ? err.message : "Erro ao buscar LMP no TOTVS.",
          );
        }
      } finally {
        if (!controller.signal.aborted) setHydrating(false);
      }
    },
    [applyLmpHydration, form.sale_number],
  );

  const scheduleAutoHydrate = useCallback(
    (ov: string) => {
      if (hydrateTimerRef.current) clearTimeout(hydrateTimerRef.current);
      if (!looksLikeOvCode(ov)) return;
      hydrateTimerRef.current = setTimeout(() => {
        void handleHydrateFromLmp(ov, { silent: true });
      }, 450);
    },
    [handleHydrateFromLmp],
  );

  const setField =
    (key: keyof NcFormState) =>
    (value: string) => {
      setForm((prev) => ({ ...prev, [key]: value }));
    };

  const setSaleNumberField = (value: string) => {
    setForm((prev) => ({ ...prev, sale_number: value }));
    scheduleAutoHydrate(value);
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

  const addProductFromHit = (hit: ProductSearchItem) => {
    const code = hit.code.trim().toUpperCase();
    if (!code) return;
    setForm((prev) => {
      if (
        prev.products.some(
          (p) => p.product_code.trim().toUpperCase() === code,
        )
      ) {
        return prev;
      }
      return {
        ...prev,
        products: [
          ...prev.products,
          {
            product_code: hit.code,
            product_description: hit.description || "",
          },
        ],
      };
    });
    setProductHits((prev) => prev.filter((p) => p.code !== hit.code));
  };

  const runProductSearch = useCallback(async (rawQuery: string) => {
    const q = rawQuery.trim();
    if (q.length < 2) {
      setProductHits([]);
      setProductSearching(false);
      return;
    }

    productSearchAbortRef.current?.abort();
    const controller = new AbortController();
    productSearchAbortRef.current = controller;
    setProductSearching(true);

    try {
      const local = lmpProductCandidatesRef.current.filter((p) => {
        const code = (p.product_code || "").toLowerCase();
        const desc = (p.product_description || "").toLowerCase();
        const needle = q.toLowerCase();
        return code.includes(needle) || desc.includes(needle);
      });
      let remote: ProductSearchItem[] = [];
      try {
        remote = await searchProducts(q, controller.signal);
      } catch {
        if (controller.signal.aborted) return;
        remote = [];
      }
      if (controller.signal.aborted) return;

      const merged = new Map<string, ProductSearchItem>();
      for (const p of local) {
        merged.set(p.product_code.toUpperCase(), {
          code: p.product_code,
          description: p.product_description || "",
        });
      }
      for (const p of remote) {
        merged.set(p.code.toUpperCase(), p);
      }
      setProductHits(Array.from(merged.values()));
    } finally {
      if (!controller.signal.aborted) {
        setProductSearching(false);
      }
    }
  }, []);

  const onProductQueryChange = (value: string) => {
    setProductQuery(value);
    if (productSearchTimerRef.current) {
      clearTimeout(productSearchTimerRef.current);
    }
    const trimmed = value.trim();
    if (!trimmed) {
      productSearchAbortRef.current?.abort();
      setProductHits([]);
      setProductSearching(false);
      return;
    }
    if (trimmed.length < 2) {
      setProductHits([]);
      setProductSearching(false);
      return;
    }
    productSearchTimerRef.current = setTimeout(() => {
      void runProductSearch(value);
    }, 280);
  };

  useEffect(() => {
    return () => {
      if (productSearchTimerRef.current) {
        clearTimeout(productSearchTimerRef.current);
      }
      productSearchAbortRef.current?.abort();
    };
  }, []);

  const persistForm = async (saveKey: string) => {
    setSaving(saveKey);
    setFormError(null);
    try {
      const payload = ncFormToPayload(form);
      if (isCreate) {
        const created = await createLmpNonconformity(payload);
        navigateLmps(buildNcDetailPath(created.id));
        return;
      }
      if (!recordId) {
        throw new Error("Identificador da não conformidade ausente.");
      }
      const updated = await updateLmpNonconformity(recordId, payload);
      const next = recordToNcForm(updated);
      setRecord(updated);
      setForm(next);
      setBaseline(next);
      lastHydratedOvRef.current = (updated.sale_number ?? "").trim();
      setHistoryReloadKey((value) => value + 1);
      if (saveKey !== "create") {
        stopEdit(saveKey);
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Erro ao salvar.");
    } finally {
      setSaving(null);
    }
  };

  const cancelSection = (key: NcSectionKey) => {
    setForm(baseline);
    setFormError(null);
    setProductQuery("");
    setProductHits([]);
    stopEdit(key);
  };

  const requestDelete = async () => {
    if (!record) return;
    const ok = await confirm({
      title: "Excluir não conformidade",
      message: "Excluir esta não conformidade? Esta ação não pode ser desfeita.",
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!ok) return;
    try {
      await deleteLmpNonconformity(record.id);
      navigateLmps(LMPS_ROUTES.nonconformities);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir.");
    }
  };

  const busy = saving !== null || hydrating;

  const identificationEdit = (
    <FormGrid>
      <div className="lmps-nc-ov-row lmps-span-2">
        <TextField
          id="nc-sale"
          label="OV"
          hint={NC_HELP.form.saleNumber}
          value={form.sale_number}
          onChange={setSaleNumberField}
          fullWidth
        />
        <div className="lmps-nc-hydrate">
          <ActionButton
            type="button"
            variant="ghost"
            disabled={busy || !form.sale_number.trim()}
            onClick={() => void handleHydrateFromLmp()}
          >
            {hydrating ? "Buscando…" : "Buscar LMP"}
          </ActionButton>
          <HelpTooltip
            content={NC_HELP.form.hydrateLmp}
            ariaLabel="Ajuda: buscar LMP no TOTVS"
          />
        </div>
      </div>
      <TextField
        id="nc-lmp-number"
        label="Número da LMP"
        hint={NC_HELP.form.lmpNumber}
        value={form.lmp_number}
        onChange={setField("lmp_number")}
        fullWidth
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
  );

  const identificationRead = (
    <ReadOnlyGrid>
      <ReadOnlyField
        id="nc-ro-sale"
        label="OV"
        hint={NC_HELP.form.saleNumber}
        value={form.sale_number}
      />
      <ReadOnlyField
        id="nc-ro-lmp-number"
        label="Número da LMP"
        hint={NC_HELP.form.lmpNumber}
        value={form.lmp_number}
      />
      <ReadOnlyField
        id="nc-ro-status"
        label="Status"
        hint={NC_HELP.form.status}
        value={lmpNcStatusLabel(form.status)}
      />
      <ReadOnlyField
        id="nc-ro-customer"
        label="Cliente"
        hint={NC_HELP.form.customer}
        value={form.customer_name}
      />
      <ReadOnlyField
        id="nc-ro-launch"
        label="Data lançamento"
        hint={NC_HELP.form.launchDate}
        value={formatDisplayDateOnly(form.launch_date || null)}
      />
      <ReadOnlyField
        id="nc-ro-revision"
        label="Data última revisão"
        hint={NC_HELP.form.lastRevisionDate}
        value={formatDisplayDateOnly(form.last_revision_date || null)}
      />
      {record?.registered_at ? (
        <ReadOnlyField
          id="nc-ro-registered"
          label="Registro"
          hint={NC_HELP.table.registeredAt}
          value={formatDisplayDate(record.registered_at)}
        />
      ) : null}
    </ReadOnlyGrid>
  );

  const peopleEdit = (
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
  );

  const peopleRead = (
    <ReadOnlyGrid>
      <ReadOnlyField
        id="nc-ro-executed"
        label="Quem executou"
        hint={NC_HELP.form.executedBy}
        value={form.executed_by}
      />
      <ReadOnlyField
        id="nc-ro-released"
        label="Quem liberou"
        hint={NC_HELP.form.releasedBy}
        value={form.released_by}
      />
    </ReadOnlyGrid>
  );

  const productsEdit = (
    <div className="lmps-nc-products">
      <div className="lmps-nc-product-search">
        <TextField
          id="nc-product-search"
          label="Buscar produto"
          hint={NC_HELP.form.productSearch}
          value={productQuery}
          onChange={onProductQueryChange}
          fullWidth
          placeholder="Código ou descrição"
        />
        {productSearching ? (
          <span className="lmps-nc-product-search__status" aria-live="polite">
            Buscando…
          </span>
        ) : null}
      </div>
      {productHits.length > 0 ? (
        <ul className="lmps-nc-product-hits" aria-label="Resultados da busca">
          {productHits.map((hit) => (
            <li key={hit.code}>
              <button
                type="button"
                className="lmps-nc-product-hits__item"
                onClick={() => addProductFromHit(hit)}
              >
                <strong>{hit.code}</strong>
                <span>{hit.description || "—"}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
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
                Nenhum produto. Informe a OV para trazer os da LMP, ou
                busque/adicione linhas.
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
        <ActionButton type="button" variant="ghost" onClick={addProductRow}>
          <Plus size={14} />
          Adicionar produto
        </ActionButton>
        <HelpTooltip
          content={NC_HELP.form.addProduct}
          ariaLabel="Ajuda: adicionar produto"
        />
      </div>
    </div>
  );

  const descriptionEdit = (
    <FormGrid className="lmps-form-grid--stack">
      <NcProblemTagsField
        id="nc-problem-tags"
        selectedValues={form.problem_tags}
        onChange={(problem_tags) =>
          setForm((prev) => ({ ...prev, problem_tags }))
        }
      />
      <TextAreaField
        id="nc-defect"
        label="Descrição do problema"
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
  );

  const descriptionRead = (
    <ReadOnlyGrid className="lmps-form-grid--stack">
      <div className="lmps-ficha-field lmps-span-2">
        <span className="lmps-field__label">
          Problema identificado
          <HelpTooltip
            content={NC_HELP.form.problemTags}
            ariaLabel="Ajuda: problema identificado"
          />
        </span>
        {form.problem_tags.length ? (
          <div className="lmps-tag-list lmps-tag-list--readonly" aria-label="Tags do problema">
            {form.problem_tags.map((tag) => (
              <span key={tag} className="lmps-tag-chip">
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <p className="lmps-ficha-field__value lmps-muted">—</p>
        )}
      </div>
      <ReadOnlyField
        id="nc-ro-defect"
        label="Descrição do problema"
        hint={NC_HELP.form.defectDescription}
        value={form.defect_description}
        multiline
        wide
      />
      <ReadOnlyField
        id="nc-ro-actions"
        label="Ações / ação corretiva"
        hint={NC_HELP.form.correctiveActions}
        value={form.corrective_actions}
        multiline
        wide
      />
      <ReadOnlyField
        id="nc-ro-opinion"
        label="Parecer técnico"
        hint={NC_HELP.form.technicalOpinion}
        value={form.technical_opinion}
        multiline
        wide
      />
    </ReadOnlyGrid>
  );

  const sectionSaveFooter = (key: NcSectionKey): ReactNode => (
    <FormActions align="end">
      <ActionButton
        type="button"
        variant="primary"
        disabled={busy}
        onClick={() => void persistForm(key)}
      >
        {saving === key ? "Salvando…" : "Salvar"}
      </ActionButton>
    </FormActions>
  );

  const renderSection = (
    key: NcSectionKey,
    title: string,
    hint: string,
    readContent: ReactNode,
    editContent: ReactNode,
  ) => {
    if (isCreate) {
      return (
        <SectionCard title={title} hint={hint}>
          {editContent}
        </SectionCard>
      );
    }

    if (!canWrite) {
      return (
        <SectionCard title={title} hint={hint}>
          <div className="lmps-section-read">{readContent}</div>
        </SectionCard>
      );
    }

    return (
      <EditableSectionCard
        title={title}
        hint={hint}
        isEditing={isEditing(key)}
        onEdit={() => startEdit(key)}
        onCancelEdit={() => cancelSection(key)}
        readContent={readContent}
        editContent={
          <>
            {editContent}
            {sectionSaveFooter(key)}
          </>
        }
      />
    );
  };

  const title = isCreate
    ? "Nova não conformidade"
    : form.sale_number.trim()
      ? `NC · OV ${form.sale_number.trim()}`
      : "Não conformidade";

  return (
    <div className="dashboard-page dashboard-lmps">
      <header className="lmps-page-header">
        <div>
          <p className="lmps-eyebrow">DELPI • Analytics</p>
          <div className="lmps-page-header__title-row">
            <h1>{title}</h1>
            {!isCreate && record ? (
              <StatusBadge
                label={lmpNcStatusLabel(String(record.status))}
                variant={statusVariant(String(record.status))}
              />
            ) : null}
          </div>
          <span className="lmps-page-subtitle">
            {isCreate
              ? "Preencha as seções e salve para registrar a NC."
              : "Detalhe da não conformidade de engenharia"}
          </span>
        </div>
        <div className="lmps-header-actions">
          {!isCreate && canWrite && record ? (
            <div className="lmps-header-action">
              <ActionButton
                type="button"
                variant="ghost"
                disabled={busy}
                onClick={() => void requestDelete()}
              >
                <Trash2 size={16} aria-hidden />
                Excluir
              </ActionButton>
            </div>
          ) : null}
          <div className="lmps-header-action">
            <button
              type="button"
              className={GHOST_BTN}
              onClick={() => navigateLmpsBack(LMPS_ROUTES.nonconformities)}
            >
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </button>
          </div>
        </div>
      </header>

      {error ? (
        <div className="lmps-refreshing-banner" role="alert">
          {error}
        </div>
      ) : null}

      {loading ? (
        <LoadingActivityCard
          title="Carregando não conformidade"
          description="Consultando o registro de NC."
        />
      ) : null}

      {!loading && (isCreate || record) ? (
        <div className="lmps-page-stack lmps-nc-form">
          {formError ? (
            <div className="lmps-refreshing-banner" role="alert">
              {formError}
            </div>
          ) : null}

          {renderSection(
            "identification",
            "Identificação",
            NC_HELP.form.sectionIdentification,
            identificationRead,
            identificationEdit,
          )}
          {renderSection(
            "people",
            "Responsáveis",
            NC_HELP.form.sectionPeople,
            peopleRead,
            peopleEdit,
          )}
          {renderSection(
            "products",
            "Produtos",
            NC_HELP.form.sectionProducts,
            <ProductsReadContent form={form} />,
            productsEdit,
          )}
          {renderSection(
            "description",
            "Descrição",
            NC_HELP.form.sectionDescription,
            descriptionRead,
            descriptionEdit,
          )}

          {isCreate ? (
            <FormActions align="end">
              <ActionButton
                type="button"
                variant="ghost"
                disabled={busy}
                onClick={() => navigateLmpsBack(LMPS_ROUTES.nonconformities)}
              >
                Cancelar
              </ActionButton>
              <ActionButton
                type="button"
                variant="primary"
                disabled={busy}
                onClick={() => void persistForm("create")}
              >
                {saving === "create" ? "Salvando…" : "Salvar"}
              </ActionButton>
            </FormActions>
          ) : recordId ? (
            <NcChangeHistory recordId={recordId} reloadKey={historyReloadKey} />
          ) : null}
        </div>
      ) : null}

      <HostContainedDialog
        open={pending !== null}
        onClose={cancelPending}
        title={pending?.title || "Confirmar"}
      >
        <ConfirmModalPanel
          message={pending?.message ?? "Confirmar ação?"}
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
