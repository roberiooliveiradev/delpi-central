import { useMemo, useState } from "react";

import { PageHeader } from "../components/PageHeader";
import { PropostasTable } from "../components/PropostasTable";
import { SearchBar } from "../components/SearchBar";
import { StateBox } from "../components/StateBox";
import { usePropostasComerciaisList } from "../hooks/usePropostasComerciaisList";
import { filterPropostasComerciais } from "../utils/format";
import { navigatePropostaDetail } from "../utils/navigation";

export function PropostasComerciaisListPage() {
  const { data, loading, error, reload } = usePropostasComerciaisList(100);
  const [search, setSearch] = useState("");

  const filteredItems = useMemo(() => {
    return filterPropostasComerciais(data?.items ?? [], search);
  }, [data?.items, search]);

  return (
    <>
      <PageHeader
        title="Propostas Comerciais"
        subtitle="Consulta read-only de propostas ativas do Protheus"
        loading={loading}
        onRefresh={reload}
      />

      <SearchBar value={search} onChange={setSearch} resultCount={filteredItems.length} />

      {loading ? (
        <StateBox variant="loading" title="Carregando propostas" message="Buscando propostas recentes no Protheus." />
      ) : null}

      {!loading && error ? (
        <StateBox
          variant="error"
          title="Erro ao carregar"
          message={error}
          action={
            <button type="button" className="pc-btn pc-btn--primary" onClick={reload}>
              Tentar novamente
            </button>
          }
        />
      ) : null}

      {!loading && !error && filteredItems.length === 0 ? (
        <StateBox
          variant="empty"
          title="Nenhuma proposta encontrada"
          message={
            search
              ? "Ajuste a busca ou limpe o filtro para ver a lista completa."
              : "Não há propostas comerciais ativas no momento."
          }
        />
      ) : null}

      {!loading && !error && filteredItems.length > 0 ? (
        <PropostasTable
          items={filteredItems}
          onSelect={(propostaInterna) => navigatePropostaDetail(propostaInterna)}
        />
      ) : null}
    </>
  );
}
