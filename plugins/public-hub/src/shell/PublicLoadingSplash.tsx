import { ScreenLoading } from "@delpi/plugin-ui/index";

type PublicLoadingSplashProps = {
  /** Chrome do palco — kiosk usa visual cinematográfico em tela cheia. */
  chrome?: "default" | "kiosk" | "fullpage";
  label?: string;
};

/**
 * Splash de carregamento do hub público — delega ao kit `ScreenLoading`.
 */
export function PublicLoadingSplash({
  chrome = "default",
  label = "Carregando",
}: PublicLoadingSplashProps) {
  const isKiosk = chrome === "kiosk";
  return (
    <ScreenLoading
      label={label}
      variant={isKiosk ? "fullscreen" : "embedded"}
      tone={isKiosk ? "dark" : "brand"}
    />
  );
}
