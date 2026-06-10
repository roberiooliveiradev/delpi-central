import { useEffect, useRef, useState } from "react";

export function useAppHostRouteTransition(pathname: string): string {
  const previousPathRef = useRef<string | null>(null);
  const [className, setClassName] = useState("");

  useEffect(() => {
    if (previousPathRef.current === null) {
      previousPathRef.current = pathname;
      return;
    }

    if (previousPathRef.current === pathname) {
      return;
    }

    previousPathRef.current = pathname;
    setClassName("app-host--route-enter");

    const timer = window.setTimeout(() => {
      setClassName("");
    }, 500);

    return () => window.clearTimeout(timer);
  }, [pathname]);

  return className;
}
