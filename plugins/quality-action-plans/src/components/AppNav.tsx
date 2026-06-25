import {
  dashboardPath,
  listPath,
  overduePath,
  recurrencePath,
  solutionsPath,
  evidencesSearchPath,
  myQueuePath,
  type AppView,
} from "../constants/actionPlans";

type Props = {
  active: AppView;
  onNavigate: (path: string) => void;
};

const TABS: Array<{ view: AppView; label: string; path: string }> = [
  { view: "dashboard", label: "Resumo", path: dashboardPath() },
  { view: "list", label: "Planos", path: listPath() },
  { view: "my-queue", label: "Minha fila", path: myQueuePath() },
  { view: "overdue", label: "Atrasados", path: overduePath() },
  { view: "recurrence", label: "Recorrência", path: recurrencePath() },
  { view: "solutions", label: "Soluções", path: solutionsPath() },
  { view: "evidences", label: "Evidências", path: evidencesSearchPath() },
];

export function AppNav({ active, onNavigate }: Props) {
  return (
    <nav className="pac-nav" aria-label="Navegação PAC Qualidade">
      {TABS.map((tab) => (
        <button
          key={tab.view}
          type="button"
          className={tab.view === active ? "pac-nav__item pac-nav__item--active" : "pac-nav__item"}
          onClick={() => onNavigate(tab.path)}
        >
          {tab.label}
        </button>
      ))}
    </nav>
  );
}
