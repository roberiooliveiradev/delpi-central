import {
  CfLoadingCard,
  CfPageHero,
  CfPagePath,
  CfTitleWithHelp,
} from "../../app/controllershipFinanceUi";

type PathItem = {
  id: string;
  label: string;
  href?: string;
  onNavigate?: () => void;
};

/**
 * Estado inicial de páginas profundas da auditoria (G7 / §16):
 * PagePath + hero + esqueleto — nunca só «Carregando…».
 */
export function EntryAuditLoadingState({
  pathItems,
  current,
  title,
  hint,
  eyebrow = "Notas fiscais",
  description = "Carregando indicadores e tabelas…",
}: {
  pathItems: PathItem[];
  current: string;
  title: string;
  hint: string;
  eyebrow?: string;
  description?: string;
}) {
  return (
    <section className="cf-page-stack" aria-busy="true" aria-live="polite">
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        items={pathItems.map((item) => ({
          id: item.id,
          label: item.label,
          href: item.href,
          onNavigate: item.onNavigate
            ? (event: { preventDefault: () => void }) => {
                event.preventDefault();
                item.onNavigate?.();
              }
            : undefined,
        }))}
        current={current}
      />
      <CfPageHero
        eyebrow={eyebrow}
        title={<CfTitleWithHelp title={title} hint={hint} />}
        description={description}
      />
      <div className="cf-kpi-grid" aria-hidden="true">
        {Array.from({ length: 6 }).map((_, index) => (
          <CfLoadingCard key={index} title="…" />
        ))}
      </div>
      <CfLoadingCard title="Carregando conteúdo…" />
    </section>
  );
}
