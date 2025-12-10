"use client";

"use client";

import { useMemo, useState } from 'react';
import { JsonViewer } from '@/components/json-viewer';
import { useJobs } from '@/hooks/useJobs';
import { useJobResult } from '@/hooks/useJobResult';
import { useProjects } from '@/hooks/useProjects';
import { apiBase } from '@/lib/api-client';

export default function JobsPage() {
  const { jobsQuery } = useJobs();
  const { projectsQuery } = useProjects();
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const resultQuery = useJobResult(selectedJobId ?? undefined);

  const jobs = useMemo(() => jobsQuery.data ?? [], [jobsQuery.data]);

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-white">Jobs</h2>
            <p className="text-sm text-slate-300">Select a job to view details and results.</p>
          </div>
          {jobsQuery.isFetching && <span className="text-xs text-slate-300">Refreshing...</span>}
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full divide-y divide-white/5 text-sm">
            <thead className="bg-white/5 text-left text-slate-200">
              <tr>
                <th className="px-3 py-2">Job</th>
                <th className="px-3 py-2">Project</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Target URL</th>
                <th className="px-3 py-2">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-slate-100">
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  className={`cursor-pointer hover:bg-white/5 ${selectedJobId === job.id ? 'bg-white/10' : ''}`}
                  onClick={() => setSelectedJobId(job.id)}
                >
                  <td className="px-3 py-2 font-semibold text-white">{job.name}</td>
                  <td className="px-3 py-2 text-slate-300">
                    {projectsQuery.data?.find((p) => p.id === job.project_id)?.name ?? job.project_id}
                  </td>
                  <td className="px-3 py-2">
                    <StatusPill status={job.status} />
                  </td>
                  <td className="px-3 py-2 text-emerald-200 truncate max-w-[240px]">{job.target_url}</td>
                  <td className="px-3 py-2 text-slate-400">
                    {new Date(job.updated_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {jobsQuery.isError && (
          <p className="mt-2 text-sm text-amber-300">
            Failed to load jobs: {(jobsQuery.error as Error).message}
          </p>
        )}
      </div>

      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <h3 className="text-lg font-semibold text-white">Result</h3>
        {!selectedJobId && <p className="text-sm text-slate-300">Select a job to view its result.</p>}
        {selectedJobId && resultQuery.isLoading && (
          <p className="text-sm text-slate-300">Loading result...</p>
        )}
        {selectedJobId && resultQuery.isError && (
          <p className="text-sm text-amber-300">
            Failed to load result: {(resultQuery.error as Error).message}
          </p>
        )}
        {selectedJobId && resultQuery.data && (
          <div className="mt-3 space-y-3">
            <div>
              <p className="text-xs text-slate-400">Structured Data</p>
              <JsonViewer data={resultQuery.data.structured_data ?? {}} />
            </div>
            <div>
              <p className="text-xs text-slate-400">Raw HTML (truncated)</p>
              <div className="max-h-64 overflow-auto rounded-lg border border-white/10 bg-slate-900/70 p-3 text-xs text-slate-200">
                {resultQuery.data.raw_html?.slice(0, 5000) ?? 'No HTML stored'}
              </div>
              <div className="mt-2 grid grid-cols-1 gap-2 text-[11px] text-slate-400 md:grid-cols-3">
                <div className="truncate">
                  <span className="text-slate-500">Path: </span>
                  <span className="text-emerald-200">{resultQuery.data.raw_html_path ?? 'n/a'}</span>
                </div>
                <div className="truncate">
                  <span className="text-slate-500">Checksum: </span>
                  <span className="text-slate-200">
                    {resultQuery.data.raw_html_checksum?.slice(0, 12) ?? 'n/a'}
                  </span>
                </div>
                <div className="truncate">
                  <span className="text-slate-500">Size: </span>
                  <span className="text-slate-200">
                    {resultQuery.data.raw_html_size
                      ? `${(resultQuery.data.raw_html_size / 1024).toFixed(1)} KB`
                      : 'n/a'}
                  </span>
                </div>
              </div>
              {resultQuery.data.raw_html_path && (
                <a
                  className="mt-2 inline-flex items-center rounded-md border border-emerald-300/50 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-100 hover:border-emerald-200 hover:bg-emerald-500/20"
                  href={`${apiBase}/api/v1/jobs/${selectedJobId}/results/raw`}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download raw HTML
                </a>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === 'succeeded' || status === 'success'
      ? 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40'
      : status === 'running' || status === 'pending'
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
