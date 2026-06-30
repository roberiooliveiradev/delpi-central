import { ArrowLeft, FileDown } from "lucide-react";

import { InfoCard, InfoGrid } from "../components/InfoCard";
import { ItensTable } from "../components/ItensTable";
import { PageHeader } from "../components/PageHeader";
import { PropostaComercialPdfExportModal } from "../components/PropostaComercialPdfExportModal";
import { StateBox } from "../components/StateBox";
import { StatusBadge } from "../components/StatusBadge";
import { usePropostaComercialDetail } from "../hooks/usePropostaComercialDetail";
import { usePropostaComercialPdf } from "../hooks/usePropostaComercialPdf";
import { displayValue } from "../utils/format";
import { navigatePropostasList } from "../utils/navigation";

type PropostaComercialDetailPageProps = {
  propostaInterna: string;
};

export function PropostaComercialDetailPage({ propostaInterna }: PropostaComercialDetailPageProps) {
  const { data, loading, error, reload } = usePropostaComercialDetail(propostaInterna);
  const {
    exportModalOpen,
    loading: pdfLoading,
    error: pdfError,
    previewUrl,
    openExportModal,
    closeExportModal,
    clearPreview,
    previewPdf,
    exportPdf,
    clearError: clearPdfError,
  } = usePropostaComercialPdf(propostaInterna);

  const cabecalho = data?.cabecalho;

  return (
    <>
      <PageHeader
        title={cabecalho?.numero_ov || "Proposta Comercial"}
        subtitle={
          data
            ? `${displayValue(data.cliente.nome)} · Proposta ${displayValue(data.cabecalho.proposta_interna)}`
            : `Proposta ${propostaInterna}`
        }
        loading={loading}
        onRefresh={reload}
        actions={
          <>
            <button
              type="button"
              className="pc-btn pc-btn--primary"
              onClick={() => {
                clearPdfError();
                openExportModal();
              }}
              disabled={loading || !data}
            >
              <FileDown size={16} aria-hidden="true" />
              Emitir PDF
            </button>
            <button type="button" className="pc-btn pc-btn--ghost" onClick={navigatePropostasList}>
              <ArrowLeft size={16} aria-hidden="true" />
              Voltar
            </button>
          </>
        }
      />

      {data ? (
        <PropostaComercialPdfExportModal
          open={exportModalOpen}
          detail={data}
          loading={pdfLoading}
          error={pdfError}
          onClose={closeExportModal}
          onPreview={previewPdf}
          onExport={exportPdf}
          previewUrl={previewUrl}
          onClearPreview={clearPreview}
        />
      ) : null}

      {loading ? (
        <StateBox variant="loading" title="Carregando proposta" message="Consultando detalhes no Protheus." />
      ) : null}

      {!loading && error ? (
        <StateBox
          variant="error"
          title="Proposta não disponível"
          message={error}
          action={
            <button type="button" className="pc-btn pc-btn--primary" onClick={reload}>
              Tentar novamente
            </button>
          }
        />
      ) : null}

      {!loading && !error && data ? (
        <div className="pc-detail-layout">
          <InfoCard title="Cabeçalho" highlight>
            <div className="pc-highlight-row">
              <div>
                <span className="pc-highlight-label">Nº OV</span>
                <strong className="pc-highlight-value">{displayValue(data.cabecalho.numero_ov)}</strong>
              </div>
              <div>
                <span className="pc-highlight-label">Cliente</span>
                <strong className="pc-highlight-value">{displayValue(data.cliente.nome)}</strong>
              </div>
              <div>
                <span className="pc-highlight-label">Data</span>
                <strong className="pc-highlight-value">{displayValue(data.cabecalho.data)}</strong>
              </div>
              <div>
                <span className="pc-highlight-label">Versão</span>
                <strong className="pc-highlight-value">{displayValue(data.cabecalho.versao)}</strong>
              </div>
              <div>
                <span className="pc-highlight-label">Soma R$/mil</span>
                <strong className="pc-highlight-value">
                  {displayValue(data.cabecalho.soma_valores_r_mil)}
                </strong>
              </div>
              <div>
                <span className="pc-highlight-label">Status</span>
                <StatusBadge status={data.cabecalho.status} />
              </div>
            </div>
            <InfoGrid
              items={[
                { label: "Proposta interna", value: displayValue(data.cabecalho.proposta_interna) },
                { label: "Oportunidade", value: displayValue(data.cabecalho.oportunidade) },
                { label: "Revisão OV", value: displayValue(data.cabecalho.revisao_oportunidade) },
                { label: "Filial", value: displayValue(data.cabecalho.filial) },
                { label: "Validade (dias)", value: displayValue(data.cabecalho.validade_dias) },
              ]}
            />
          </InfoCard>

          <div className="pc-detail-grid">
            <InfoCard title="Empresa">
              <InfoGrid
                items={[
                  { label: "Razão social", value: displayValue(data.empresa.nome), wide: true },
                  { label: "CNPJ", value: displayValue(data.empresa.cnpj) },
                  { label: "IE", value: displayValue(data.empresa.inscricao_estadual) },
                  { label: "Site", value: displayValue(data.empresa.site) },
                  { label: "Telefone", value: displayValue(data.empresa.telefone) },
                  { label: "Endereço", value: displayValue(data.empresa.endereco), wide: true },
                  {
                    label: "Cidade/UF",
                    value: `${displayValue(data.empresa.cidade)} / ${displayValue(data.empresa.uf)}`,
                  },
                  { label: "CEP", value: displayValue(data.empresa.cep) },
                ]}
              />
            </InfoCard>

            <InfoCard title="Cliente">
              <InfoGrid
                items={[
                  { label: "Nome", value: displayValue(data.cliente.nome), wide: true },
                  { label: "Código", value: displayValue(data.cliente.codigo) },
                  { label: "CNPJ", value: displayValue(data.cliente.cnpj) },
                  { label: "Telefone", value: displayValue(data.cliente.telefone) },
                  { label: "Endereço", value: displayValue(data.cliente.endereco), wide: true },
                  {
                    label: "Cidade/UF",
                    value: `${displayValue(data.cliente.cidade)} / ${displayValue(data.cliente.uf)}`,
                  },
                ]}
              />
            </InfoCard>

            <InfoCard title="Contato">
              <InfoGrid
                items={[
                  { label: "Nome", value: displayValue(data.contato.nome) },
                  { label: "Departamento", value: displayValue(data.contato.departamento) },
                  { label: "E-mail", value: displayValue(data.contato.email), wide: true },
                  { label: "Telefone", value: displayValue(data.contato.telefone) },
                ]}
              />
            </InfoCard>

            <InfoCard title="Condições comerciais">
              <InfoGrid
                items={[
                  { label: "Código", value: displayValue(data.condicoes.codigo) },
                  { label: "Descrição", value: displayValue(data.condicoes.descricao), wide: true },
                  { label: "ICMS", value: displayValue(data.condicoes.icms) },
                  { label: "PIS/COFINS", value: displayValue(data.condicoes.pis_cofins) },
                  { label: "IPI", value: displayValue(data.condicoes.ipi) },
                  { label: "Embalagem", value: displayValue(data.condicoes.embalagem) },
                  { label: "Frete", value: displayValue(data.condicoes.frete) },
                ]}
              />
            </InfoCard>

            <InfoCard title="Vendedor">
              <InfoGrid
                items={[
                  { label: "Nome", value: displayValue(data.vendedor.nome) },
                  { label: "Cargo", value: displayValue(data.vendedor.cargo) },
                  { label: "E-mail", value: displayValue(data.vendedor.email), wide: true },
                  { label: "Telefone", value: displayValue(data.vendedor.telefone) },
                ]}
              />
            </InfoCard>
          </div>

          <InfoCard title="Observações">
            <p className="pc-observacoes">
              {data.observacoes.trim() ? data.observacoes : "Sem observações registradas."}
            </p>
          </InfoCard>

          <InfoCard title={`Itens (${data.itens.length})`}>
            <ItensTable items={data.itens} />
          </InfoCard>
        </div>
      ) : null}
    </>
  );
}
