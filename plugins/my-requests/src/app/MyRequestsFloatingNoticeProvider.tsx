import {
  createContext,
  useCallback,
  useContext,
  type ReactNode,
} from "react";
import {
  createFloatingNoticeStack,
  useFloatingNotices,
  type FloatingNoticeInput,
} from "@delpi/plugin-ui/index";

import {
  humanizeApiErrorCode,
  isTechnicalErrorCode,
} from "../content/apiErrorMessages";

const MR_UI_PREFIX = "my-requests";
const MR_PORTAL_SCOPE = "dashboard-my-requests";

const PAGE_ERROR_NOTICE_ID = "mr-page-error";
const PAGE_SUCCESS_NOTICE_ID = "mr-page-success";

type MyRequestsFloatingNoticeContextValue = {
  notice: (input: FloatingNoticeInput | string) => string;
  notifySuccess: (message: string, options?: { title?: string; id?: string }) => string;
  notifyInfo: (
    message: string,
    options?: { title?: string; id?: string; autoDismissMs?: number | null },
  ) => string;
  notifyWarning: (
    message: string,
    options?: { title?: string; id?: string; autoDismissMs?: number | null },
  ) => string;
  notifyError: (
    message: string,
    options?: { title?: string; id?: string; autoDismissMs?: number | null },
  ) => string;
  dismiss: (id: string) => void;
};

const MyRequestsFloatingNoticeContext =
  createContext<MyRequestsFloatingNoticeContextValue | null>(null);

const MyRequestsFloatingNotices = createFloatingNoticeStack({
  prefix: MR_UI_PREFIX,
  portalScopeClassName: MR_PORTAL_SCOPE,
  labels: {
    stackAriaLabel: "Avisos de Minhas Solicitações",
    dismissAriaLabel: "Fechar aviso",
  },
});

type ParsedErrorBody = {
  message?: string;
  detail?: string | unknown;
  data?: { message?: string; code?: string; field?: string };
};

function messageFromParsedBody(body: ParsedErrorBody): string | null {
  const code = typeof body.data?.code === "string" ? body.data.code.trim() : "";
  const field =
    typeof body.data?.field === "string" ? body.data.field.trim() : null;
  const candidates = [
    typeof body.message === "string" ? body.message.trim() : "",
    typeof body.detail === "string" ? body.detail.trim() : "",
    typeof body.data?.message === "string" ? body.data.message.trim() : "",
  ].filter(Boolean);

  for (const candidate of candidates) {
    if (isTechnicalErrorCode(candidate)) {
      return (
        humanizeApiErrorCode(candidate, { field }) ||
        humanizeApiErrorCode(code, { field }) ||
        candidate
      );
    }
    return candidate;
  }
  if (code) {
    return humanizeApiErrorCode(code, { field }) || code;
  }
  return null;
}

/** Extract a user-facing message from API/JSON error payloads. */
export function friendlyNoticeMessage(raw: unknown, fallback: string): string {
  if (typeof raw !== "string") {
    if (raw instanceof Error && raw.message.trim()) {
      return friendlyNoticeMessage(raw.message, fallback);
    }
    return fallback;
  }
  const trimmed = raw.trim();
  if (!trimmed) return fallback;
  if (trimmed.startsWith("{") || trimmed.startsWith("[")) {
    try {
      const body = JSON.parse(trimmed) as ParsedErrorBody;
      const fromBody = messageFromParsedBody(body);
      if (fromBody) return fromBody;
    } catch {
      // keep trimmed text
    }
  }
  if (isTechnicalErrorCode(trimmed)) {
    return humanizeApiErrorCode(trimmed) || fallback;
  }
  return trimmed;
}

export function MyRequestsFloatingNoticeProvider({
  children,
}: {
  children: ReactNode;
}) {
  const { items, push, dismiss } = useFloatingNotices();

  const notice = useCallback(
    (input: FloatingNoticeInput | string) => {
      if (typeof input === "string") {
        return push({
          message: friendlyNoticeMessage(input, "Ocorreu um erro."),
          variant: "error",
        });
      }
      return push({
        variant: "error",
        ...input,
        message: friendlyNoticeMessage(input.message, "Ocorreu um erro."),
      });
    },
    [push],
  );

  const notifySuccess = useCallback(
    (message: string, options?: { title?: string; id?: string }) =>
      notice({
        id: options?.id ?? PAGE_SUCCESS_NOTICE_ID,
        variant: "success",
        title: options?.title ?? "Pronto",
        message,
      }),
    [notice],
  );

  const notifyInfo = useCallback(
    (
      message: string,
      options?: { title?: string; id?: string; autoDismissMs?: number | null },
    ) =>
      notice({
        id: options?.id,
        variant: "info",
        title: options?.title ?? "Atualização",
        message,
        autoDismissMs: options?.autoDismissMs ?? 6500,
      }),
    [notice],
  );

  const notifyWarning = useCallback(
    (
      message: string,
      options?: { title?: string; id?: string; autoDismissMs?: number | null },
    ) =>
      notice({
        id: options?.id,
        variant: "warning",
        title: options?.title ?? "Atenção",
        message,
        autoDismissMs: options?.autoDismissMs ?? 6500,
      }),
    [notice],
  );

  const notifyError = useCallback(
    (
      message: string,
      options?: { title?: string; id?: string; autoDismissMs?: number | null },
    ) =>
      notice({
        id: options?.id ?? PAGE_ERROR_NOTICE_ID,
        variant: "error",
        title: options?.title ?? "Não foi possível concluir",
        message,
        autoDismissMs: options?.autoDismissMs ?? 8000,
      }),
    [notice],
  );

  return (
    <MyRequestsFloatingNoticeContext.Provider
      value={{
        notice,
        notifySuccess,
        notifyInfo,
        notifyWarning,
        notifyError,
        dismiss,
      }}
    >
      {children}
      <MyRequestsFloatingNotices items={items} onDismiss={dismiss} />
    </MyRequestsFloatingNoticeContext.Provider>
  );
}

export function useMyRequestsFloatingNotice(): MyRequestsFloatingNoticeContextValue {
  const context = useContext(MyRequestsFloatingNoticeContext);
  if (!context) {
    throw new Error(
      "useMyRequestsFloatingNotice deve ser usado dentro de MyRequestsFloatingNoticeProvider.",
    );
  }
  return context;
}

export { PAGE_ERROR_NOTICE_ID, PAGE_SUCCESS_NOTICE_ID };
