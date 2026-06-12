import {
  getAdminChatResponseModeSettings,
  saveAdminChatResponseModeSettings,
} from "../../../../data/api/adminApi";
import type { AdminChatResponseModeSettings } from "../../../../data/api/adminTypes";
import {
  BundleToggleSettingCard,
  ChatAdminBundleSettingsPanel,
} from "./ChatAdminBundleSettingsPanel";
import {
  CHAT_RESPONSE_MODE_SECTIONS,
  CHAT_RESPONSE_MODE_TOGGLE_META,
} from "./chatResponseModeSettingMeta";

type Props = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatResponseModeSettingsPanel({ getAccessToken }: Props) {
  return (
    <ChatAdminBundleSettingsPanel<AdminChatResponseModeSettings>
      title="Modos de resposta"
      intro="Define se o seletor Texto / Painel / Automático aparece no chat. Valores salvos aqui prevalecem sobre o .env do Docker."
      sections={CHAT_RESPONSE_MODE_SECTIONS}
      getAccessToken={getAccessToken}
      loadSettings={getAdminChatResponseModeSettings}
      saveSettings={saveAdminChatResponseModeSettings}
      renderSection={(settings, updateField, _sectionId) => (
        <BundleToggleSettingCard
          meta={CHAT_RESPONSE_MODE_TOGGLE_META.responseModesEnabled}
          checked={Boolean(settings.responseModesEnabled)}
          onChange={(checked) => updateField("responseModesEnabled", checked)}
        />
      )}
    />
  );
}
