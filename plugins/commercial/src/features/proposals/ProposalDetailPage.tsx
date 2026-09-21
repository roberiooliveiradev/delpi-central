import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { Check, FileDown, Pencil, RefreshCw, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  getAccountContactsBundle,
  type AccountContactsBundle,
} from "../../api/accountContactsApi";
import { getProposalDocument, openProposalDocumentPdf } from "../../api/commercialProposalsApi";
import { resolvePagePathBack } from "../../app/commercialNavigationReturn";
import {
  CommercialActionButton,
  CommercialDataTable,
  CommercialDetailFieldGrid,
  CommercialEmptyState,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialPagePath,
  CommercialSectionCard,
  CommercialSelectField,
  CommercialStateBanner,
  CommercialTextAreaField,
  CommercialTextField,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { PROPOSALS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import type {
  ProposalDocumentDetail,
  ProposalDocumentItem,
  ProposalDocumentPdfExportOverrides,
} from "../../types/proposalsDocument";
import {
  PROPOSAL_DETAIL_ITEMS_COLUMN_HELP,
  withColumnHelp,
} from "../../utils/customersColumnHelp";
import {
  buildProposalPdfContactOptions,
  defaultProposalPdfContactValue,
  type ProposalPdfContactOption,
} from "../../utils/resolveProposalPdfContact";

function applyPdfContactSelectionToFields(
  option: ProposalPdfContactOption | null | undefined,
  proposalContact: ProposalDocumentDetail["contato"] | null | undefined,
): {
  nome: string;
  departamento: string;
  email: string;
  telefone: string;
} {
  if (!option) {
    return {
      nome: (proposalContact?.nome || "").trim(),
      departamento: (proposalContact?.departamento || "").trim(),
      email: (proposalContact?.email || "").trim(),
      telefone: (proposalContact?.telefone || "").trim(),
    };
  }
  return {
    nome: option.nome,
    email: option.email,
    departamento: option.departamento,
    telefone: option.telefone,
  };
}

function displayValue(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  const text = value.trim();
  return text || "—";
}

type PdfConditionFields = {
  descricao: string;
  icms: string;
  pis_cofins: string;
  frete: string;
};

const PDF_CONDITION_KEYS = ["descricao", "icms", "pis_cofins", "frete"] as const;

function conditionsFromDocument(
  condicoes: ProposalDocumentDetail["condicoes"] | null | undefined,
): PdfConditionFields {
  return {
    descricao: condicoes?.descricao ?? "",
    icms: condicoes?.icms ?? "",
    pis_cofins: condicoes?.pis_cofins ?? "",
    frete: condicoes?.frete ?? "",
  };
}

type ProposalDetailPageProps = {
  basePath: string;
  propostaId: string;
};

export function ProposalDetailPage({ basePath, propostaId }: ProposalDetailPageProps) {
  const { canExportProposals } = usePortfolioScope();
  const [data, setData] = useState<ProposalDocumentDetail | null>(null);
  const [contactsBundle, setContactsBundle] = useState<AccountContactsBundle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [pdfObservacoes, setPdfObservacoes] = useState("");
  const [pdfContactValue, setPdfContactValue] = useState("");
  const [pdfContatoNome, setPdfContatoNome] = useState("");
  const [pdfContatoDepartamento, setPdfContatoDepartamento] = useState("");
  const [pdfContatoEmail, setPdfContatoEmail] = useState("");
  const [pdfContatoTelefone, setPdfContatoTelefone] = useState("");
  const [pdfCondicoes, setPdfCondicoes] = useState<PdfConditionFields>(conditionsFromDocument(null));
  const [editingConditions, setEditingConditions] = useState(false);
  const [conditionDraft, setConditionDraft] = useState<PdfConditionFields>(
    conditionsFromDocument(null),
  );

  function syncPdfContactFields(
    options: readonly ProposalPdfContactOption[],
    selectedValue: string,
    proposalContact: ProposalDocumentDetail["contato"] | null | undefined,
  ) {
    const selected = options.find((option) => option.value === selectedValue);
    const fields = applyPdfContactSelectionToFields(selected, proposalContact);
    setPdfContatoNome(fields.nome);
    setPdfContatoDepartamento(fields.departamento);
    setPdfContatoEmail(fields.email);
    setPdfContatoTelefone(fields.telefone);
  }

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setContactsBundle(null);
    void getProposalDocument(propostaId, controller.signal)
      .then(async (result) => {
        if (controller.signal.aborted) return;
        setData(result);
        setPdfObservacoes(result.observacoes || "");
        setPdfCondicoes(conditionsFromDocument(result.condicoes));
        setEditingConditions(false);

        const code = result.cliente.codigo?.trim();
        const store = result.cliente.loja?.trim();
        let bundle: AccountContactsBundle | null = null;
        if (code && store) {
          try {
            bundle = await getAccountContactsBundle(code, store, controller.signal);
          } catch {
            bundle = { totvs_contact: null, items: [] };
          }
        }
        if (controller.signal.aborted) return;
        setContactsBundle(bundle);
        const options = buildProposalPdfContactOptions({
          proposalContact: result.contato,
          totvsContact: bundle?.totvs_contact,
          savedContacts: bundle?.items ?? [],
        });
        const defaultValue = defaultProposalPdfContactValue(options, result.contato);
        setPdfContactValue(defaultValue);
        syncPdfContactFields(options, defaultValue, result.contato);
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

  const pdfContactOptions = useMemo(
    () =>
      buildProposalPdfContactOptions({
        proposalContact: data?.contato,
        totvsContact: contactsBundle?.totvs_contact,
        savedContacts: contactsBundle?.items ?? [],
      }),
    [data?.contato, contactsBundle],
  );

  function handlePdfContactChange(value: string) {
    setPdfContactValue(value);
    syncPdfContactFields(pdfContactOptions, value, data?.contato);
  }

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
    const nome = pdfContatoNome.trim();
    const departamento = pdfContatoDepartamento.trim();
    const email = pdfContatoEmail.trim();
    const telefone = pdfContatoTelefone.trim();
    if (nome !== (data.contato?.nome || "").trim()) {
      contato.nome = nome;
    }
    if (departamento !== (data.contato?.departamento || "").trim()) {
      contato.departamento = departamento;
    }
    if (email !== (data.contato?.email || "").trim()) {
      contato.email = email;
    }
    if (telefone !== (data.contato?.telefone || "").trim()) {
      contato.telefone = telefone;
    }
    if (Object.keys(contato).length) overrides.contato = contato;
    const source = editingConditions ? conditionDraft : pdfCondicoes;
    const condicoes: NonNullable<ProposalDocumentPdfExportOverrides["condicoes"]> = {};
    for (const key of PDF_CONDITION_KEYS) {
      const next = source[key].trim();
      if (next !== (data.condicoes?.[key] || "").trim()) {
        condicoes[key] = next;
      }
    }
    if (Object.keys(condicoes).length) overrides.condicoes = condicoes;
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
  const listHref = buildPluginPath("proposals", basePath);
  const search =
    typeof window !== "undefined" ? window.location.search : "";
  const back = resolvePagePathBack(
    search,
    { href: listHref, label: "Propostas" },
    basePath,
  );

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: back.label,
          href: back.href,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginPath(back.href);
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

      {pdfError ? <CommercialStateBanner variant="error">{pdfError}</CommercialStateBanner> : null}
      {loading ? <CommercialLoadingCard title="Carregando proposta…" variant="panel" /> : null}
      {error ? <CommercialEmptyState message={error} role="alert" /> : null}

      {!loading && data ? (
        <>
          <CommercialSectionCard title="Cabeçalho">
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
          </CommercialSectionCard>

          <div className="cm-gestao-detail-grid">
            <CommercialSectionCard title="Empresa">
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
            </CommercialSectionCard>
            <CommercialSectionCard title="Cliente">
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Nome", value: displayValue(data.cliente.nome) },
                  { label: "Código", value: displayValue(data.cliente.codigo) },
                  { label: "CNPJ", value: displayValue(data.cliente.cnpj) },
                  { label: "Telefone", value: displayValue(data.cliente.telefone) },
                ]}
              />
            </CommercialSectionCard>
            <CommercialSectionCard title="Contato">
              <CommercialDetailFieldGrid
                fields={[
                  { label: "Nome", value: displayValue(data.contato.nome) },
                  { label: "Departamento", value: displayValue(data.contato.departamento) },
                  { label: "E-mail", value: displayValue(data.contato.email) },
                  { label: "Telefone", value: displayValue(data.contato.telefone) },
                ]}
              />
            </CommercialSectionCard>
            <CommercialSectionCard
              title="Condições"
              hint={canExportProposals ? CM_HELP.proposals.editConditions : undefined}
              actions={
                canExportProposals && !editingConditions ? (
                  <CommercialActionButton
                    variant="ghost"
                    aria-label={PROPOSALS_CONTENT.detail.editConditions}
                    onClick={() => {
                      setConditionDraft(pdfCondicoes);
                      setEditingConditions(true);
                    }}
                  >
                    <Pencil size={16} aria-hidden="true" />
                  </CommercialActionButton>
                ) : null
              }
            >
              {editingConditions ? (
                <div className="cm-form-grid">
                  <p className="cm-muted">{PROPOSALS_CONTENT.detail.conditionsPdfHint}</p>
                  <CommercialTextField
                    id="proposal-pdf-condicao-descricao"
                    label="Descrição"
                    hint={CM_HELP.proposals.editConditions}
                    value={conditionDraft.descricao}
                    onChange={(value) =>
                      setConditionDraft((current) => ({ ...current, descricao: value }))
                    }
                  />
                  <CommercialTextField
                    id="proposal-pdf-condicao-icms"
                    label="ICMS"
                    hint={CM_HELP.proposals.editConditions}
                    value={conditionDraft.icms}
                    onChange={(value) =>
                      setConditionDraft((current) => ({ ...current, icms: value }))
                    }
                  />
                  <CommercialTextField
                    id="proposal-pdf-condicao-pis"
                    label="PIS/COFINS"
                    hint={CM_HELP.proposals.editConditions}
                    value={conditionDraft.pis_cofins}
                    onChange={(value) =>
                      setConditionDraft((current) => ({ ...current, pis_cofins: value }))
                    }
                  />
                  <CommercialTextField
                    id="proposal-pdf-condicao-frete"
                    label="Frete"
                    hint={CM_HELP.proposals.editConditions}
                    value={conditionDraft.frete}
                    onChange={(value) =>
                      setConditionDraft((current) => ({ ...current, frete: value }))
                    }
                  />
                  <div className="cm-nav-row">
                    <CommercialActionButton
                      variant="primary"
                      onClick={() => {
                        setPdfCondicoes(conditionDraft);
                        setEditingConditions(false);
                      }}
                    >
                      <Check size={16} aria-hidden="true" />
                      {PROPOSALS_CONTENT.detail.applyConditions}
                    </CommercialActionButton>
                    <CommercialActionButton
                      variant="ghost"
                      onClick={() => setEditingConditions(false)}
                    >
                      <X size={16} aria-hidden="true" />
                      {PROPOSALS_CONTENT.detail.cancelConditions}
                    </CommercialActionButton>
                  </div>
                </div>
              ) : (
                <CommercialDetailFieldGrid
                  fields={[
                    { label: "Descrição", value: displayValue(pdfCondicoes.descricao) },
                    { label: "ICMS", value: displayValue(pdfCondicoes.icms) },
                    { label: "PIS/COFINS", value: displayValue(pdfCondicoes.pis_cofins) },
                    { label: "Frete", value: displayValue(pdfCondicoes.frete) },
                  ]}
                />
              )}
            </CommercialSectionCard>
          </div>

          <CommercialSectionCard title={PROPOSALS_CONTENT.detail.items}>
            <CommercialDataTable
              rows={data.itens}
              columns={withColumnHelp(itemColumns, PROPOSAL_DETAIL_ITEMS_COLUMN_HELP)}
              rowKey={(row) => row.item}
              layout="section"
            />
          </CommercialSectionCard>

          {canExportProposals ? (
            <CommercialSectionCard
              title={PROPOSALS_CONTENT.detail.pdfSection}
              hint={PROPOSALS_CONTENT.detail.pdfSectionHint}
            >
              {pdfContactOptions.length > 0 ? (
                <CommercialSelectField
                  id="proposal-pdf-contact"
                  label={PROPOSALS_CONTENT.detail.pdfContactLabel}
                  hint={CM_HELP.proposals.pdfContact}
                  value={pdfContactValue}
                  onChange={handlePdfContactChange}
                  options={pdfContactOptions.map((option) => ({
                    value: option.value,
                    label: option.label,
                  }))}
                />
              ) : (
                <CommercialEmptyState message={PROPOSALS_CONTENT.detail.pdfContactEmpty} />
              )}
              <p className="cm-muted">{PROPOSALS_CONTENT.detail.pdfContactFieldsHint}</p>
              <div className="cm-form-grid">
                <CommercialTextField
                  id="proposal-pdf-contact-nome"
                  label={PROPOSALS_CONTENT.detail.pdfContactNomeLabel}
                  hint={CM_HELP.proposals.pdfContactNome}
                  value={pdfContatoNome}
                  onChange={setPdfContatoNome}
                />
                <CommercialTextField
                  id="proposal-pdf-contact-departamento"
                  label={PROPOSALS_CONTENT.detail.pdfContactDepartamentoLabel}
                  hint={CM_HELP.proposals.pdfContactDepartamento}
                  value={pdfContatoDepartamento}
                  onChange={setPdfContatoDepartamento}
                />
                <CommercialTextField
                  id="proposal-pdf-contact-email"
                  label={PROPOSALS_CONTENT.detail.pdfContactEmailLabel}
                  hint={CM_HELP.proposals.pdfContactEmail}
                  value={pdfContatoEmail}
                  onChange={setPdfContatoEmail}
                />
                <CommercialTextField
                  id="proposal-pdf-contact-telefone"
                  label={PROPOSALS_CONTENT.detail.pdfContactTelefoneLabel}
                  hint={CM_HELP.proposals.pdfContactTelefone}
                  value={pdfContatoTelefone}
                  onChange={setPdfContatoTelefone}
                />
              </div>
              <CommercialTextAreaField
                label={PROPOSALS_CONTENT.detail.pdfObservacoesLabel}
                hint={CM_HELP.proposals.pdfObservacoes}
                value={pdfObservacoes}
                onChange={setPdfObservacoes}
                rows={4}
              />
            </CommercialSectionCard>
          ) : data.observacoes ? (
            <CommercialSectionCard title="Observações">
              <p className="cm-prose">{data.observacoes}</p>
            </CommercialSectionCard>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
