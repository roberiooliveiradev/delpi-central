import { useCallback, useMemo, useState } from "react";

import { ChatConfirmDialog } from "./ChatConfirmDialog";

type ConfirmOptions = {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
};

type PendingConfirm = ConfirmOptions & {
  resolve: (value: boolean) => void;
};

export function useConfirmDialog() {
  const [pending, setPending] = useState<PendingConfirm | null>(null);

  const confirm = useCallback((options: ConfirmOptions) => {
    return new Promise<boolean>((resolve) => {
      setPending({ ...options, resolve });
    });
  }, []);

  const dialog = useMemo(() => {
    if (!pending) return null;

    return (
      <ChatConfirmDialog
        open
        title={pending.title}
        description={pending.description}
        confirmLabel={pending.confirmLabel}
        cancelLabel={pending.cancelLabel}
        danger={pending.danger}
        onCancel={() => {
          pending.resolve(false);
          setPending(null);
        }}
        onConfirm={() => {
          pending.resolve(true);
          setPending(null);
        }}
      />
    );
  }, [pending]);

  return { confirm, dialog };
}

