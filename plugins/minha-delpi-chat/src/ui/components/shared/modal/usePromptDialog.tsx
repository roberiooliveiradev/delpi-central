import { useCallback, useMemo, useState } from "react";

import { ChatPromptDialog } from "./ChatPromptDialog";

type PromptOptions = {
  title: string;
  description?: string;
  label?: string;
  defaultValue?: string;
  placeholder?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  maxLength?: number;
};

type PendingPrompt = PromptOptions & {
  resolve: (value: string | null) => void;
};

export function usePromptDialog() {
  const [pending, setPending] = useState<PendingPrompt | null>(null);

  const prompt = useCallback((options: PromptOptions) => {
    return new Promise<string | null>((resolve) => {
      setPending({ ...options, resolve });
    });
  }, []);

  const dialog = useMemo(() => {
    if (!pending) {
      return null;
    }

    return (
      <ChatPromptDialog
        open
        title={pending.title}
        description={pending.description}
        label={pending.label}
        defaultValue={pending.defaultValue}
        placeholder={pending.placeholder}
        confirmLabel={pending.confirmLabel}
        cancelLabel={pending.cancelLabel}
        maxLength={pending.maxLength}
        onCancel={() => {
          pending.resolve(null);
          setPending(null);
        }}
        onConfirm={(value) => {
          pending.resolve(value);
          setPending(null);
        }}
      />
    );
  }, [pending]);

  return { prompt, dialog };
}
