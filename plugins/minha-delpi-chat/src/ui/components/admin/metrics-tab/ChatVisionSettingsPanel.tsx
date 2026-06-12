import {
  getAdminChatVisionSettings,
  saveAdminChatVisionSettings,
} from "../../../../data/api/adminApi";
import type { AdminChatVisionSettings } from "../../../../data/api/adminTypes";
import {
  BundleNumberSettingCard,
  BundleToggleSettingCard,
  ChatAdminBundleSettingsPanel,
} from "./ChatAdminBundleSettingsPanel";
import {
  CHAT_VISION_NUMBER_META,
  CHAT_VISION_SECTIONS,
  CHAT_VISION_TOGGLE_META,
} from "./chatVisionSettingMeta";

type Props = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatVisionSettingsPanel({ getAccessToken }: Props) {
  return (
    <ChatAdminBundleSettingsPanel<AdminChatVisionSettings>
      title="Visão e anexos"
      intro="OCR, desenhos técnicos e limites de extração. Modelo VLM, DPI e URLs permanecem só no Docker (.env)."
      sections={CHAT_VISION_SECTIONS}
      getAccessToken={getAccessToken}
      loadSettings={getAdminChatVisionSettings}
      saveSettings={saveAdminChatVisionSettings}
      renderSection={(settings, updateField, sectionId) => {
        if (sectionId === "limits") {
          return (
            <>
              <BundleNumberSettingCard
                meta={CHAT_VISION_NUMBER_META.documentVisionMaxPages}
                value={Number(settings.documentVisionMaxPages)}
                onChange={(value) => updateField("documentVisionMaxPages", value)}
              />
              <BundleNumberSettingCard
                meta={CHAT_VISION_NUMBER_META.documentVisionMaxChars}
                value={Number(settings.documentVisionMaxChars)}
                onChange={(value) => updateField("documentVisionMaxChars", value)}
              />
            </>
          );
        }

        return (
          <>
            <BundleToggleSettingCard
              meta={CHAT_VISION_TOGGLE_META.documentVisionEnabled}
              checked={Boolean(settings.documentVisionEnabled)}
              onChange={(checked) => updateField("documentVisionEnabled", checked)}
            />
            <BundleToggleSettingCard
              meta={CHAT_VISION_TOGGLE_META.documentVisionAutoWithDrawing}
              checked={Boolean(settings.documentVisionAutoWithDrawing)}
              onChange={(checked) =>
                updateField("documentVisionAutoWithDrawing", checked)
              }
            />
            <BundleToggleSettingCard
              meta={CHAT_VISION_TOGGLE_META.documentVisionAutoVlmFallback}
              checked={Boolean(settings.documentVisionAutoVlmFallback)}
              onChange={(checked) =>
                updateField("documentVisionAutoVlmFallback", checked)
              }
            />
            <BundleToggleSettingCard
              meta={CHAT_VISION_TOGGLE_META.attachmentImageOcrEnabled}
              checked={Boolean(settings.attachmentImageOcrEnabled)}
              onChange={(checked) => updateField("attachmentImageOcrEnabled", checked)}
            />
            <BundleToggleSettingCard
              meta={CHAT_VISION_TOGGLE_META.documentVisionStampCropEnabled}
              checked={Boolean(settings.documentVisionStampCropEnabled)}
              onChange={(checked) =>
                updateField("documentVisionStampCropEnabled", checked)
              }
            />
            <BundleToggleSettingCard
              meta={CHAT_VISION_TOGGLE_META.documentVisionImageDescribeEnabled}
              checked={Boolean(settings.documentVisionImageDescribeEnabled)}
              onChange={(checked) =>
                updateField("documentVisionImageDescribeEnabled", checked)
              }
            />
          </>
        );
      }}
    />
  );
}
