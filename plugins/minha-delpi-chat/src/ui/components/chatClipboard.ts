const COPY_FEEDBACK_MS = 1800;

export async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";

  document.body.appendChild(textarea);
  textarea.select();

  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

export function scheduleCopyFeedback(
  setCopied: (value: boolean) => void,
  timeoutMs = COPY_FEEDBACK_MS,
): number {
  return window.setTimeout(() => setCopied(false), timeoutMs);
}
