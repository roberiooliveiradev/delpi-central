import { useEffect, useMemo, useState } from "react";
import { Eye, FileDown, Loader2 } from "lucide-react";

import {
  DEFAULT_ITEM_COLUMN_LABELS,
  DEFAULT_RESUMO_LABELS,
  buildDefaultRotulosDraft,
  type PropostaComercialItemColumnKey,
  type PropostaComercialResumoLabelKey,
  type PropostaComercialRotulosDraft,
} from "../constants/propostaComercialLabels";
import type {
  PropostaComercialDetail,
  PropostaComercialItem,
  PropostaComercialItemTextDraft,
  PropostaComercialPdfExportOverrides,
  PropostaComercialPdfItemTextOverrides,
  PropostaComercialPdfRotulosOverrides,
} from "../types/propostasComerciais";
import { displayValue } from "../utils/format";
import { ItensTable } from "./ItensTable";
import { PcNativeTextAreaControl } from "./pcFormFields";
import { PropostaComercialModal } from "./PropostaComercialModal";

type PropostaComercialPdfExportModalProps = {
  open: boolean;
  detail: PropostaComercialDetail;
  loading: boolean;
  error: string | null;
  onClose: () => void;
  onPreview: (overrides: PropostaComercialPdfExportOverrides) => Promise<void>;
  onExport: (overrides: PropostaComercialPdfExportOverrides) => Promise<void>;
  previewUrl: string | null;
  onClearPreview: () => void;
};

type DraftState = {
  observacoes: string;
  contatoNome: string;
  contatoDepartamento: string;
  contatoEmail: string;
  contatoTelefone: string;
  condicaoDescricao: string;
  condicaoIcms: string;
  condicaoPisCofins: string;
  condicaoIpi: string;
  condicaoFrete: string;
  condicaoEmbalagem: string;
  vendedorNome: string;
  vendedorCargo: string;
  vendedorEmail: string;
  vendedorTelefone: string;
  itemDrafts: PropostaComercialItemTextDraft[];
  rotulos: PropostaComercialRotulosDraft;
  exibirColunaValorLiquido: boolean;
};

function buildItemDrafts(items: PropostaComercialItem[]): PropostaComercialItemTextDraft[] {
  return items.map((item) => ({
    item: item.item,
    descricao: item.descricao ?? "",
    referencia_cliente: item.referencia_cliente ?? "",
    ncm: item.ncm ?? "",
    prazo_dias: item.prazo_dias != null ? String(item.prazo_dias) : "",
  }));
}

function buildDraft(detail: PropostaComercialDetail): DraftState {
  return {
    observacoes: detail.observacoes ?? "",
    contatoNome: detail.contato.nome ?? "",
    contatoDepartamento: detail.contato.departamento ?? "",
    contatoEmail: detail.contato.email ?? "",
    contatoTelefone: detail.contato.telefone ?? "",
    condicaoDescricao: detail.condicoes.descricao ?? "",
    condicaoIcms: detail.condicoes.icms ?? "",
    condicaoPisCofins: detail.condicoes.pis_cofins ?? "9,25% INCLUSO",
    condicaoIpi: detail.condicoes.ipi ?? "",
    condicaoFrete: detail.condicoes.frete ?? "",
    condicaoEmbalagem: detail.condicoes.embalagem ?? "",
    vendedorNome: detail.vendedor.nome ?? "",
    vendedorCargo: detail.vendedor.cargo ?? "",
    vendedorEmail: detail.vendedor.email ?? "",
    vendedorTelefone: detail.vendedor.telefone ?? "",
    itemDrafts: buildItemDrafts(detail.itens),
    rotulos: buildDefaultRotulosDraft(),
    exibirColunaValorLiquido: true,
  };
}

function buildChangedStringMap<T extends string>(
  current: Record<T, string>,
  defaults: Record<T, string>,
): Partial<Record<T, string>> | undefined {
  const changes = {} as Partial<Record<T, string>>;

  for (const key of Object.keys(defaults) as T[]) {
    if (current[key] !== defaults[key]) {
      changes[key] = current[key];
    }
  }

  return Object.keys(changes).length > 0 ? changes : undefined;
}

