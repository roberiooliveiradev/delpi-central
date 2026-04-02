type SettingsHeroProps = {
  routePath: string;
  permissionCode: string;
};

export function SettingsHero({
  routePath,
  permissionCode,
}: SettingsHeroProps) {
  return (
    <section className="si-settings-hero">
      <div className="si-settings-hero__content">
        <p className="si-settings-hero__eyebrow">Governança do módulo</p>
        <h2 className="si-settings-hero__title">Configurações do Strategic Indicators</h2>
        <p className="si-settings-hero__description">
          Esta área organiza os pesos oficiais do IGD, as metas resumidas por
          área e os parâmetros administrativos do painel.
        </p>
      </div>

      <div className="si-settings-hero__meta">
        <div className="si-settings-hero__meta-item">
          <span>Rota</span>
          <strong>{routePath}</strong>
        </div>

        <div className="si-settings-hero__meta-item">
          <span>Permissão</span>
          <strong>{permissionCode}</strong>
        </div>
      </div>
    </section>
  );
}