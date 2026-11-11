import { useState } from "react";

import { ItpActionButton, ItpPageHero, ItpSelectField } from "../../app/itPortalUi";
import { useDebouncedValue } from "../../app/useDebouncedValue";
import { ACTION_PRIORITY_OPTIONS, ACTION_STATUS_OPTIONS } from "../../content/labels";
import { ActionPlanTable, useListState } from "./ActionPlanTable";

const SCOPE_OPTIONS = [
  { value: "open", label: "Abertos (pendentes e em andamento)" },
  { value: "overdue", label: "Atrasados" },
  { value: "all", label: "Todos" },
  ...ACTION_STATUS_OPTIONS,
];

export function ActionPlansPage() {
  const list = useListState("due_date");
  const [scope, setScope] = useState("open");
  const [priority, setPriority] = useState("");
  const [search, setSearch] = useState("");
  const q = useDebouncedValue(search);

  const statuses =
    scope === "open" || scope === "overdue" ? ["pending", "in_progress"] : scope === "all" ? [] : [scope];

  const query = {
    status: statuses,
    overdue_only: scope === "overdue",
    priority: priority || undefined,
    q: q || undefined,
    sort: list.sort,
    direction: list.direction,
    page: list.page,
    page_size: list.pageSize,
  };

  const filtersActive = scope !== "open" || Boolean(priority) || Boolean(search);

  return (
    <>
      <ItpPageHero
        variant="immersive"
        aria-label="Planos de ação"
        eyebrow="Infraestrutura"
        title="Planos de ação"
        description="Acompanhe as ações planejadas para os servidores. Para criar um plano, abra o servidor correspondente."
      />
      <ActionPlanTable
        title="Planos de ação"
        query={query}
        showServer
        emptyMessage={
          filtersActive
            ? "Nenhum plano de ação corresponde aos filtros."
            : "Nenhum plano de ação aberto. Crie planos a partir da página de cada servidor."
        }
        search={search}
        onSearchChange={(value) => {
          setSearch(value);
          list.resetPage();
        }}
        onPageChange={list.setPage}
        onPageSizeChange={list.onPageSizeChange}
        onSortChange={list.onSortChange}
        toolbarFilters={
          <div className="itp-filters">
            <ItpSelectField
              label="Situação"
              options={SCOPE_OPTIONS}
              value={scope}
              onChange={(value) => {
                setScope(value || "open");
                list.resetPage();
              }}
            />
            <ItpSelectField
              label="Prioridade"
              options={ACTION_PRIORITY_OPTIONS}
              value={priority}
              allowEmpty
              onChange={(value) => {
                setPriority(value);
                list.resetPage();
              }}
            />
            {filtersActive ? (
              <ItpActionButton
                variant="link"
                onClick={() => {
                  setScope("open");
                  setPriority("");
                  setSearch("");
                  list.resetPage();
                }}
              >
                Limpar filtros
              </ItpActionButton>
            ) : null}
          </div>
        }
      />
    </>
  );
}
