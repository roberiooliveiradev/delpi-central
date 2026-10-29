import { useCallback, useEffect, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDateField,
  EngineeringEmptyState,
  EngineeringLoadingActivityCard,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../../../ui/engineeringUi";
import {
  createNonconformity,
  fetchNonconformity,
  fetchProblemTags,
  updateNonconformity,
} from "../api/nonconformityApi";
import { NC_HELP, NC_STATUS_LABELS } from "../ncCopy";
import { NC_PATHS, navigateNc } from "../nonconformityRoutes";
import type { NcPayload, NcProduct, NcStatus } from "../types";

type FormState = {
  status: NcStatus;
  sale_number: string;
  lmp_number: string;
  customer_name: string;
  occurrence_date: string;
  launch_date: string;
  last_revision_date: string;
  executed_by: string;
  released_by: string;
  defect_description: string;
  corrective_actions: string;
  technical_opinion: string;
  problem_tags: string[];
  products: NcProduct[];
};

const EMPTY_FORM: FormState = {
  status: "open",
  sale_number: "",
  lmp_number: "",
  customer_name: "",
  occurrence_date: "",
  launch_date: "",
  last_revision_date: "",
  executed_by: "",
  released_by: "",
  defect_description: "",
  corrective_actions: "",
  technical_opinion: "",
  problem_tags: [],
  products: [],
};

function blank(value: string): string | null {
  const text = value.trim();
  return text || null;
}

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof HomeApiError) return error.message;
  return fallback;
}

