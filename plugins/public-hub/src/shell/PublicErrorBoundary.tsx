import { Component, type ErrorInfo, type ReactNode } from "react";

import {
  isStaleModuleLoadError,
  requestAssetRecover,
} from "../../../vite/assetRecover";

import { PublicFallback } from "./PublicFallback";
import { PublicLoadingSplash } from "./PublicLoadingSplash";

type Props = {
  children: ReactNode;
};

type State = {
  message: string | null;
  /** Chunk lazy stale — não re-renderizar filhos (evita loop). */
  staleChunk: boolean;
};

export class PublicErrorBoundary extends Component<Props, State> {
  state: State = { message: null, staleChunk: false };

  static getDerivedStateFromError(error: Error): State {
    if (isStaleModuleLoadError(error.message)) {
      return { message: null, staleChunk: true };
    }
    return {
      message: error.message || "Erro inesperado.",
      staleChunk: false,
    };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (isStaleModuleLoadError(error.message)) {
      if (requestAssetRecover()) {
        return;
      }
      this.setState({
        message:
          "A visualização não pôde ser atualizada após a última atualização do sistema.",
        staleChunk: true,
      });
      return;
    }
    console.error("[public-hub]", error, info.componentStack);
  }

  render() {
    if (this.state.staleChunk) {
      if (!this.state.message) {
        return <PublicLoadingSplash chrome="kiosk" label="Atualizando visualização" />;
      }
      return (
        <PublicFallback
          kind="error"
          title="Não foi possível exibir esta página"
          message={this.state.message}
          chrome="kiosk"
          showRetry
          onRetry={() => requestAssetRecover({ force: true })}
        />
      );
    }

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
