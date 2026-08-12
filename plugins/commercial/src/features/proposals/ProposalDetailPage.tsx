import {
  EmptyState,
  OPERATIONAL_UNIT_COLUMN_LABEL,
  SectionCard,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { FileDown, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { getProposalDocument, openProposalDocumentPdf } from "../../api/commercialProposalsApi";
import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialDataTable,
  CommercialDetailFieldGrid,
  CommercialLoadingCard,
  CommercialPagePath,
  CommercialTextAreaField,
  CommercialPageHero,
  CommercialActionButton,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { PROPOSALS_CONTENT } from "../../content/analyticsContent";
import type {
  ProposalDocumentDetail,
  ProposalDocumentItem,
  ProposalDocumentPdfExportOverrides,
} from "../../types/proposalsDocument";

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  const text = value.trim();
  return text || "—";
}

type ProposalDetailPageProps = {
  basePath: string;
  propostaId: string;
};

export function ProposalDetailPage({ basePath, propostaId }: ProposalDetailPageProps) {
  const { canExportProposals } = usePortfolioScope();
  const [data, setData] = useState<ProposalDocumentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [pdfObservacoes, setPdfObservacoes] = useState("");
  const [pdfContatoNome, setPdfContatoNome] = useState("");
  const [pdfContatoEmail, setPdfContatoEmail] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getProposalDocument(propostaId, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        setData(result);
        setPdfObservacoes(result.observacoes || "");
        setPdfContatoNome(result.contato?.nome || "");
        setPdfContatoEmail(result.contato?.email || "");
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Proposta não disponível.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [propostaId, reloadKey]);

  const itemColumns: DataTableColumn<ProposalDocumentItem>[] = [
    { key: "item", header: "Item", render: (row) => row.item },
    { key: "produto", header: "Produto", render: (row) => row.produto },
    { key: "desc", header: "Descrição", render: (row) => row.descricao || "—" },
    {
      key: "qty",
      header: "Qtd",
      render: (row) => row.quantidade.toLocaleString("pt-BR"),
    },
    { key: "total", header: "Total", render: (row) => row.valor_total || "—" },
    {
      key: "prazo",
      header: "Prazo",
      render: (row) => (row.prazo_dias != null ? String(row.prazo_dias) : "—"),
    },
  ];

  function buildPdfOverrides(): ProposalDocumentPdfExportOverrides | undefined {
    if (!data) return undefined;
    const overrides: ProposalDocumentPdfExportOverrides = {};
    const obs = pdfObservacoes.trim();
    if (obs && obs !== (data.observacoes || "").trim()) {
      overrides.observacoes = obs;
    }
    const contato: NonNullable<ProposalDocumentPdfExportOverrides["contato"]> = {};
    if (pdfContatoNome.trim() && pdfContatoNome.trim() !== (data.contato?.nome || "").trim()) {
      contato.nome = pdfContatoNome.trim();
    }
    if (pdfContatoEmail.trim() && pdfContatoEmail.trim() !== (data.contato?.email || "").trim()) {
      contato.email = pdfContatoEmail.trim();
    }
    if (Object.keys(contato).length) overrides.contato = contato;
    return Object.keys(overrides).length ? overrides : undefined;
  }

  async function handleExportPdf() {
    try {
      setPdfLoading(true);
      setPdfError(null);
      await openProposalDocumentPdf(propostaId, buildPdfOverrides());
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : "Não foi possível gerar o PDF.");
    } finally {
      setPdfLoading(false);
    }
  }

  const cabecalho = data?.cabecalho;
  const backHref = buildPluginPath("proposals", basePath);

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: "Propostas",
          href: backHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(backHref);
          },
        }}
        current={cabecalho?.numero_ov || `Proposta ${propostaId}`}
      />
      <CommercialPageHero
        aria-label={cabecalho?.numero_ov || PROPOSALS_CONTENT.detail.title}
        title={cabecalho?.numero_ov || PROPOSALS_CONTENT.detail.title}
        description={
          data
            ? `${displayValue(data.cliente.nome)} · ${displayValue(data.cabecalho.proposta_interna)}`
            : `Proposta ${propostaId}`
        }
        actions={
          <div className="cm-nav-row">
            {canExportProposals ? (
              <CommercialActionButton
                variant="primary"
                onClick={() => void handleExportPdf()}
                disabled={loading || !data || pdfLoading}
              >
                <FileDown size={16} aria-hidden="true" />
                {pdfLoading ? "Gerando…" : PROPOSALS_CONTENT.detail.exportPdf}
              </CommercialActionButton>
            ) : null}
            <CommercialActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
              <RefreshCw size={16} aria-hidden="true" /> Atualizar
            </CommercialActionButton>
          </div>
        }
      />

      {pdfError ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={pdfError} role="alert" />
      ) : null}
      {loading ? <CommercialLoadingCard title="Carregando proposta…" variant="panel" /> : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}

      {!loading && data ? (
        <>
          <SectionCard
            title="Cabeçalho"
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <CommercialDetailFieldGrid
              fields={[
                { label: "Nº OV", value: displayValue(data.cabecalho.numero_ov) },
                { label: "Proposta interna", value: displayValue(data.cabecalho.proposta_interna) },
                { label: "Cliente", value: displayValue(data.cliente.nome) },
                { label: "Data", value: displayValue(data.cabecalho.data) },
                { label: "Versão", value: displayValue(data.cabecalho.versao) },
                { label: "Status", value: displayValue(data.cabecalho.status) },
                {
                  label: OPERATIONAL_UNIT_COLUMN_LABEL,
                  value: displayValue(formatOperationalUnitCode(data.cabecalho.filial, "")),
                },
                { label: "Soma R$/mil", value: displayValue(data.cabecalho.soma_valores_r_mil) },
                { label: "Oportunidade", value: displayValue(data.cabecalho.oportunidade) },
                {
                  label: "Validade (dias)",
                  value: displayValue(data.cabecalho.validade_dias),
                },
              ]}
            />
          </SectionCard>

          <div className="cm-gestao-detail-grid">
            <SectionCard title="Empresa" classNames={cmSectionCardClassNames} labels={cmSectionLabels}>
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Razão social", value: displayValue(data.empresa.nome) },
                  { label: "CNPJ", value: displayValue(data.empresa.cnpj) },
                  {
                    label: "Cidade/UF",
                    value: `${displayValue(data.empresa.cidade)} / ${displayValue(data.empresa.uf)}`,
                  },
                  { label: "Telefone", value: displayValue(data.empresa.telefone) },
                ]}
              />
            </SectionCard>
            <SectionCard title="Cliente" classNames={cmSectionCardClassNames} labels={cmSectionLabels}>
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Nome", value: displayValue(data.cliente.nome) },
                  { label: "Código", value: displayValue(data.cliente.codigo) },
                  { label: "CNPJ", value: displayValue(data.cliente.cnpj) },
                  { label: "Telefone", value: displayValue(data.cliente.telefone) },
                ]}
              />
            </SectionCard>
            <SectionCard title="Contato" classNames={cmSectionCardClassNames} labels={cmSectionLabels}>
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Nome", value: displayValue(data.contato.nome) },
                  { label: "Departamento", value: displayValue(data.contato.departamento) },
                  { label: "E-mail", value: displayValue(data.contato.email) },
                  { label: "Telefone", value: displayValue(data.contato.telefone) },
                ]}
              />
            </SectionCard>
            <SectionCard
              title="Condições"
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
            >
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Descrição", value: displayValue(data.condicoes.descricao) },
                  { label: "ICMS", value: displayValue(data.condicoes.icms) },
                  { label: "PIS/COFINS", value: displayValue(data.condicoes.pis_cofins) },
                  { label: "Frete", value: displayValue(data.condicoes.frete) },
                ]}
              />
            </SectionCard>
          </div>

          <SectionCard
            title={PROPOSALS_CONTENT.detail.items}
            classNames={cmSectionCardClassNames}
            labels={cmSectionLabels}
          >
            <CommercialDataTable
              rows={data.itens}
              columns={itemColumns}
              rowKey={(row) => row.item}
              layout="section"
            />
          </SectionCard>

          {canExportProposals ? (
            <SectionCard
              title="PDF revisável"
              subtitle="Ajuste observações/contato antes de exportar (POST com overrides)."
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
            >
              <div className="cm-form-grid">
                <label className="cm-manage-search__field">
                  Contato (nome)
                  <input
                    type="text"
                    value={pdfContatoNome}
                    onChange={(e) => setPdfContatoNome(e.target.value)}
                  />
                </label>
                <label className="cm-manage-search__field">
                  Contato (e-mail)
                  <input
                    type="email"
                    value={pdfContatoEmail}
                    onChange={(e) => setPdfContatoEmail(e.target.value)}
                  />
                </label>
              </div>
              <CommercialTextAreaField
                label="Observações no PDF"
                value={pdfObservacoes}
                onChange={setPdfObservacoes}
                rows={4}
              />
            </SectionCard>
          ) : data.observacoes ? (
            <SectionCard
              title="Observações"
              classNames={cmSectionCardClassNames}
              labels={cmSectionLabels}
            >
              <p className="cm-prose">{data.observacoes}</p>
            </SectionCard>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
