const readinessItems = [
  { label: "Frontend", value: "Running" },
  { label: "Backend", value: "Health API" },
  { label: "Database", value: "Phase 1" },
  { label: "Authentication", value: "Phase 2" },
];

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <header className="border-b border-border pb-6">
          <p className="text-sm font-medium text-primary">NEXUS operations</p>
          <h1 className="mt-2 text-3xl font-semibold text-slate-950">
            Platform foundation
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-700">
            Phase 0 confirms the application shell, backend API process, and
            repository structure are ready for database work.
          </p>
        </header>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {readinessItems.map((item) => (
            <article
              className="rounded-lg border border-border bg-white p-5 shadow-sm"
              key={item.label}
            >
              <p className="text-sm text-slate-500">{item.label}</p>
              <p className="mt-2 text-xl font-semibold text-slate-950">
                {item.value}
              </p>
            </article>
          ))}
        </section>
      </div>
    </main>
  );
}

