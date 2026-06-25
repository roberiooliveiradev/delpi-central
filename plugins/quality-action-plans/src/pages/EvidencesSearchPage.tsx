import { useCallback, useEffect, useState } from "react";

import { searchEvidences } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { EvidenceSearchTable } from "../components/EvidenceSearchTable";
import { PageHeader } from "../components/PageHeader";
import { StateAlert } from "../components/StateAlert";
import { FilterBar } from "../components/ui/FilterBar";
import { MultiSelectField } from "../components/ui/MultiSelectField";
import { TextField } from "../components/ui/TextField";
import { PAC_BRANCH_OPTIONS } from "../constants/actionPlans";
import type { EvidenceSearchHit } from "../types/evidenceSearch";

type Props = {
  onNavigate: (path: string) => void;
};

export function EvidencesSearchPage({ onNavigate }: Props) {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [branches, setBranches] = useState<string[]>([]);
  const [items, setItems] = useState<EvidenceSearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (submittedQuery.trim().length < 2) {
      setItems([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await searchEvidences({
        q: submittedQuery.trim(),
        branch_code: branches.length === 1 ? branches[0] : undefined,
        page_size: 200,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao buscar evidências.");
    } finally {
      setLoading(false);
    }
  }, [branches, submittedQuery]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    setSubmittedQuery(query);
  }

  return (
    <>
      <PageHeader
        title="Busca de evidências"
        subtitle="Pesquisa por nome de arquivo, descrição ou trecho de texto em todos os planos."
      />
      <AppNav active="evidences" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <form onSubmit={handleSearch}>
        <FilterBar compact>
          <TextField
            id="pac-evidence-search-q"
            label="Termo"
            value={query}
            onChange={setQuery}
            placeholder="nome do arquivo, descrição…"
          />
          <MultiSelectField
            id="pac-evidence-search-branch"
            label="Filial"
            options={PAC_BRANCH_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
            selectedValues={branches}
            onChange={setBranches}
            emptyLabel="Todas"
            searchable={false}
          />
          <div className="pac-filter-actions">
            <button type="submit" className="pac-primary-btn" disabled={query.trim().length < 2}>
              Buscar
            </button>
          </div>
        </FilterBar>
      </form>

      <section className="pac-card">
        {submittedQuery.trim().length < 2 ? (
          <p className="pac-muted">Digite ao menos 2 caracteres e clique em Buscar.</p>
        ) : (
          <EvidenceSearchTable
            items={items}
            loading={loading}
            emptyMessage={`Nenhuma evidência para "${submittedQuery}".`}
            onNavigate={onNavigate}
          />
        )}
      </section>
    </>
  );
}
