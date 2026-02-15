// src/ui/Loader.tsx

export const Loader = () => {
  return (
    <div style={{
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      height: "100vh"
    }}>
      <div style={{
        width: 40,
        height: 40,
        border: "4px solid var(--border)",
        borderTop: "4px solid var(--primary)",
        borderRadius: "50%",
        animation: "spin 1s linear infinite"
      }} />
    </div>
  );
};
