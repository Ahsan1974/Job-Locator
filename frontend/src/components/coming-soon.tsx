export default function ComingSoonPage({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mx-auto max-w-xl py-16 text-center animate-fade-up">
      <div className="glass-panel p-10">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-accent">Coming soon</p>
        <h1 className="mt-3 font-display text-3xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-3 text-sm text-ink-muted">{description}</p>
      </div>
    </div>
  );
}
