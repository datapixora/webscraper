'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import { useProjects } from '@/hooks/useProjects';
import { useJobs } from '@/hooks/useJobs';
import { useCampaigns } from '@/hooks/useCampaigns';
import { useTopics } from '@/hooks/useTopics';

type StatCardProps = {
  title: string;
  value: string | number;
  sublabel?: string;
  href?: string;
};

function StatCard({ title, value, sublabel, href }: StatCardProps) {
  const content = (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 transition hover:border-emerald-300/40 hover:bg-white/10">
      <p className="text-xs uppercase tracking-[0.16em] text-emerald-200/80">{title}</p>
      <div className="mt-2 text-3xl font-semibold text-white">{value}</div>
      {sublabel && <p className="mt-1 text-sm text-slate-300">{sublabel}</p>}
    </div>
  );
  if (href) {
    return (
      <Link href={href} className="block">
        {content}
      </Link>
    );
  }
  return content;
}

function StatusPill({ text, tone = 'neutral' }: { text: string; tone?: 'success' | 'warn' | 'error' | 'info' | 'neutral' }) {
  const styles = {
    success: 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40',
    warn: 'bg-amber-500/20 text-amber-100 border-amber-300/40',
    error: 'bg-red-500/20 text-red-100 border-red-300/40',
    info: 'bg-cyan-500/20 text-cyan-100 border-cyan-300/40',
    neutral: 'bg-slate-500/20 text-slate-100 border-slate-300/40',
  } as const;
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold capitalize ${styles[tone]}`}>
      {text}
    </span>
  );
}

export default function DashboardPage() {
  const { projectsQuery } = useProjects();
  const { jobsQuery } = useJobs();
  const { campaignsQuery } = useCampaigns();
  const { topicsQuery } = useTopics();

  const projectNames = useMemo(() => {
    const map = new Map<string, string>();
    (projectsQuery.data ?? []).forEach((p) => map.set(p.id, p.name));
    return map;
  }, [projectsQuery.data]);

  const jobCounts = useMemo(() => {
    const counts = { total: jobsQuery.data?.length ?? 0, succeeded: 0, running: 0, pending: 0, failed: 0 };
    (jobsQuery.data ?? []).forEach((job) => {
      const s = (job.status || '').toLowerCase();
      if (s.includes('success')) counts.succeeded += 1;
      else if (s.includes('fail')) counts.failed += 1;
      else if (s.includes('run')) counts.running += 1;
      else counts.pending += 1;
    });
    return counts;
  }, [jobsQuery.data]);

  const recentJobs = useMemo(() => {
    const sorted = [...(jobsQuery.data ?? [])].sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    );
    return sorted.slice(0, 5);
  }, [jobsQuery.data]);

  const campaignSummary = useMemo(() => {
    const campaigns = campaignsQuery.data ?? [];
    const pages = campaigns.reduce((acc, c) => acc + (c.pages_collected ?? 0), 0);
    return { total: campaigns.length, pages };
  }, [campaignsQuery.data]);

  const topicSummary = useMemo(() => {
    const topics = topicsQuery.data ?? [];
    const completed = topics.filter((t) => t.status === 'completed').length;
    return { total: topics.length, completed };
  }, [topicsQuery.data]);

  const topCampaigns = useMemo(() => (campaignsQuery.data ?? []).slice(0, 3), [campaignsQuery.data]);
  const topTopics = useMemo(() => (topicsQuery.data ?? []).slice(0, 3), [topicsQuery.data]);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-white/5 bg-gradient-to-r from-emerald-900/30 via-emerald-800/20 to-slate-900/40 p-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-200/80">Live overview</p>
            <h2 className="mt-2 text-2xl font-semibold text-white">Scraping & discovery pulse</h2>
            <p className="mt-1 text-sm text-slate-300">
              Real-time counts pulled from your API — no sample data.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-sm">
            <Link href="/projects" className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 hover:border-emerald-300/40">
              Manage Projects
            </Link>
            <Link href="/jobs" className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 hover:border-emerald-300/40">
              View Jobs
            </Link>
            <Link href="/topics" className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 hover:border-emerald-300/40">
              Topics
            </Link>
            <Link href="/campaigns" className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 hover:border-emerald-300/40">
              Campaigns
            </Link>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard title="Projects" value={projectsQuery.data ? projectsQuery.data.length : '...'} sublabel="Active extraction schemas" href="/projects" />
        <StatCard
          title="Jobs"
          value={jobCounts.total}
          sublabel={`Running ${jobCounts.running} · Pending ${jobCounts.pending} · Success ${jobCounts.succeeded} · Failed ${jobCounts.failed}`}
          href="/jobs"
        />
        <StatCard
          title="Campaigns"
          value={campaignSummary.total}
          sublabel={`Pages collected ${campaignSummary.pages}`}
          href="/campaigns"
        />
        <StatCard
          title="Topics"
          value={topicSummary.total}
          sublabel={`${topicSummary.completed} completed searches`}
          href="/topics"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-white/5 bg-white/5 p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Recent jobs</h3>
              <p className="text-sm text-slate-300">Latest executions across all projects.</p>
            </div>
            <Link href="/jobs" className="text-sm text-emerald-300 hover:underline">
              View all
            </Link>
          </div>
          {jobsQuery.isLoading && <p className="mt-3 text-sm text-slate-300">Loading jobs...</p>}
          {jobsQuery.isError && (
            <p className="mt-3 text-sm text-amber-300">Failed to load jobs: {(jobsQuery.error as Error).message}</p>
          )}
          {!jobsQuery.isLoading && recentJobs.length === 0 && (
            <p className="mt-3 text-sm text-slate-300">No jobs yet.</p>
          )}
          {recentJobs.length > 0 && (
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full divide-y divide-white/5 text-sm">
                <thead className="bg-white/5 text-left text-slate-200">
                  <tr>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2">Project</th>
                    <th className="px-3 py-2">Status</th>
                    <th className="px-3 py-2">Updated</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-100">
                  {recentJobs.map((job) => (
                    <tr key={job.id} className="hover:bg-white/5">
                      <td className="px-3 py-2 font-semibold text-white">{job.name}</td>
                      <td className="px-3 py-2 text-slate-300">
                        {projectNames.get(job.project_id) ?? job.project_id}
                      </td>
                      <td className="px-3 py-2">
                        <JobStatus status={job.status} />
                      </td>
                      <td className="px-3 py-2 text-slate-400">{new Date(job.updated_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-white/5 bg-white/5 p-5">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">Topics & discovery</h3>
              <p className="text-sm text-slate-300">Latest topic searches and auto-crawl seeds.</p>
            </div>
            <Link href="/topics" className="text-sm text-emerald-300 hover:underline">
              Manage topics
            </Link>
          </div>
          {topicsQuery.isLoading && <p className="mt-3 text-sm text-slate-300">Loading topics...</p>}
          {topicsQuery.isError && (
            <p className="mt-3 text-sm text-amber-300">Failed to load topics: {(topicsQuery.error as Error).message}</p>
          )}
          {topTopics.length === 0 && !topicsQuery.isLoading && (
            <p className="mt-3 text-sm text-slate-300">No topics yet. Create one to collect URLs.</p>
          )}
          {topTopics.length > 0 && (
            <ul className="mt-3 divide-y divide-white/5">
              {topTopics.map((topic) => (
                <li key={topic.id} className="flex items-start justify-between py-3">
                  <div>
                    <p className="text-base font-semibold text-white">{topic.name}</p>
                    <p className="text-sm text-slate-300">{topic.query}</p>
                    <p className="text-xs text-slate-400">
                      Max results {topic.max_results} · {new Date(topic.created_at).toLocaleString()}
                    </p>
                  </div>
                  <StatusPill
                    text={topic.status}
                    tone={
                      topic.status === 'completed'
                        ? 'success'
                        : topic.status === 'failed'
                          ? 'error'
                          : topic.status === 'searching'
                            ? 'info'
                            : 'neutral'
                    }
                  />
                </li>
              ))}
            </ul>
          )}
          <div className="mt-4 rounded-lg border border-white/10 bg-slate-900/70 p-3 text-sm text-slate-200">
            <p className="font-semibold text-white">Quick tip</p>
            <p className="text-slate-300">
              Create a topic, let it collect URLs, tick the checkboxes, then trigger scraping jobs. Jobs will show up on
              the Jobs page in seconds.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Campaigns snapshot</h3>
            <p className="text-sm text-slate-300">Auto-crawl campaigns and their progress.</p>
          </div>
          <Link href="/campaigns" className="text-sm text-emerald-300 hover:underline">
            View campaigns
          </Link>
        </div>
        {campaignsQuery.isLoading && <p className="mt-3 text-sm text-slate-300">Loading campaigns...</p>}
        {campaignsQuery.isError && (
          <p className="mt-3 text-sm text-amber-300">
            Failed to load campaigns: {(campaignsQuery.error as Error).message}
          </p>
        )}
        {topCampaigns.length === 0 && !campaignsQuery.isLoading && (
          <p className="mt-3 text-sm text-slate-300">No campaigns yet.</p>
        )}
        {topCampaigns.length > 0 && (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/5 text-sm">
              <thead className="bg-white/5 text-left text-slate-200">
                <tr>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Pages</th>
                  <th className="px-3 py-2">Max</th>
                  <th className="px-3 py-2">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-100">
                {topCampaigns.map((c) => (
                  <tr key={c.id} className="hover:bg-white/5">
                    <td className="px-3 py-2 font-semibold text-white">
                      <Link className="hover:underline" href={`/campaigns/${c.id}`}>
                        {c.name}
                      </Link>
                      <div className="text-xs text-slate-400">{c.query}</div>
                    </td>
                    <td className="px-3 py-2">
                      <StatusPill
                        text={c.status}
                        tone={
                          c.status === 'active'
                            ? 'info'
                            : c.status === 'failed'
                              ? 'error'
                              : c.status === 'completed'
                                ? 'success'
                                : 'neutral'
                        }
                      />
                    </td>
                    <td className="px-3 py-2">{c.pages_collected}</td>
                    <td className="px-3 py-2 text-slate-300">{c.max_pages}</td>
                    <td className="px-3 py-2 text-slate-400">{new Date(c.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function JobStatus({ status }: { status: string }) {
  const normalized = (status || '').toLowerCase();
  let tone: 'success' | 'warn' | 'error' | 'info' | 'neutral' = 'neutral';
  if (normalized.includes('success')) tone = 'success';
  else if (normalized.includes('fail')) tone = 'error';
  else if (normalized.includes('run')) tone = 'info';
  else if (normalized.includes('pending')) tone = 'warn';
  return <StatusPill text={status} tone={tone} />;
}
