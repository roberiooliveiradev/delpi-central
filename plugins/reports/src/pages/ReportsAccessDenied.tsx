type Props = {
  message?: string;
};

export function ReportsAccessDenied({
  message = "Você não tem permissão para esta área do Delpi Reports.",
}: Props) {
  return (
    <div className="rp-page-content">
      <header className="rp-page-header">
        <div className="rp-page-header__shell">
          <div className="rp-page-header__main">
            <div className="rp-page-header__brand">
              <div className="rp-page-header__titles">
                <p className="rp-page-header__eyebrow">Delpi Reports</p>
                <div className="rp-page-header__title-row">
                  <h1>Acesso restrito</h1>
                </div>
                <p className="rp-page-header__subtitle">{message}</p>
              </div>
            </div>
          </div>
        </div>
      </header>
    </div>
  );
}
