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
        <h2 className="si-settings-hero__title">
          Administração dos Indicadores Estratégicos
        </h2>
        <p className="si-settings-hero__description">
          Gerencie departamentos, indicadores estruturais, metas anuais,
          parâmetros globais e trilha de auditoria em um único espaço
          administrativo.
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