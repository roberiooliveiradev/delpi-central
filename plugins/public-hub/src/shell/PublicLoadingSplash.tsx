import { ScreenLoading } from "@delpi/plugin-ui/screen-loading";
import { usePublicThemeMode } from "./ThemeToggle";

type PublicLoadingSplashProps = {
  /** Chrome do palco — kiosk usa tela cheia escura. */
  chrome?: "default" | "kiosk" | "fullpage";
  label?: string;
};

/**
 * Splash de carregamento do hub público — delega ao kit `ScreenLoading`
 * (badge branco + logo Minha DELPI). Kiosk sempre escuro; demais seguem o tema.
 */
export function PublicLoadingSplash({
  chrome = "default",
  label = "Carregando",
}: PublicLoadingSplashProps) {
  const theme = usePublicThemeMode();
  const isKiosk = chrome === "kiosk";
  const tone = isKiosk ? "dark" : theme === "dark" ? "dark" : "light";

  return (
    <ScreenLoading
      label={label}
      variant={isKiosk ? "fullscreen" : "embedded"}
      tone={tone}
      logoSrc="/p/logoMinhaDelpi.svg"
    />
  );
}
