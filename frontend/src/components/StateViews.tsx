export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <div className="state state--loading">{label}</div>;
}

export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="state">
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}

export function ErrorState({
  title,
  message,
  onRetry,
}: {
  title: string;
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="state state--error">
      <h3>{title}</h3>
      <p>{message}</p>
      {onRetry ? (
        <button className="button" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}