export function NonconformityFormPage({
  mode,
  recordId,
}: {
  mode: "create" | "edit";
  recordId?: string;
}) {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [etag, setEtag] = useState<string | null>(null);
  const [knownTags, setKnownTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [loading, setLoading] = useState(mode === "edit");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetchProblemTags()
      .then((tags) => {
        if (!cancelled) setKnownTags(tags.map((t) => t.label));
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const load = useCallback(async () => {
    if (mode !== "edit" || !recordId) return;
    setLoading(true);
    try {
      const record = await fetchNonconformity(recordId);
      setForm({
        status: record.status,
        sale_number: record.sale_number ?? "",
        lmp_number: record.lmp_number ?? "",
        customer_name: record.customer_name ?? "",
        occurrence_date: record.occurrence_date ?? "",
        launch_date: record.launch_date ?? "",
        last_revision_date: record.last_revision_date ?? "",
        executed_by: record.executed_by ?? "",
        released_by: record.released_by ?? "",
        defect_description: record.defect_description ?? "",
        corrective_actions: record.corrective_actions ?? "",
        technical_opinion: record.technical_opinion ?? "",
        problem_tags: record.problem_tags,
        products: record.products.map((p) => ({
          product_code: p.product_code,
          product_description: p.product_description,
        })),
      });
      setEtag(record.updated_at);
    } catch (err) {
      if (err instanceof HomeApiError && err.status === 404) {
        setNotFound(true);
      } else {
        setError(errorMessage(err, "Não foi possível carregar o registro."));
      }
    } finally {
      setLoading(false);
    }
  }, [mode, recordId]);

  useEffect(() => {
    void load();
  }, [load]);

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((f) => ({ ...f, [key]: value }));

  const addTag = (label: string) => {
    const text = label.trim().slice(0, 80);
    if (!text) return;
    setForm((f) =>
      f.problem_tags.some((t) => t.toLowerCase() === text.toLowerCase())
        ? f
        : { ...f, problem_tags: [...f.problem_tags, text] },
    );
    setTagInput("");
  };

  const removeTag = (label: string) =>
    setForm((f) => ({
      ...f,
      problem_tags: f.problem_tags.filter((t) => t !== label),
    }));

  const setProduct = (index: number, patch: Partial<NcProduct>) =>
    setForm((f) => ({
      ...f,
      products: f.products.map((p, i) =>
        i === index ? { ...p, ...patch } : p,
      ),
    }));

  const onSubmit = async () => {
    setError(null);
    if (mode === "edit" && !form.occurrence_date.trim()) {
      setError("Data de ocorrência é obrigatória.");
      return;
    }
    const payload: NcPayload = {
      status: form.status,
      sale_number: blank(form.sale_number),
      lmp_number: blank(form.lmp_number),
      customer_name: blank(form.customer_name),
      occurrence_date: blank(form.occurrence_date),
      launch_date: blank(form.launch_date),
      last_revision_date: blank(form.last_revision_date),
      executed_by: blank(form.executed_by),
      released_by: blank(form.released_by),
      defect_description: blank(form.defect_description),
      corrective_actions: blank(form.corrective_actions),
      technical_opinion: blank(form.technical_opinion),
      problem_tags: form.problem_tags,
      products: form.products.filter((p) => p.product_code.trim()),
      ...(mode === "edit" ? { expected_updated_at: etag } : {}),
    };
    setSaving(true);
    try {
      const saved =
        mode === "create"
          ? await createNonconformity(payload)
          : await updateNonconformity(recordId!, payload);
      navigateNc(NC_PATHS.detail(saved.id));
    } catch (err) {
      setError(errorMessage(err, "Falha ao salvar a não conformidade."));
    } finally {
      setSaving(false);
    }
  };

  const title =
    mode === "create" ? "Nova não conformidade" : "Editar não conformidade";

  return (
    <main className="engineering-nonconformities">
      <EngineeringPagePath
        back={{
          label: "Não conformidades",
          href: NC_PATHS.list,
          onNavigate: (event) => {
            event.preventDefault();
            navigateNc(NC_PATHS.list);
          },
        }}
        items={[]}
        current={title}
      />

      <EngineeringPageHero
        eyebrow="Portal Engenharia • Não conformidades"
        title={title}
        description="Registro oficial via Engineering API — alterações geram histórico de auditoria com seu usuário."
      />

      {loading ? (
        <EngineeringLoadingActivityCard
          title="Carregando registro"
          description="Consultando os dados atuais da não conformidade."
        />
      ) : null}

      {notFound ? (
        <EngineeringEmptyState message="Não conformidade não encontrada.">
          <EngineeringActionButton
            variant="primary"
            onClick={() => navigateNc(NC_PATHS.list)}
          >
            Voltar à listagem
          </EngineeringActionButton>
        </EngineeringEmptyState>
      ) : null}

      {error ? (
        <EngineeringStateBanner variant="error">
          {`Não foi possível salvar — ${error}`}
        </EngineeringStateBanner>
      ) : null}

      {!loading && !notFound ? (
        <>
          <EngineeringSectionCard title="Identificação">
            <div className="engineering-nc-form-grid">
              <label className="engineering-nc-field">
                <span>OV</span>
                <input
                  value={form.sale_number}
                  onChange={(e) => set("sale_number", e.target.value)}
                  maxLength={20}
                  placeholder="Número da OV"
                />
              </label>
              <label className="engineering-nc-field">
                <span>LMP</span>
                <input
                  value={form.lmp_number}
                  onChange={(e) => set("lmp_number", e.target.value)}
                  maxLength={40}
                  placeholder="Número da LMP (opcional)"
                />
              </label>
              <label className="engineering-nc-field">
                <span>Cliente</span>
                <input
                  value={form.customer_name}
                  onChange={(e) => set("customer_name", e.target.value)}
                  maxLength={200}
                  placeholder="Nome do cliente"
                />
              </label>
              <label className="engineering-nc-field">
                <span>Status</span>
                <select
                  value={form.status}
                  onChange={(e) => set("status", e.target.value as NcStatus)}
                >
                  {(Object.keys(NC_STATUS_LABELS) as NcStatus[]).map((s) => (
                    <option key={s} value={s}>
                      {NC_STATUS_LABELS[s]}
                    </option>
                  ))}
                </select>
              </label>
              <EngineeringDateField
                hint={NC_HELP.occurrenceDate}
                label={`Data de ocorrência${mode === "edit" ? " *" : ""}`}
                type="date"
                value={form.occurrence_date}
                onChange={(v) => set("occurrence_date", v)}
              />
              <EngineeringDateField
                label="Data de lançamento"
                type="date"
                value={form.launch_date}
                onChange={(v) => set("launch_date", v)}
              />
              <EngineeringDateField
                label="Última revisão"
                type="date"
                value={form.last_revision_date}
                onChange={(v) => set("last_revision_date", v)}
              />
              <label className="engineering-nc-field">
                <span>Executado por</span>
                <input
                  value={form.executed_by}
                  onChange={(e) => set("executed_by", e.target.value)}
                  maxLength={200}
                />
              </label>
              <label className="engineering-nc-field">
                <span>Liberado por</span>
                <input
                  value={form.released_by}
                  onChange={(e) => set("released_by", e.target.value)}
                  maxLength={200}
                />
              </label>
            </div>
          </EngineeringSectionCard>

          <EngineeringSectionCard title="Problema e tratativa">
            <label className="engineering-nc-field engineering-nc-field--block">
              <span>Descrição do problema</span>
              <textarea
                className="engineering-nc-textarea"
                rows={3}
                value={form.defect_description}
                onChange={(e) => set("defect_description", e.target.value)}
              />
            </label>
            <label className="engineering-nc-field engineering-nc-field--block">
              <span>Ações corretivas</span>
              <textarea
                className="engineering-nc-textarea"
                rows={3}
                value={form.corrective_actions}
                onChange={(e) => set("corrective_actions", e.target.value)}
              />
            </label>
            <label className="engineering-nc-field engineering-nc-field--block">
              <span>Parecer técnico</span>
              <textarea
                className="engineering-nc-textarea"
                rows={3}
                value={form.technical_opinion}
                onChange={(e) => set("technical_opinion", e.target.value)}
              />
            </label>
          </EngineeringSectionCard>

          <EngineeringSectionCard
            title="Problemas identificados"
            subtitle="Tags compartilhadas — selecione do catálogo ou crie novas (até 80 caracteres)."
          >
            <div className="engineering-nc-tag-editor">
              {form.problem_tags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  className="engineering-nc-tag"
                  onClick={() => removeTag(tag)}
                  title="Remover tag"
                >
                  {tag} ×
                </button>
              ))}
              <input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag(tagInput);
                  }
                }}
                list="engineering-nc-known-tags"
                placeholder="Adicionar tag e Enter"
                maxLength={80}
                aria-label="Adicionar tag de problema"
              />
              <datalist id="engineering-nc-known-tags">
                {knownTags.map((tag) => (
                  <option key={tag} value={tag} />
                ))}
              </datalist>
              <EngineeringActionButton
                variant="ghost"
                onClick={() => addTag(tagInput)}
              >
                Adicionar
              </EngineeringActionButton>
            </div>
          </EngineeringSectionCard>

          <EngineeringSectionCard
            title="Produtos associados"
            subtitle={`${form.products.length} item(ns) — códigos são normalizados para maiúsculas.`}
          >
            {form.products.map((product, index) => (
              <div key={index} className="engineering-nc-product-row">
                <input
                  value={product.product_code}
                  onChange={(e) =>
                    setProduct(index, { product_code: e.target.value })
                  }
                  placeholder="Código do produto"
                  maxLength={60}
                  aria-label={`Código do produto ${index + 1}`}
                />
                <input
                  value={product.product_description ?? ""}
                  onChange={(e) =>
                    setProduct(index, {
                      product_description: e.target.value,
                    })
                  }
                  placeholder="Descrição"
                  maxLength={255}
                  aria-label={`Descrição do produto ${index + 1}`}
                />
                <EngineeringActionButton
                  variant="ghost"
                  onClick={() =>
                    setForm((f) => ({
                      ...f,
                      products: f.products.filter((_, i) => i !== index),
                    }))
                  }
                >
                  Remover
                </EngineeringActionButton>
              </div>
            ))}
            <EngineeringActionButton
              variant="ghost"
              onClick={() =>
                setForm((f) => ({
                  ...f,
                  products: [
                    ...f.products,
                    { product_code: "", product_description: "" },
                  ],
                }))
              }
            >
              Adicionar produto
            </EngineeringActionButton>
          </EngineeringSectionCard>

          <div className="engineering-nc-actions engineering-nc-actions--footer">
            <EngineeringActionButton
              variant="primary"
              onClick={() => void onSubmit()}
              disabled={saving}
            >
              {saving ? "Salvando…" : mode === "create" ? "Criar" : "Salvar alterações"}
            </EngineeringActionButton>
            <EngineeringActionButton
              variant="ghost"
              onClick={() =>
                recordId
                  ? navigateNc(NC_PATHS.detail(recordId))
                  : navigateNc(NC_PATHS.list)
              }
              disabled={saving}
            >
              Cancelar
            </EngineeringActionButton>
          </div>
        </>
      ) : null}
    </main>
  );
}
