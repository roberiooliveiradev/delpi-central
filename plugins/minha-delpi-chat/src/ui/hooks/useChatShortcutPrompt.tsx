import { useCallback, useMemo, useState } from "react";

import {
  buildShortcutPrefill,
  extractProductCodeFromContextChips,
  hasShortcutPlaceholders,
  listShortcutFieldIds,
  normalizeShortcutTemplate,
  resolveShortcutFields,
  type ShortcutPrefillContext,
} from "../chatShortcutPrompt";
import { ChatShortcutPromptDialog } from "../components/ChatShortcutPromptDialog";

type PendingShortcutPrompt = {
  template: string;
  title?: string;
  description?: string;
  prefill?: ShortcutPrefillContext;
  resolve: (query: string | null) => void;
};

type UseChatShortcutPromptOptions = {
  getPrefillContext?: () => ShortcutPrefillContext;
};

export function useChatShortcutPrompt(options: UseChatShortcutPromptOptions = {}) {
  const [pending, setPending] = useState<PendingShortcutPrompt | null>(null);

  const resolveShortcutQuery = useCallback(
    (rawQuery: string, promptOptions?: { title?: string; description?: string }) => {
      const template = normalizeShortcutTemplate(rawQuery.trim());

      if (!template) {
        return Promise.resolve(null);
      }

      if (!hasShortcutPlaceholders(template)) {
        return Promise.resolve(template);
      }

      const fieldIds = listShortcutFieldIds(template);

      if (fieldIds.length === 0) {
        return Promise.resolve(template);
      }

      const prefill: ShortcutPrefillContext = options.getPrefillContext?.() ?? {};

      return new Promise<string | null>((resolve) => {
        setPending({
          template,
          title: promptOptions?.title,
          description: promptOptions?.description,
          prefill,
          resolve,
        });
      });
    },
    [options.getPrefillContext],
  );

  const dialog = useMemo(() => {
    if (!pending) {
      return null;
    }

    const fields = resolveShortcutFields(pending.template);
    const initialValues = buildShortcutPrefill(
      fields.map((field) => field.id),
      pending.prefill,
    );

    return (
      <ChatShortcutPromptDialog
        open
        template={pending.template}
        title={pending.title}
        description={pending.description}
        fields={fields}
        initialValues={initialValues}
        onCancel={() => {
          pending.resolve(null);
          setPending(null);
        }}
        onConfirm={(filledQuery) => {
          pending.resolve(filledQuery);
          setPending(null);
        }}
      />
    );
  }, [pending]);

  return { resolveShortcutQuery, shortcutPromptDialog: dialog };
}

export function useShortcutPrefillFromChips(
  chips: Array<{ kind?: string; value?: string }>,
): ShortcutPrefillContext {
  return useMemo(
    () => ({
      productCode: extractProductCodeFromContextChips(chips),
    }),
    [chips],
  );
}
