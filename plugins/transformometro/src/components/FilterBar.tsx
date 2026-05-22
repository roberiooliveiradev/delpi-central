import type { OptionsData } from "../data/api/transformometroApi";
import { PageHeader } from "./PageHeader";

type FilterBarProps = {
  title?: string;
  subtitle?: string;
  currentPath?: string;
  onNavigate: (path: string) => void;
  dateStart: string;
  dateEnd: string;
  branch: string;
  setorId: string;
  options: OptionsData | null;
  onDateStartChange: (value: string) => void;
  onDateEndChange: (value: string) => void;
  onBranchChange: (value: string) => void;
  onSetorChange: (value: string) => void;
  onRefresh: () => void;
  refreshing?: boolean;
  headerActions?: React.ReactNode;
};

export function FilterBar({
  title = "Dashboard Transformômetro",
  subtitle = "Economia bruta e líquida por competência — cadastro no PostgreSQL",
  currentPath,
  onNavigate,
  dateStart,
  dateEnd,
  branch,
  setorId,
  options,
  onDateStartChange,
  onDateEndChange,
  onBranchChange,
  onSetorChange,
  onRefresh,
  refreshing = false,
  headerActions,
}: FilterBarProps) {
  return (
    <>
      <PageHeader
        title={title}
        subtitle={subtitle}
        currentPath={currentPath}
        onNavigate={onNavigate}
        onRefresh={onRefresh}
        refreshing={refreshing}
        actions={headerActions}
      />
      <section className="ds-filters-row ds-no-print">
        <div className="ds-filter-box">
          <label htmlFor="tm-date-start">Data inicial</label>
          <input
            id="tm-date-start"
            type="date"
            value={dateStart}
            onChange={(e) => onDateStartChange(e.target.value)}
          />
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-date-end">Data final</label>
          <input
            id="tm-date-end"
            type="date"
            value={dateEnd}
            onChange={(e) => onDateEndChange(e.target.value)}
          />
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-branch">Filial</label>
          <select id="tm-branch" value={branch} onChange={(e) => onBranchChange(e.target.value)}>
            <option value="">Consolidado</option>
            {(options?.filiais ?? []).map((f) => (
              <option key={f.id} value={f.id}>
                {f.id} — {f.label}
              </option>
            ))}
          </select>
        </div>
        <div className="ds-filter-box">
          <label htmlFor="tm-setor">Setor</label>
          <select id="tm-setor" value={setorId} onChange={(e) => onSetorChange(e.target.value)}>
            <option value="">Todos</option>
            {(options?.setores ?? []).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </section>
    </>
  );
}
