import { useCallback, useMemo, useRef, useState } from "react";

import {
  buildShortcutPrefill,
  extractProductCodeFromContextChips,
  hasShortcutPlaceholders,
  normalizeShortcutTemplate,
  resolveShortcutFields,
  type ShortcutFieldDefinition,
  type ShortcutPrefillContext,
} from "../chatShortcutPrompt";
import { ChatShortcutPromptDialog } from "../components/shared";

type PendingShortcutPrompt = {
  template: string;
  title?: string;
  description?: string;
  confirmLabel?: string;
  fields?: ShortcutFieldDefinition[];
  prefill?: ShortcutPrefillContext;
  resolve: (query: string | null) => void;
};

export type ShortcutPromptOptions = {
  title?: string;
  description?: string;
  confirmLabel?: string;
  fields?: import("../chatShortcutPrompt").ShortcutFieldDefinition[];
};

type UseChatShortcutPromptOptions = {
  getPrefillContext?: () => ShortcutPrefillContext;
};

export function useChatShortcutPrompt(options: UseChatShortcutPromptOptions = {}) {
  const [pending, setPending] = useState<PendingShortcutPrompt | null>(null);
  const pendingRef = useRef<PendingShortcutPrompt | null>(null);
  const isOpenRef = useRef(false);
  const getPrefillContextRef = useRef(options.getPrefillContext);
  getPrefillContextRef.current = options.getPrefillContext;

  const closePending = useCallback((result: string | null) => {
    const current = pendingRef.current;

    if (current) {
      current.resolve(result);
    }

    pendingRef.current = null;
    isOpenRef.current = false;
    setPending(null);
  }, []);

  const resolveShortcutQuery = useCallback(
    (rawQuery: string, promptOptions?: ShortcutPromptOptions) => {
      const template = normalizeShortcutTemplate(rawQuery.trim());

      if (!template) {
        return Promise.resolve(null);
      }

      if (!hasShortcutPlaceholders(template)) {
        return Promise.resolve(template);
      }

      const fields = promptOptions?.fields ?? resolveShortcutFields(template);

      if (fields.length === 0) {
        return Promise.resolve(null);
      }

      const prefill: ShortcutPrefillContext = getPrefillContextRef.current?.() ?? {};

      return new Promise<string | null>((resolve) => {
        if (pendingRef.current) {
          pendingRef.current.resolve(null);
        }

        const entry: PendingShortcutPrompt = {
          template,
          title: promptOptions?.title,
          description: promptOptions?.description,
          confirmLabel: promptOptions?.confirmLabel,
          fields,
          prefill,
          resolve,
        };

        pendingRef.current = entry;
        isOpenRef.current = true;
        setPending(entry);
      });
    },
    [],
  );

  const isShortcutPromptOpen = useCallback(() => isOpenRef.current, []);

  const dialog = useMemo(() => {
    if (!pending) {
      return null;
    }

    const fields = pending.fields ?? resolveShortcutFields(pending.template);
    const initialValues = buildShortcutPrefill(
      fields.map((field) => field.id),
      pending.prefill,
    );

    return (
      <ChatShortcutPromptDialog
        key={pending.template}
        open
        template={pending.template}
        title={pending.title}
        description={pending.description}
        confirmLabel={pending.confirmLabel}
        fields={fields}
        initialValues={initialValues}
        onCancel={() => closePending(null)}
        onConfirm={(filledQuery) => closePending(filledQuery)}
      />
    );
  }, [closePending, pending]);

  return { resolveShortcutQuery, shortcutPromptDialog: dialog, isShortcutPromptOpen };
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
