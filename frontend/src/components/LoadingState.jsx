export default function LoadingState({ message = "Loading..." }) {
  return (
    <div className="loading-state" role="status">
      <div className="spinner" />
      <p className="muted">{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="banner banner-error" role="alert">
      <div>
        <strong>Something went wrong.</strong>
        <div>{message}</div>
      </div>
      {onRetry ? (
        <button className="btn btn-secondary btn-small" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, message, children }) {
  return (
    <div className="empty-state">
      <h2>{title}</h2>
      {message ? <p className="muted">{message}</p> : null}
      {children ? <div className="row center">{children}</div> : null}
    </div>
  );
}