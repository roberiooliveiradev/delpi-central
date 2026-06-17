import { useCallback, useMemo, useState } from "react";

import { ChatAlertDialog } from "./ChatAlertDialog";

type AlertOptions = {
  title?: string;
  message: string;
  confirmLabel?: string;
};

type PendingAlert = AlertOptions & {
  resolve: () => void;
};

export function useAlertDialog() {
  const [pending, setPending] = useState<PendingAlert | null>(null);

  const alert = useCallback((options: AlertOptions | string) => {
    const normalized =
      typeof options === "string" ? { message: options } : options;

    return new Promise<void>((resolve) => {
      setPending({
        ...normalized,
        resolve,
      });
    });
  }, []);

  const dialog = useMemo(() => {
    if (!pending) {
      return null;
    }

    return (
      <ChatAlertDialog
        open
        title={pending.title}
        message={pending.message}
        confirmLabel={pending.confirmLabel}
        onClose={() => {
          pending.resolve();
          setPending(null);
        }}
      />
    );
  }, [pending]);

  return { alert, dialog };
}
