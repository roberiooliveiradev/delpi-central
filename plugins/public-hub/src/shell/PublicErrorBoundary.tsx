import { Component, type ErrorInfo, type ReactNode } from "react";

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
        <div className="pub-fallback pub-fallback--fatal">
          <h1>Não foi possível exibir esta página</h1>
          <p>{this.state.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
