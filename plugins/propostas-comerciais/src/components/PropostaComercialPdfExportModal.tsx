import { useEffect, useMemo, useState } from "react";
import { Eye, FileDown, Loader2 } from "lucide-react";

import type { PropostaComercialDetail, PropostaComercialPdfExportOverrides } from "../types/propostasComerciais";
import { displayValue } from "../utils/format";
import { ItensTable } from "./ItensTable";
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
  condicaoIpi: string;
  condicaoFrete: string;
  condicaoEmbalagem: string;
  vendedorNome: string;
  vendedorCargo: string;
  vendedorEmail: string;
  vendedorTelefone: string;
};

function buildDraft(detail: PropostaComercialDetail): DraftState {
  return {
    observacoes: detail.observacoes ?? "",
    contatoNome: detail.contato.nome ?? "",
    contatoDepartamento: detail.contato.departamento ?? "",
    contatoEmail: detail.contato.email ?? "",
    contatoTelefone: detail.contato.telefone ?? "",
    condicaoDescricao: detail.condicoes.descricao ?? "",
    condicaoIcms: detail.condicoes.icms ?? "",
    condicaoIpi: detail.condicoes.ipi ?? "",
    condicaoFrete: detail.condicoes.frete ?? "",
    condicaoEmbalagem: detail.condicoes.embalagem ?? "",
    vendedorNome: detail.vendedor.nome ?? "",
    vendedorCargo: detail.vendedor.cargo ?? "",
    vendedorEmail: detail.vendedor.email ?? "",
    vendedorTelefone: detail.vendedor.telefone ?? "",
  };
}

function buildOverrides(draft: DraftState): PropostaComercialPdfExportOverrides {
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
        <textarea
          rows={4}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <input type="text" value={value} onChange={(event) => onChange(event.target.value)} />
      )}
    </label>
  );
}

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

  const overrides = useMemo(() => buildOverrides(draft), [draft]);

  const updateDraft = (patch: Partial<DraftState>) => {
    setDraft((current) => ({ ...current, ...patch }));
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
        não alteram a proposta no Protheus.
      </p>

      {error ? (
        <div className="pc-modal__error" role="alert">
          {error}
        </div>
      ) : null}

      <section className="pc-export-section">
        <h3>Resumo da proposta</h3>
        <dl className="pc-export-summary">
          <div>
            <dt>Nº OV</dt>
            <dd>{displayValue(detail.cabecalho.numero_ov)}</dd>
          </div>
          <div>
            <dt>Data</dt>
            <dd>{displayValue(detail.cabecalho.data)}</dd>
          </div>
          <div>
            <dt>Versão</dt>
            <dd>{displayValue(detail.cabecalho.versao)}</dd>
          </div>
          <div>
            <dt>Total R$/mil</dt>
            <dd>{displayValue(detail.cabecalho.soma_valores_r_mil)}</dd>
          </div>
          <div className="pc-export-summary__wide">
            <dt>Empresa</dt>
            <dd>{displayValue(detail.empresa.nome)}</dd>
          </div>
          <div className="pc-export-summary__wide">
            <dt>Cliente</dt>
            <dd>{displayValue(detail.cliente.nome)}</dd>
          </div>
        </dl>
      </section>

      <section className="pc-export-section">
        <h3>Itens ({detail.itens.length})</h3>
        <div className="pc-table-wrap">
          <ItensTable items={detail.itens} />
        </div>
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
