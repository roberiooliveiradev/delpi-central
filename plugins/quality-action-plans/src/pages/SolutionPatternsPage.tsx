import { useCallback, useEffect, useState } from "react";

import { fetchSolutionPatterns } from "../api/actionPlansApi";
import { AppNav } from "../components/AppNav";
import { PageHeader } from "../components/PageHeader";
import { SolutionPatternsTable } from "../components/SolutionPatternsTable";
import { StateAlert } from "../components/StateAlert";
import { FilterBar } from "../components/ui/FilterBar";
import { TextField } from "../components/ui/TextField";
import type { SolutionPattern } from "../types/solutionPattern";

type Props = {
  onNavigate: (path: string) => void;
};

export function SolutionPatternsPage({ onNavigate }: Props) {
  const [items, setItems] = useState<SolutionPattern[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [failureMode, setFailureMode] = useState("");
  const [problemCategory, setProblemCategory] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSolutionPatterns({
        failure_mode: failureMode.trim() || undefined,
        problem_category: problemCategory.trim() || undefined,
        q: search.trim() || undefined,
        page_size: 200,
      });
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao listar padrões de solução.");
    } finally {
      setLoading(false);
    }
  }, [failureMode, problemCategory, search]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <>
      <PageHeader
        title="Soluções testadas"
        subtitle="Padrões curados a partir de planos com eficácia comprovada."
      />
      <AppNav active="solutions" onNavigate={onNavigate} />
      {error ? <StateAlert variant="error">{error}</StateAlert> : null}

      <FilterBar compact>
        <TextField
          id="pac-solutions-search"
          label="Busca"
          value={search}
          onChange={setSearch}
          placeholder="Título, categoria ou modo de falha"
        />
        <TextField
          id="pac-solutions-category"
          label="Categoria"
          value={problemCategory}
          onChange={setProblemCategory}
        />
        <TextField
          id="pac-solutions-failure"
          label="Modo de falha"
          value={failureMode}
          onChange={setFailureMode}
        />
      </FilterBar>

      <section className="pac-card">
        <SolutionPatternsTable
          items={items}
          loading={loading}
          emptyMessage="Nenhum padrão encontrado. Promova um plano eficaz no detalhe do plano."
        />
      </section>
    </>
  );
}
