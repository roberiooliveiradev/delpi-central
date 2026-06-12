import {
  getAdminChatLearningPipelineSettings,
  saveAdminChatLearningPipelineSettings,
} from "../../../../data/api/adminApi";
import type { AdminChatLearningPipelineSettings } from "../../../../data/api/adminTypes";
import {
  BundleNumberSettingCard,
  BundleToggleSettingCard,
  ChatAdminBundleSettingsPanel,
} from "../metrics-tab/ChatAdminBundleSettingsPanel";
import {
  CHAT_LEARNING_PIPELINE_NUMBER_META,
  CHAT_LEARNING_PIPELINE_SECTIONS,
  CHAT_LEARNING_PIPELINE_TOGGLE_META,
} from "../metrics-tab/chatLearningPipelineSettingMeta";

type Props = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function ChatLearningPipelineSettingsPanel({ getAccessToken }: Props) {
  return (
    <ChatAdminBundleSettingsPanel<AdminChatLearningPipelineSettings>
      title="Pipeline de aprendizagem"
      intro="Captura, vocabulário, glossário, regressão e fine-tuning. Modelos, webhooks e URLs de treino permanecem só no Docker (.env)."
      sections={CHAT_LEARNING_PIPELINE_SECTIONS}
      getAccessToken={getAccessToken}
      loadSettings={getAdminChatLearningPipelineSettings}
      saveSettings={saveAdminChatLearningPipelineSettings}
      renderSection={(settings, updateField, sectionId) => {
        if (sectionId === "typing") {
          return (
            <>
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.typingCorrectionEnabled}
                checked={Boolean(settings.typingCorrectionEnabled)}
                onChange={(checked) => updateField("typingCorrectionEnabled", checked)}
              />
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.typingCorrectionFuzzyEnabled}
                checked={Boolean(settings.typingCorrectionFuzzyEnabled)}
                onChange={(checked) =>
                  updateField("typingCorrectionFuzzyEnabled", checked)
                }
              />
            </>
          );
        }

        if (sectionId === "glossary") {
          return (
            <>
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningGlossaryRetrieval}
                checked={Boolean(settings.learningGlossaryRetrieval)}
                onChange={(checked) => updateField("learningGlossaryRetrieval", checked)}
              />
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningGlossaryCapture}
                checked={Boolean(settings.learningGlossaryCapture)}
                onChange={(checked) => updateField("learningGlossaryCapture", checked)}
              />
              <BundleToggleSettingCard
                meta={
                  CHAT_LEARNING_PIPELINE_TOGGLE_META.learningTermConfirmationEnabled
                }
                checked={Boolean(settings.learningTermConfirmationEnabled)}
                onChange={(checked) =>
                  updateField("learningTermConfirmationEnabled", checked)
                }
              />
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningGlossaryWebMeaning}
                checked={Boolean(settings.learningGlossaryWebMeaning)}
                onChange={(checked) => updateField("learningGlossaryWebMeaning", checked)}
              />
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningGlossaryRagIndex}
                checked={Boolean(settings.learningGlossaryRagIndex)}
                onChange={(checked) => updateField("learningGlossaryRagIndex", checked)}
              />
            </>
          );
        }

        if (sectionId === "evaluation") {
          return (
            <>
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningEvaluationEnabled}
                checked={Boolean(settings.learningEvaluationEnabled)}
                onChange={(checked) => updateField("learningEvaluationEnabled", checked)}
              />
              <BundleToggleSettingCard
                meta={
                  CHAT_LEARNING_PIPELINE_TOGGLE_META.learningEvaluationBlockPromotion
                }
                checked={Boolean(settings.learningEvaluationBlockPromotion)}
                onChange={(checked) =>
                  updateField("learningEvaluationBlockPromotion", checked)
                }
              />
              <BundleToggleSettingCard
                meta={
                  CHAT_LEARNING_PIPELINE_TOGGLE_META.learningEvaluationCaptureFromFeedback
                }
                checked={Boolean(settings.learningEvaluationCaptureFromFeedback)}
                onChange={(checked) =>
                  updateField("learningEvaluationCaptureFromFeedback", checked)
                }
              />
            </>
          );
        }

        if (sectionId === "finetuning") {
          return (
            <>
              <BundleToggleSettingCard
                meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningFineTuningEnabled}
                checked={Boolean(settings.learningFineTuningEnabled)}
                onChange={(checked) => updateField("learningFineTuningEnabled", checked)}
              />
              <BundleToggleSettingCard
                meta={
                  CHAT_LEARNING_PIPELINE_TOGGLE_META.learningFineTuningCapturePositiveFeedback
                }
                checked={Boolean(settings.learningFineTuningCapturePositiveFeedback)}
                onChange={(checked) =>
                  updateField("learningFineTuningCapturePositiveFeedback", checked)
                }
              />
            </>
          );
        }

        return (
          <>
            <BundleToggleSettingCard
              meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningEnabled}
              checked={Boolean(settings.learningEnabled)}
              onChange={(checked) => updateField("learningEnabled", checked)}
            />
            <BundleToggleSettingCard
              meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningApplyVocabulary}
              checked={Boolean(settings.learningApplyVocabulary)}
              onChange={(checked) => updateField("learningApplyVocabulary", checked)}
            />
            <BundleToggleSettingCard
              meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningCaptureFromFeedback}
              checked={Boolean(settings.learningCaptureFromFeedback)}
              onChange={(checked) =>
                updateField("learningCaptureFromFeedback", checked)
              }
            />
            <BundleToggleSettingCard
              meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningCaptureFromTurn}
              checked={Boolean(settings.learningCaptureFromTurn)}
              onChange={(checked) => updateField("learningCaptureFromTurn", checked)}
            />
            <BundleToggleSettingCard
              meta={CHAT_LEARNING_PIPELINE_TOGGLE_META.learningAutoApproveEnabled}
              checked={Boolean(settings.learningAutoApproveEnabled)}
              onChange={(checked) => updateField("learningAutoApproveEnabled", checked)}
            />
            <BundleNumberSettingCard
              meta={CHAT_LEARNING_PIPELINE_NUMBER_META.learningAutoApproveMinConfidence}
              value={Number(settings.learningAutoApproveMinConfidence)}
              onChange={(value) =>
                updateField("learningAutoApproveMinConfidence", value)
              }
            />
          </>
        );
      }}
    />
  );
}
