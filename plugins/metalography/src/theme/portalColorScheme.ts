import { useEffect, useState } from "react";

export function readPortalColorScheme(): "light" | "dark" {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

export function usePortalColorScheme(): "light" | "dark" {
  const [scheme, setScheme] = useState(readPortalColorScheme);
  useEffect(() => {
    const root = document.documentElement;
    const observer = new MutationObserver(() => setScheme(readPortalColorScheme()));
    observer.observe(root, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);
  return scheme;
}
