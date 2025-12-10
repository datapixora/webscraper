'use client';

import { useMemo, useState } from 'react';
import { useProjects } from '@/hooks/useProjects';
import { useJobs } from '@/hooks/useJobs';
import { JsonViewer } from '@/components/json-viewer';

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start">
        <div className="flex-1 rounded-xl border border-white/5 bg-white/5 p-5">
          <h2 className="text-lg font-semibold text-white">Projects</h2>
          <p className="text-sm text-slate-300">List and create scraping projects.</p>
          <ProjectsList />
        </div>
        <div className="w-full md:w-96 rounded-xl border border-white/5 bg-white/5 p-5">
          <h3 className="text-md font-semibold text-white">Create Project</h3>
          <ProjectForm />
        </div>
      </div>
      <ProjectJobs />
    </div>
  );
}

function ProjectsList() {
  const { projectsQuery } = useProjects();
  if (projectsQuery.isLoading) {
    return <p className="mt-3 text-sm text-slate-300">Loading projects...</p>;
  }
  if (projectsQuery.isError) {
    return (
      <p className="mt-3 text-sm text-amber-300">
        Failed to load projects: {(projectsQuery.error as Error).message}
      </p>
    );
  }
  return (
    <ul className="mt-4 divide-y divide-white/5">
      {projectsQuery.data?.map((proj) => (
        <li key={proj.id} className="py-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-base font-semibold text-white">{proj.name}</p>
              <p className="text-sm text-slate-300">{proj.description}</p>
            </div>
            <span className="text-xs text-slate-400">
              updated {new Date(proj.updated_at).toLocaleString()}
            </span>
          </div>
          {proj.extraction_schema ? (
            <div className="mt-2 text-xs text-emerald-200">Schema attached</div>
          ) : (
            <div className="mt-2 text-xs text-slate-400">No schema</div>
          )}
        </li>
      ))}
    </ul>
  );
}

function ProjectForm() {
  const { createProjectMutation } = useProjects();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const presets = [
    {
      label: 'Empty schema',
      value: '{"fields": []}',
    },
    {
      label: 'Page title',
      value:
        '{"fields":[{"name":"title","selector":"title::text","type":"css","attr":"text"}]}',
    },
    {
      label: 'Links (hrefs)',
      value:
        '{"fields":[{"name":"links","selector":"a","type":"css","attr":"href","all":true}]}',
    },
    {
      label: 'Article headlines (h2)',
      value:
        '{"fields":[{"name":"headlines","selector":"h2::text","type":"css","attr":"text","all":true}]}',
    },
  ];
  const [schemaText, setSchemaText] = useState(presets[0].value);
  const [selectedPreset, setSelectedPreset] = useState(presets[0].value);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    let parsed: object | null = null;
    try {
      parsed = schemaText ? JSON.parse(schemaText) : null;
    } catch (err) {
      setError('Extraction schema must be valid JSON');
      return;
    }
    createProjectMutation.mutate({ name, description, extraction_schema: parsed });
    setName('');
    setDescription('');
    setSchemaText('{"fields": []}');
  };

  return (
    <form className="mt-3 space-y-3" onSubmit={onSubmit}>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Name</label>
        <input
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          placeholder="Project name"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Description</label>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          placeholder="Optional description"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Extraction Schema (JSON)</label>
        <select
          value={selectedPreset}
          onChange={(e) => {
            setSelectedPreset(e.target.value);
            setSchemaText(e.target.value);
          }}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        >
          {presets.map((p) => (
            <option key={p.label} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
        <textarea
          value={schemaText}
          onChange={(e) => setSchemaText(e.target.value)}
          rows={6}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        />
        {error && <p className="text-xs text-amber-300">{error}</p>}
      </div>
      <button
        type="submit"
        className="w-full rounded-lg border border-emerald-400/50 bg-emerald-500/20 px-3 py-2 text-sm font-semibold text-emerald-50 hover:border-emerald-300 hover:bg-emerald-500/30"
        disabled={createProjectMutation.isPending}
      >
        {createProjectMutation.isPending ? 'Creating...' : 'Create Project'}
      </button>
      {createProjectMutation.isError && (
        <p className="text-xs text-amber-300">
          {(createProjectMutation.error as Error).message}
        </p>
      )}
    </form>
  );
}

function ProjectJobs() {
  const { projectsQuery } = useProjects();
  const { jobsQuery, createJobMutation } = useJobs();
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [jobName, setJobName] = useState('');
  const [targetUrl, setTargetUrl] = useState('');

  const filteredJobs = useMemo(() => {
    if (!selectedProject) return jobsQuery.data ?? [];
    return (jobsQuery.data ?? []).filter((job) => job.project_id === selectedProject);
  }, [jobsQuery.data, selectedProject]);

  const onCreateJob = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProject) return;
    createJobMutation.mutate({
      project_id: selectedProject,
      name: jobName,
      target_url: targetUrl,
    });
    setJobName('');
    setTargetUrl('');
  };

  return (
    <div className="rounded-xl border border-white/5 bg-white/5 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-white">Jobs per project</h3>
          <p className="text-sm text-slate-300">
            Select a project to view and create jobs for it.
          </p>
        </div>
        <select
          className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          value={selectedProject ?? ''}
          onChange={(e) => setSelectedProject(e.target.value || null)}
        >
          <option value="">All projects</option>
          {projectsQuery.data?.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <form className="mt-4 grid gap-3 md:grid-cols-3" onSubmit={onCreateJob}>
        <input
          required
          value={jobName}
          onChange={(e) => setJobName(e.target.value)}
          placeholder="Job name"
          className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        />
        <input
          required
          value={targetUrl}
          onChange={(e) => setTargetUrl(e.target.value)}
          placeholder="Target URL"
          className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-lg border border-emerald-400/50 bg-emerald-500/20 px-3 py-2 text-sm font-semibold text-emerald-50 hover:border-emerald-300 hover:bg-emerald-500/30"
          disabled={createJobMutation.isPending || !selectedProject}
        >
          {createJobMutation.isPending ? 'Creating...' : 'Create Job'}
        </button>
      </form>

      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-white/5 text-sm">
          <thead className="bg-white/5 text-left text-slate-200">
            <tr>
              <th className="px-3 py-2">Job</th>
              <th className="px-3 py-2">Project</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Target</th>
              <th className="px-3 py-2">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 text-slate-100">
            {filteredJobs.map((job) => (
              <tr key={job.id} className="hover:bg-white/5">
                <td className="px-3 py-2 font-semibold text-white">{job.name}</td>
                <td className="px-3 py-2 text-slate-300">
                  {projectsQuery.data?.find((p) => p.id === job.project_id)?.name ?? job.project_id}
                </td>
                <td className="px-3 py-2">
                  <StatusPill status={job.status} />
                </td>
                <td className="px-3 py-2 text-emerald-200">{job.target_url}</td>
                <td className="px-3 py-2 text-slate-400">
                  {new Date(job.updated_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
