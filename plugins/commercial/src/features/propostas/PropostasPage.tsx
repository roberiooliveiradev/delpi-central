import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { RefreshCw } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { listPropostasComerciais } from "../../api/propostasComerciaisApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTextField,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { navigatePropostaDetail } from "../../app/pluginNavigation";
import { PROPOSTAS_CONTENT } from "../../content/gestaoContent";
import type { PropostaComercialListData, PropostaComercialListItem } from "../../types/propostasComerciais";

function filterPropostas(
  items: PropostaComercialListItem[],
  search: string,
): PropostaComercialListItem[] {
  const query = search.trim().toLowerCase();
  if (!query) return items;
  const withoutOv = query.replace(/^ov\s*/i, "").trim();
  return items.filter((item) => {
    const haystack = [item.proposta_interna, item.numero_ov, item.oportunidade, item.cliente]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query) || (withoutOv !== query && haystack.includes(withoutOv));
  });
}

type PropostasPageProps = {
  basePath: string;
};

export function PropostasPage({ basePath }: PropostasPageProps) {
  const [data, setData] = useState<PropostaComercialListData | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void listPropostasComerciais(100, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setData(result);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Não foi possível carregar as propostas.");
        setData(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reloadKey]);

  const filtered = useMemo(
    () => filterPropostas(data?.items ?? [], search),
    [data?.items, search],
  );

  const columns: DataTableColumn<PropostaComercialListItem>[] = [
    {
      key: "ov",
      header: "Nº OV",
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={() => navigatePropostaDetail(row.proposta_interna, { basePath })}
        >
          {row.numero_ov || row.proposta_interna}
        </button>
      ),
    },
    { key: "interna", header: "Proposta", render: (row) => row.proposta_interna },
    { key: "cliente", header: "Cliente", render: (row) => row.cliente || "—" },
    { key: "oportunidade", header: "Oportunidade", render: (row) => row.oportunidade || "—" },
    { key: "versao", header: "Versão", render: (row) => row.versao || "—" },
    { key: "data", header: "Data", render: (row) => row.data || "—" },
    {
      key: "itens",
      header: "Itens",
      render: (row) => row.quantidade_itens.toLocaleString("pt-BR"),
    },
  ];

  return (
    <section className="cm-page-stack">
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={PROPOSTAS_CONTENT.list.title}
          hint={PROPOSTAS_CONTENT.list.subtitle}
        />
        <ActionButton variant="ghost" onClick={() => setReloadKey((v) => v + 1)}>
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <CommercialTextField
        label="Busca"
        hint={PROPOSTAS_CONTENT.list.search}
        value={search}
        onChange={setSearch}
        placeholder="OV, proposta, cliente…"
      />

      <SectionCard
        title={`Propostas (${filtered.length.toLocaleString("pt-BR")})`}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? <CommercialLoadingCard title="Carregando propostas…" variant="panel" /> : null}
        {error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
        ) : null}
        {!loading && !error && filtered.length === 0 ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultTitle={PROPOSTAS_CONTENT.list.empty}
            defaultMessage={
              search ? PROPOSTAS_CONTENT.list.emptySearch : PROPOSTAS_CONTENT.list.empty
            }
          />
        ) : null}
        {!loading && !error && filtered.length > 0 ? (
          <DataTable
            rows={filtered}
            columns={columns}
            rowKey={(row) => row.proposta_interna}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        ) : null}
      </SectionCard>
    </section>
  );
}
