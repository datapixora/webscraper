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
  const [showNewJob, setShowNewJob] = useState(false);

  const jobs = useMemo(() => jobsQuery.data ?? [], [jobsQuery.data]);
  const selectedJob = useMemo(
    () => jobs.find((j) => j.id === selectedJobId),
    [jobs, selectedJobId],
  );
  const grouped = useMemo(() => {
    const map = new Map<string, { projectName: string; jobs: typeof jobs }>();
    jobs.forEach((j) => {
      const name = projectsQuery.data?.find((p) => p.id === j.project_id)?.name ?? j.project_id;
      const bucket = map.get(j.project_id);
      if (!bucket) {
        map.set(j.project_id, { projectName: name, jobs: [j] });
      } else {
        bucket.jobs.push(j);
      }
    });
    return Array.from(map.entries()).map(([project_id, value]) => ({ project_id, ...value }));
  }, [jobs, projectsQuery.data]);

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Jobs</h2>
            <p className="text-sm text-slate-300">Grouped by project. Click a job to view details.</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="rounded-md border border-emerald-300/50 bg-emerald-500/20 px-3 py-2 text-sm font-semibold text-emerald-100 hover:border-emerald-200 hover:bg-emerald-500/30"
              onClick={() => setShowNewJob(true)}
            >
              + New Job
            </button>
            {jobsQuery.isFetching && <span className="text-xs text-slate-300">Refreshing...</span>}
          </div>
        </div>

        {grouped.map((grp) => {
          const total = grp.jobs.length;
          const succeeded = grp.jobs.filter((j) => j.status.toLowerCase().includes('succeed')).length;
          const failed = grp.jobs.filter((j) => j.status.toLowerCase().includes('fail')).length;
          const running = grp.jobs.filter((j) => j.status.toLowerCase().includes('run')).length;
          const pending = total - succeeded - failed - running;
          const percent = total ? Math.round((succeeded / total) * 100) : 0;
          return (
            <div key={grp.project_id} className="rounded-xl border border-white/5 bg-white/5 p-4">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-emerald-200/80">Project</p>
                  <h3 className="text-lg font-semibold text-white">{grp.projectName}</h3>
                  <p className="text-xs text-slate-300">
                    {total} jobs • {succeeded} succeeded • {running} running • {pending} pending • {failed} failed
                  </p>
                </div>
                <div className="w-40">
                  <Progress percent={percent} />
                </div>
              </div>
              <div className="mt-3 space-y-2">
                {grp.jobs.map((job) => (
                  <JobRow
                    key={job.id}
                    job={job}
                    projectName={grp.projectName}
                    selected={selectedJobId === job.id}
                    onSelect={() => setSelectedJobId(job.id)}
                  />
                ))}
              </div>
            </div>
          );
        })}

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
          <div className="space-y-2 text-sm text-slate-300">
            <p>No result stored for this job yet.</p>
            {selectedJob?.status === 'failed' && (
              <p className="text-amber-300">
                Job failed{selectedJob?.error_message ? `: ${selectedJob.error_message}` : ''}.
              </p>
            )}
            <p className="text-slate-400">
              Jobs may take time to finish. If it remains empty, check logs or retry the job.
            </p>
          </div>
        )}
        {selectedJobId && !resultQuery.isLoading && !resultQuery.data && !resultQuery.isError && (
          <div className="space-y-2 text-sm text-slate-300">
            <p>Job not found or no result stored (DB may have been reset).</p>
            <p className="text-slate-400">Clear local history and create a new job to continue.</p>
          </div>
        )}
        {selectedJobId && resultQuery.data && (
          <div className="mt-3 space-y-3">
            {resultQuery.data.blocked && (
              <div className="rounded-md border border-amber-400/40 bg-amber-500/10 p-3 text-sm text-amber-100">
                <p className="font-semibold">
                  Blocked {resultQuery.data.http_status ? `(${resultQuery.data.http_status})` : ''}
                </p>
                <p className="text-amber-200">
                  Reason: {resultQuery.data.block_reason || 'Access denied / anti-bot detected.'}
                </p>
                <p className="mt-2 text-amber-100/80">
                  Suggestions: rotate proxy / region, use residential IP, slow down requests, randomize headers, or
                  retry with Playwright.
                </p>
              </div>
            )}
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

      {showNewJob && (
        <NewJobModal projects={projectsQuery.data ?? []} onClose={() => setShowNewJob(false)} />
      )}
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

function Progress({ percent }: { percent: number }) {
  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-[11px] text-slate-400">
        <span>Progress</span>
        <span>{percent}%</span>
      </div>
      <div className="mt-1 h-2 rounded-full bg-slate-800">
        <div
          className="h-2 rounded-full bg-emerald-400"
          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
        />
      </div>
    </div>
  );
}

function JobRow({
  job,
  projectName,
  selected,
  onSelect,
}: {
  job: any;
  projectName: string;
  selected: boolean;
  onSelect: () => void;
}) {
  const { deleteJobMutation } = useJobs();
  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-lg border border-white/10 px-3 py-2 ${
        selected ? 'bg-white/10' : 'hover:bg-white/5'
      }`}
      onClick={onSelect}
    >
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-white truncate">{job.name}</p>
          <StatusPill status={job.status} />
        </div>
        <p className="text-xs text-slate-300 truncate">{job.target_url}</p>
        <p className="text-[11px] text-slate-500">
          {projectName} • {new Date(job.updated_at).toLocaleString()}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <button
          className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-emerald-100 hover:border-emerald-300/50"
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
        >
          View
        </button>
        <button
          className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-amber-200 hover:border-amber-300/50"
          onClick={(e) => {
            e.stopPropagation();
            if (confirm('Delete this job?')) deleteJobMutation.mutate(job.id);
          }}
        >
          Delete
        </button>
      </div>
    </div>
  );
}

type ProjectOption = {
  id: string;
  name: string;
};

function NewJobModal({ projects, onClose }: { projects: ProjectOption[]; onClose: () => void }) {
  const { createBatchJobsMutation } = useJobs();
  const [projectId, setProjectId] = useState('');
  const [urls, setUrls] = useState('');
  const [allowDuplicates, setAllowDuplicates] = useState(true);
  const [feedback, setFeedback] = useState<string | null>(null);

  const submit = async () => {
    setFeedback(null);
    const urlList = urls
      .split('\n')
      .map((u) => u.trim())
      .filter(Boolean);
    if (!projectId || urlList.length === 0) {
      setFeedback('Pick a project and enter at least one URL.');
      return;
    }
    const res = await createBatchJobsMutation.mutateAsync({
      project_id: projectId,
      urls: urlList,
      name_prefix: 'Manual job',
      allow_duplicates: allowDuplicates,
    });
    const rejected = res.rejected || [];
    const created = res.created || [];
    setFeedback(
      `Created ${created.length} jobs. ${rejected.length > 0 ? `Rejected ${rejected.length}: ${rejected.map((r) => r.url).join(', ')}` : ''}`,
    );
  };

  return (
    <div className="fixed inset-0 z-10 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-xl border border-white/10 bg-slate-900 p-5 shadow-xl">
        <h4 className="text-lg font-semibold text-white">New Job</h4>
        <p className="text-sm text-slate-300">Select a project and paste one or more URLs (one per line).</p>
        <div className="mt-3 space-y-3">
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Project</label>
            <select
              className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
            >
              <option value="">Choose a project</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-sm text-slate-200">Target URLs</label>
            <textarea
              rows={6}
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              className="w-full rounded-lg border border-white/10 bg-slate-800 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
              placeholder={`https://example.com/page-1\nhttps://example.com/page-2`}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-200">
            <input
              type="checkbox"
              checked={allowDuplicates}
              onChange={(e) => setAllowDuplicates(e.target.checked)}
            />
            Allow duplicates (ignore project dedup for this batch)
          </label>
        </div>
        {feedback && <p className="mt-2 text-xs text-emerald-300">{feedback}</p>}
        {createBatchJobsMutation.isError && (
          <p className="mt-2 text-xs text-amber-300">{(createBatchJobsMutation.error as Error).message}</p>
        )}
        <div className="mt-4 flex justify-end gap-2">
          <button
            className="rounded-md border border-white/10 px-3 py-2 text-sm text-slate-200 hover:border-white/30"
            onClick={onClose}
          >
            Close
          </button>
          <button
            className="rounded-md border border-emerald-300/50 bg-emerald-500/20 px-3 py-2 text-sm font-semibold text-emerald-100 hover:border-emerald-200 hover:bg-emerald-500/30 disabled:opacity-60"
            onClick={submit}
            disabled={createBatchJobsMutation.isPending}
          >
            {createBatchJobsMutation.isPending ? 'Creating...' : 'Create jobs'}
          </button>
        </div>
      </div>
    </div>
  );
}
