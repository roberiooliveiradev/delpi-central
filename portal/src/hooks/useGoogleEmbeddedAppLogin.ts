import { useEffect, useRef, useState } from "react";

const GOOGLE_OPTIONS_DELAY_MS = 1800;

function buildGoogleLoginUrl() {
  return "https://accounts.google.com/AccountChooser";
}

export function isGoogleHostedApp(url: string | undefined) {
  if (!url) return false;

  try {
    const parsed = new URL(url, window.location.origin);

    return (
      parsed.hostname === "script.google.com" ||
      parsed.hostname.endsWith(".googleusercontent.com") ||
      parsed.hostname.endsWith(".google.com")
    );
  } catch {
    return false;
  }
}

type UseGoogleEmbeddedAppLoginParams = {
  enabled: boolean;
  pathname: string;
  resolvedEntry?: string;
  onReloadIframe: () => void;
};

export function useGoogleEmbeddedAppLogin({
  enabled,
  pathname,
  resolvedEntry,
  onReloadIframe,
}: UseGoogleEmbeddedAppLoginParams) {
  const loginTabOpenedRef = useRef(false);
  const optionsInitializedRef = useRef<string | null>(null);

  const [barVisible, setBarVisible] = useState(false);
  const [optionsAvailable, setOptionsAvailable] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [popupBlocked, setPopupBlocked] = useState(false);

  function openGoogleLogin() {
    const loginTab = window.open(
      buildGoogleLoginUrl(),
      "_blank",
      "noopener,noreferrer"
    );

    setShowHelp(true);
    setBarVisible(true);
    setOptionsAvailable(true);

    if (!loginTab) {
      setPopupBlocked(true);
      return;
    }

    loginTabOpenedRef.current = true;
    setPopupBlocked(false);
  }

  function handleLoginReturn() {
    if (!loginTabOpenedRef.current) return;

    loginTabOpenedRef.current = false;

    setShowHelp(false);
    setPopupBlocked(false);
    setBarVisible(false);
    setOptionsAvailable(true);

    onReloadIframe();
  }

  function closeBar() {
    setBarVisible(false);
  }

  function showBar() {
    setBarVisible(true);
    setOptionsAvailable(true);
  }

  function reset() {
    loginTabOpenedRef.current = false;

    setBarVisible(false);
    setOptionsAvailable(false);
    setShowHelp(false);
    setPopupBlocked(false);
  }

  useEffect(() => {
    reset();
  }, [enabled, pathname, resolvedEntry]);

  useEffect(() => {
    if (!enabled) return;
    if (!resolvedEntry) return;

    const attemptKey = `${pathname}|${resolvedEntry}`;

    if (optionsInitializedRef.current === attemptKey) return;

    optionsInitializedRef.current = attemptKey;

    const timer = window.setTimeout(() => {
      setOptionsAvailable(true);
    }, GOOGLE_OPTIONS_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [enabled, pathname, resolvedEntry]);

  useEffect(() => {
    function onWindowFocus() {
      handleLoginReturn();
    }

    function onVisibilityChange() {
      if (document.visibilityState === "visible") {
        handleLoginReturn();
      }
    }

    window.addEventListener("focus", onWindowFocus);
    document.addEventListener("visibilitychange", onVisibilityChange);

    return () => {
      window.removeEventListener("focus", onWindowFocus);
      document.removeEventListener("visibilitychange", onVisibilityChange);
    };
  }, [onReloadIframe]);

  return {
    barVisible,
    optionsAvailable,
    showHelp,
    popupBlocked,
    openGoogleLogin,
    closeBar,
    showBar,
  };
}