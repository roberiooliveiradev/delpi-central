type PageHeaderProps = {
  title: string;
  subtitle: string;
  refreshing?: boolean;
  onRefresh?: () => void;
};

export function PageHeader({ title, subtitle, refreshing, onRefresh }: PageHeaderProps) {
  return (
    <header className="pa-page-header">
      <div>
        <h1 className="pa-page-header__title">{title}</h1>
        <p className="pa-page-header__subtitle">{subtitle}</p>
      </div>
      {onRefresh ? (
        <button
          type="button"
          className="pa-btn pa-btn--secondary"
          onClick={onRefresh}
          disabled={refreshing}
        >
          {refreshing ? "Atualizando…" : "Atualizar"}
        </button>
      ) : null}
    </header>
  );
}