function buildRotulosOverrides(rotulos: PropostaComercialRotulosDraft): PropostaComercialPdfRotulosOverrides | undefined {
  const colunas_itens = buildChangedStringMap(rotulos.colunas_itens, DEFAULT_ITEM_COLUMN_LABELS);
  const resumo = buildChangedStringMap(rotulos.resumo, DEFAULT_RESUMO_LABELS);

  if (!colunas_itens && !resumo) {
    return undefined;
  }

  return {
    ...(colunas_itens ? { colunas_itens } : {}),
    ...(resumo ? { resumo } : {}),
  };
}

function buildItemOverrides(
  itemDrafts: PropostaComercialItemTextDraft[],
  originalItems: PropostaComercialItem[],
): PropostaComercialPdfItemTextOverrides[] | undefined {
  const overrides: PropostaComercialPdfItemTextOverrides[] = [];

  itemDrafts.forEach((draft, index) => {
    const original = originalItems[index];
    if (!original || original.item !== draft.item) {
      return;
    }

    const patch: PropostaComercialPdfItemTextOverrides = { item: draft.item };
    let hasChange = false;

    if (draft.descricao !== (original.descricao ?? "")) {
      patch.descricao = draft.descricao;
      hasChange = true;
    }
    if (draft.referencia_cliente !== (original.referencia_cliente ?? "")) {
      patch.referencia_cliente = draft.referencia_cliente;
      hasChange = true;
    }
    if (draft.ncm !== (original.ncm ?? "")) {
      patch.ncm = draft.ncm;
      hasChange = true;
    }
    if (draft.prazo_dias !== (original.prazo_dias != null ? String(original.prazo_dias) : "")) {
      patch.prazo_dias = draft.prazo_dias;
      hasChange = true;
    }

    if (hasChange) {
      overrides.push(patch);
    }
  });

  return overrides.length > 0 ? overrides : undefined;
}

function buildOverrides(
  draft: DraftState,
  originalItems: PropostaComercialItem[],
): PropostaComercialPdfExportOverrides {
  const itemOverrides = buildItemOverrides(draft.itemDrafts, originalItems);
  const rotulosOverrides = buildRotulosOverrides(draft.rotulos);

  return {
    observacoes: draft.observacoes,
    contato: {
      nome: draft.contatoNome,
      departamento: draft.contatoDepartamento,
      email: draft.contatoEmail,
      telefone: draft.contatoTelefone || null,
    },
    condicoes: {
      descricao: draft.condicaoDescricao,
      icms: draft.condicaoIcms || null,
      pis_cofins: draft.condicaoPisCofins,
      ipi: draft.condicaoIpi,
      frete: draft.condicaoFrete,
      embalagem: draft.condicaoEmbalagem,
    },
    vendedor: {
      nome: draft.vendedorNome,
      cargo: draft.vendedorCargo,
      email: draft.vendedorEmail,
      telefone: draft.vendedorTelefone || null,
    },
    ...(itemOverrides ? { itens: itemOverrides } : {}),
    ...(rotulosOverrides ? { rotulos: rotulosOverrides } : {}),
    ...(draft.exibirColunaValorLiquido ? {} : { exibir_coluna_valor_liquido: false }),
  };
}

function Field({
  label,
  value,
  onChange,
  wide = false,
  multiline = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  wide?: boolean;
  multiline?: boolean;
}) {
  return (
    <label className={`pc-form-field${wide ? " pc-form-field--wide" : ""}`}>
      <span>{label}</span>
      {multiline ? (
        <PcNativeTextAreaControl rows={4} value={value} onChange={onChange} />
      ) : (
        <input type="text" value={value} onChange={(event) => onChange(event.target.value)} />
      )}
    </label>
  );
}

