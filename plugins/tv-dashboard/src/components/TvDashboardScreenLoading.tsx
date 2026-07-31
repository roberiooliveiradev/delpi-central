import { ScreenLoading, type ScreenLoadingProps } from "@delpi/plugin-ui/index";

const DEFAULT_LOGO = "/logoMinhaDelpi.svg";

type Props = {
  label?: string;
  /**
   * `fullscreen` — editor / deck (preenche o shell).
   * `embedded` — home / listas dentro do fluxo da página.
   */
  variant?: ScreenLoadingProps["variant"];
  tone?: ScreenLoadingProps["tone"];
  className?: string;
};

/**
 * Splash de tela do TV Dashboard — `ScreenLoading` do plugin-ui
 * (mesmo padrão da prévia e do hub público).
 */
export function TvDashboardScreenLoading({
  label = "Carregando",
  variant = "fullscreen",
  tone = "dark",
  className,
}: Props) {
  return (
    <div
      className={["td-screen-loading", `td-screen-loading--${variant}`, className]
        .filter(Boolean)
        .join(" ")}
    >
      <ScreenLoading
        label={label}
        variant={variant}
        tone={tone}
        logoSrc={DEFAULT_LOGO}
      />
    </div>
  );
}
