import { Activity, Building2, Server } from "lucide-react";

const milestones = [
  "Monorepo initialized",
  "FastAPI health endpoint ready",
  "Next.js App Router configured",
  "Docs and environment templates created",
];

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <section className="mx-auto flex min-h-screen w-full max-w-6xl flex-col justify-center px-6 py-12">
        <div className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm font-medium text-slate-700">
              <Activity aria-hidden="true" className="h-4 w-4 text-primary" />
              Phase 0 initialization
            </div>
            <h1 className="max-w-3xl text-5xl font-semibold tracking-normal text-slate-950">
              NEXUS
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-700">
              A production-minded foundation for a multi-branch business
              management and analytics platform.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-3 text-sm font-semibold text-white"
                href="/dashboard"
              >
                <Building2 aria-hidden="true" className="h-4 w-4" />
                Open dashboard
              </a>
              <a
                className="inline-flex items-center gap-2 rounded-md border border-border bg-white px-4 py-3 text-sm font-semibold text-slate-900"
                href={`${process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === "production" ? "/api/v1" : "http://localhost:8000/api/v1")}/health`}
              >
                <Server aria-hidden="true" className="h-4 w-4" />
                API health
              </a>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-white p-6 shadow-sm">
            <h2 className="text-base font-semibold text-slate-950">
              Foundation status
            </h2>
            <ul className="mt-5 space-y-4">
              {milestones.map((item) => (
                <li key={item} className="flex items-center gap-3 text-sm text-slate-700">
                  <span className="h-2.5 w-2.5 rounded-full bg-accent" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>
    </main>
  );
}

