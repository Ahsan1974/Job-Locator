"use client";

import { useEffect } from "react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center p-6">
      <div className="glass-panel max-w-md p-8 text-center">
        <h2 className="font-display text-xl font-semibold text-danger">Something went wrong</h2>
        <p className="mt-2 text-sm text-ink-muted">{error.message || "An unexpected error occurred."}</p>
        <button type="button" onClick={reset} className="btn-primary mt-6">
          Try again
        </button>
      </div>
    </div>
  );
}
