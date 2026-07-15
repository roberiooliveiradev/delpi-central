type PageHeaderProps = {
  title: string;
  subtitle: string;
};

export function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <header className="sm-page-header">
      <div>
        <h1 className="sm-page-header__title">{title}</h1>
        <p className="sm-page-header__subtitle">{subtitle}</p>
      </div>
    </header>
  );
}
