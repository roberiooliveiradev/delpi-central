import { Component, type ErrorInfo, type ReactNode } from "react";

import { PublicFallback } from "./PublicFallback";

type Props = {
  children: ReactNode;
};

type State = {
  message: string | null;
};

export class PublicErrorBoundary extends Component<Props, State> {
  state: State = { message: null };

  static getDerivedStateFromError(error: Error): State {
    return { message: error.message || "Erro inesperado." };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[public-hub]", error, info.componentStack);
  }

  render() {
    if (this.state.message) {
      return (
        <PublicFallback
          kind="error"
          title="Não foi possível exibir esta página"
          message={this.state.message}
          chrome="kiosk"
        />
      );
    }
    return this.props.children;
  }
}