function SummaryLabelInput({
  value,
  onChange,
  "aria-label": ariaLabel,
}: {
  value: string;
  onChange: (value: string) => void;
  "aria-label": string;
}) {
  return (
    <input
      type="text"
      className="pc-summary-label-input"
      value={value}
      aria-label={ariaLabel}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

const RESUMO_FIELDS: Array<{
  key: PropostaComercialResumoLabelKey;
  wide?: boolean;
  value: (detail: PropostaComercialDetail) => string;
}> = [
  { key: "numero_ov", value: (detail) => displayValue(detail.cabecalho.numero_ov) },
  { key: "data", value: (detail) => displayValue(detail.cabecalho.data) },
  { key: "versao", value: (detail) => displayValue(detail.cabecalho.versao) },
  { key: "total_r_mil", value: (detail) => displayValue(detail.cabecalho.soma_valores_r_mil) },
  { key: "empresa", wide: true, value: (detail) => displayValue(detail.empresa.nome) },
  { key: "cliente", wide: true, value: (detail) => displayValue(detail.cliente.nome) },
];

export function PropostaComercialPdfExportModal({
  open,
  detail,
  loading,
  error,
  onClose,
  onPreview,
  onExport,
  previewUrl,
  onClearPreview,
}: PropostaComercialPdfExportModalProps) {
  const [draft, setDraft] = useState<DraftState>(() => buildDraft(detail));

  useEffect(() => {
    if (open) {
      setDraft(buildDraft(detail));
      onClearPreview();
    }
  }, [detail, open, onClearPreview]);

  const overrides = useMemo(() => buildOverrides(draft, detail.itens), [draft, detail.itens]);

  const updateDraft = (patch: Partial<DraftState>) => {
    setDraft((current) => ({ ...current, ...patch }));
    onClearPreview();
  };

  const updateItemField = (
    itemKey: string,
    field: keyof Pick<
      PropostaComercialItemTextDraft,
      "descricao" | "referencia_cliente" | "ncm" | "prazo_dias"
    >,
    value: string,
  ) => {
    setDraft((current) => ({
      ...current,
      itemDrafts: current.itemDrafts.map((itemDraft) =>
        itemDraft.item === itemKey ? { ...itemDraft, [field]: value } : itemDraft,
      ),
    }));
    onClearPreview();
  };

  const updateColumnLabel = (field: PropostaComercialItemColumnKey, value: string) => {
    setDraft((current) => ({
      ...current,
      rotulos: {
        ...current.rotulos,
        colunas_itens: {
          ...current.rotulos.colunas_itens,
          [field]: value,
        },
      },
    }));
    onClearPreview();
  };

  const updateResumoLabel = (field: PropostaComercialResumoLabelKey, value: string) => {
    setDraft((current) => ({
      ...current,
      rotulos: {
        ...current.rotulos,
        resumo: {
          ...current.rotulos.resumo,
          [field]: value,
        },
      },
    }));
    onClearPreview();
  };

  const footer = (
    <div className="pc-modal__footer-actions">
      <button type="button" className="pc-btn pc-btn--ghost" onClick={onClose} disabled={loading}>
        Cancelar
      </button>
      <button
        type="button"
        className="pc-btn pc-btn--ghost"
        onClick={() => void onPreview(overrides)}
        disabled={loading}
      >
        {loading ? (
          <Loader2 size={16} className="pc-spin" aria-hidden="true" />
        ) : (
          <Eye size={16} aria-hidden="true" />
        )}
        Visualizar PDF
      </button>
      <button
        type="button"
        className="pc-btn pc-btn--primary"
        onClick={() => void onExport(overrides)}
        disabled={loading}
      >
        {loading ? (
          <Loader2 size={16} className="pc-spin" aria-hidden="true" />
        ) : (
          <FileDown size={16} aria-hidden="true" />
        )}
        Exportar PDF
      </button>
    </div>
  );

  return (
    <PropostaComercialModal
      open={open}
      title="Revisar antes de exportar"
      subtitle={`Proposta ${displayValue(detail.cabecalho.numero_ov)} · ${displayValue(detail.cliente.nome)}`}
      onClose={onClose}
      footer={footer}
    >
      <p className="pc-modal__intro">
        Revise o conteúdo que irá para o PDF. Os ajustes abaixo valem apenas para esta exportação e
        não alteram a proposta no Protheus. É possível editar rótulos do resumo, colunas da tabela e
        os textos de descrição, referência do cliente e NCM (o NCM é exibido em Observações no PDF).
      </p>

      {error ? (
        <div className="pc-modal__error" role="alert">
          {error}
        </div>
      ) : null}

      <section className="pc-export-section">
        <h3>Resumo da proposta</h3>
        <dl className="pc-export-summary">
          {RESUMO_FIELDS.map((field) => (
            <div
              key={field.key}
              className={field.wide ? "pc-export-summary__wide" : undefined}
            >
              <dt>
                <SummaryLabelInput
                  aria-label={`Rótulo ${draft.rotulos.resumo[field.key]}`}
                  value={draft.rotulos.resumo[field.key]}
                  onChange={(value) => updateResumoLabel(field.key, value)}
                />
              </dt>
              <dd>{field.value(detail)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="pc-export-section">
        <h3>Itens ({detail.itens.length})</h3>
        <label className="pc-export-option">
          <input
            type="checkbox"
            checked={draft.exibirColunaValorLiquido}
            onChange={(event) => {
              updateDraft({ exibirColunaValorLiquido: event.target.checked });
              onClearPreview();
            }}
          />
          <span>Exibir coluna Líquido R$/mil no PDF</span>
        </label>
        <ItensTable
          items={detail.itens}
          editable
          itemDrafts={draft.itemDrafts}
          columnLabels={draft.rotulos.colunas_itens}
          onItemFieldChange={updateItemField}
          onColumnLabelChange={updateColumnLabel}
        />
      </section>

      <section className="pc-export-section">
        <h3>Contato no PDF</h3>
        <div className="pc-form-grid">
          <Field label="Nome" value={draft.contatoNome} onChange={(value) => updateDraft({ contatoNome: value })} />
          <Field
            label="Departamento"
            value={draft.contatoDepartamento}
            onChange={(value) => updateDraft({ contatoDepartamento: value })}
          />
          <Field
            label="E-mail"
            value={draft.contatoEmail}
            onChange={(value) => updateDraft({ contatoEmail: value })}
            wide
          />
          <Field
            label="Telefone"
            value={draft.contatoTelefone}
            onChange={(value) => updateDraft({ contatoTelefone: value })}
          />
        </div>
      </section>

      <section className="pc-export-section">
        <h3>Condições comerciais</h3>
        <div className="pc-form-grid">
          <Field
            label="Condição de pagamento"
            value={draft.condicaoDescricao}
            onChange={(value) => updateDraft({ condicaoDescricao: value })}
            wide
          />
          <Field
            label="ICMS"
            value={draft.condicaoIcms}
            onChange={(value) => updateDraft({ condicaoIcms: value })}
          />
          <Field
            label="PIS/COFINS"
            value={draft.condicaoPisCofins}
            onChange={(value) => updateDraft({ condicaoPisCofins: value })}
          />
          <Field label="IPI" value={draft.condicaoIpi} onChange={(value) => updateDraft({ condicaoIpi: value })} />
          <Field
            label="Embalagem"
            value={draft.condicaoEmbalagem}
            onChange={(value) => updateDraft({ condicaoEmbalagem: value })}
          />
          <Field
            label="Frete"
            value={draft.condicaoFrete}
            onChange={(value) => updateDraft({ condicaoFrete: value })}
            wide
          />
        </div>
      </section>

      <section className="pc-export-section">
        <h3>Observações</h3>
        <Field
          label="Texto das observações"
          value={draft.observacoes}
          onChange={(value) => updateDraft({ observacoes: value })}
          wide
          multiline
        />
      </section>

      <section className="pc-export-section">
        <h3>Assinatura do vendedor</h3>
        <div className="pc-form-grid">
          <Field
            label="Nome"
            value={draft.vendedorNome}
            onChange={(value) => updateDraft({ vendedorNome: value })}
          />
          <Field
            label="Cargo"
            value={draft.vendedorCargo}
            onChange={(value) => updateDraft({ vendedorCargo: value })}
          />
          <Field
            label="Telefone"
            value={draft.vendedorTelefone}
            onChange={(value) => updateDraft({ vendedorTelefone: value })}
          />
          <Field
            label="E-mail"
            value={draft.vendedorEmail}
            onChange={(value) => updateDraft({ vendedorEmail: value })}
            wide
          />
        </div>
      </section>

      {previewUrl ? (
        <section className="pc-export-section pc-export-preview">
          <h3>Pré-visualização do PDF</h3>
          <iframe title="Pré-visualização do PDF da proposta" src={previewUrl} className="pc-export-preview__frame" />
        </section>
      ) : null}
    </PropostaComercialModal>
  );
}
