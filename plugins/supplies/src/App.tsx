export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  basePath?: string;
  search?: string;
};

export default function App({}: AppProps) {
  return (
    <div className="dashboard-supplies-portal dashboard-page">
      <h1>Portal Suprimentos</h1>
    </div>
  );
}
