const apiUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';

const stats = [
  { label: 'Active Projects', value: 12, trend: '+2 this week' },
  { label: 'Running Jobs', value: 7, trend: '3 scheduled' },
  { label: 'Success Rate (24h)', value: '94%', trend: 'steady' },
  { label: 'Avg Duration', value: '3m 12s', trend: '-18% vs last week' },
];

const projects = [
  { name: 'Ecommerce Pulse', jobs: 14, status: 'healthy', updated: '3m ago' },
  { name: 'News Tracker', jobs: 9, status: 'warning', updated: '12m ago' },
  { name: 'Leads Collector', jobs: 6, status: 'healthy', updated: '27m ago' },
];

const jobs = [
  { name: 'Daily catalog crawl', project: 'Ecommerce Pulse', status: 'running', eta: '1m left' },
  { name: 'Headlines snapshot', project: 'News Tracker', status: 'queued', eta: 'starts in 2m' },
  { name: 'Pricing delta', project: 'Ecommerce Pulse', status: 'failed', eta: 'retrying' },
  { name: 'Contact enrichment', project: 'Leads Collector', status: 'success', eta: 'completed' },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <TopBar />
      <StatGrid />
      <div className="grid gap-6 lg:grid-cols-3">
        <ProjectsCard className="lg:col-span-2" />
        <BackendCard />
      </div>
      <JobsCard />
    </div>
  );
}

function TopBar() {
  return (
    <section className="rounded-xl border border-white/5 bg-gradient-to-r from-emerald-500/20 via-teal-400/10 to-cyan-400/15 px-6 py-5 shadow-lg shadow-emerald-500/10">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-emerald-200/80">Live overview</p>
          <h2 className="text-2xl font-semibold text-white">Scraping fleet status</h2>
          <p className="text-sm text-emerald-100/80">Quick access to health and docs.</p>
        </div>
        <div className="flex gap-2">
          <a
            href={`${apiUrl}/api/v1/health/`}
            className="rounded-lg border border-emerald-300/50 bg-emerald-500/20 px-4 py-2 text-sm font-medium text-emerald-50 transition hover:border-emerald-200 hover:bg-emerald-500/30"
          >
            Check API health
          </a>
          <a
            href={`${apiUrl}/docs`}
            className="rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium text-white/90 transition hover:border-emerald-300/40 hover:bg-white/10"
          >
            Open docs
          </a>
        </div>
      </div>
    </section>
  );
}

function StatGrid() {
  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl border border-white/5 bg-white/5 p-4 shadow-sm shadow-black/20"
        >
          <p className="text-xs uppercase tracking-[0.14em] text-slate-300">{stat.label}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{stat.value}</p>
          <p className="text-sm text-emerald-200/80">{stat.trend}</p>
        </div>
      ))}
    </section>
  );
}

function ProjectsCard({ className = '' }: { className?: string }) {
  return (
    <section
      className={`rounded-xl border border-white/5 bg-white/5 p-5 shadow-sm shadow-black/20 ${className}`}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Projects</h3>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300">
          mock data
        </span>
      </div>
      <div className="mt-4 divide-y divide-white/5">
        {projects.map((proj) => (
          <div key={proj.name} className="flex items-center justify-between py-3">
            <div>
              <p className="text-base font-semibold text-white">{proj.name}</p>
              <p className="text-sm text-slate-300">
                {proj.jobs} jobs · updated {proj.updated}
              </p>
            </div>
            <StatusPill status={proj.status} />
          </div>
        ))}
      </div>
    </section>
  );
}

function JobsCard() {
  return (
    <section className="rounded-xl border border-white/5 bg-white/5 p-5 shadow-sm shadow-black/20">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Recent Jobs</h3>
        <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs uppercase tracking-[0.18em] text-slate-300">
          mock data
        </span>
      </div>
      <div className="mt-4 overflow-hidden rounded-lg border border-white/5">
        <table className="min-w-full divide-y divide-white/5 text-sm">
          <thead className="bg-white/5 text-left text-slate-200">
            <tr>
              <th className="px-4 py-2">Job</th>
              <th className="px-4 py-2">Project</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">ETA</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-slate-100">
            {jobs.map((job) => (
              <tr key={job.name} className="hover:bg-white/5">
                <td className="px-4 py-3">{job.name}</td>
                <td className="px-4 py-3 text-slate-300">{job.project}</td>
                <td className="px-4 py-3">
                  <StatusPill status={job.status} />
                </td>
                <td className="px-4 py-3 text-slate-300">{job.eta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function BackendCard() {
  return (
    <section className="rounded-xl border border-white/5 bg-white/5 p-5 shadow-sm shadow-black/20">
      <h3 className="text-lg font-semibold text-white">Backend endpoints</h3>
      <p className="mt-1 text-sm text-slate-300">
        Quick links to verify the API while you build UI wiring.
      </p>
      <ul className="mt-4 space-y-2">
        <li>
          <a
            className="text-emerald-200 underline underline-offset-4 transition hover:text-emerald-100"
            href={`${apiUrl}/api/v1/health/`}
          >
            {`${apiUrl}/api/v1/health/`}
          </a>
        </li>
        <li>
          <a
            className="text-emerald-200 underline underline-offset-4 transition hover:text-emerald-100"
            href={`${apiUrl}/docs`}
          >
            {`${apiUrl}/docs`}
          </a>
        </li>
      </ul>
    </section>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === 'healthy' || status === 'success'
      ? 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40'
      : status === 'running' || status === 'queued'
        ? 'bg-cyan-500/20 text-cyan-100 border-cyan-300/40'
        : 'bg-amber-500/20 text-amber-100 border-amber-300/50';
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold capitalize ${color}`}
    >
      {status}
    </span>
  );
}
