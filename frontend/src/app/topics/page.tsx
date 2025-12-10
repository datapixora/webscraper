'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useTopics } from '@/hooks/useTopics';

export default function TopicsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start">
        <div className="flex-1 rounded-xl border border-white/5 bg-white/5 p-5">
          <h2 className="text-lg font-semibold text-white">Topics</h2>
          <p className="text-sm text-slate-300">Search the web for a topic, collect URLs, and pick which to scrape.</p>
          <TopicsList />
        </div>
        <div className="w-full md:w-96 rounded-xl border border-white/5 bg-white/5 p-5">
          <h3 className="text-md font-semibold text-white">New Topic</h3>
          <TopicForm />
        </div>
      </div>
    </div>
  );
}

function TopicsList() {
  const { topicsQuery } = useTopics();
  if (topicsQuery.isLoading) return <p className="mt-3 text-sm text-slate-300">Loading topics...</p>;
  if (topicsQuery.isError)
    return (
      <p className="mt-3 text-sm text-amber-300">
        Failed to load topics: {(topicsQuery.error as Error).message}
      </p>
    );
  const topics = topicsQuery.data ?? [];
  return (
    <div className="mt-4 overflow-x-auto">
      <table className="min-w-full divide-y divide-white/5 text-sm">
        <thead className="bg-white/5 text-left text-slate-200">
          <tr>
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Query</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Max results</th>
            <th className="px-3 py-2">Created</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5 text-slate-100">
          {topics.map((t) => (
            <tr key={t.id} className="hover:bg-white/5">
              <td className="px-3 py-2 font-semibold text-white">
                <Link href={`/topics/${t.id}`} className="hover:underline">
                  {t.name}
                </Link>
              </td>
              <td className="px-3 py-2 max-w-xs truncate text-slate-300">{t.query}</td>
              <td className="px-3 py-2">
                <StatusPill status={t.status} />
              </td>
              <td className="px-3 py-2 text-slate-200">{t.max_results}</td>
              <td className="px-3 py-2 text-slate-400">{new Date(t.created_at).toLocaleString()}</td>
              <td className="px-3 py-2">
                <Link
                  href={`/topics/${t.id}`}
                  className="rounded-md border border-white/10 bg-white/5 px-2 py-1 text-xs text-emerald-200 hover:border-emerald-300/50 hover:text-emerald-100"
                >
                  View URLs
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TopicForm() {
  const { createTopicMutation } = useTopics();
  const [name, setName] = useState('');
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(20);
  const [searchEngine, setSearchEngine] = useState<'duckduckgo' | 'mock'>('duckduckgo');
  const [error, setError] = useState<string | null>(null);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!name || !query) {
      setError('Name and query are required');
      return;
    }
    createTopicMutation.mutate({ name, query, max_results: maxResults, search_engine: searchEngine });
    setName('');
    setQuery('');
    setMaxResults(20);
    setSearchEngine('duckduckgo');
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
          placeholder="Topic name"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Query / Keyword</label>
        <input
          required
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          placeholder="e.g. electric motors"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Max results</label>
        <input
          type="number"
          min={1}
          max={100}
          value={maxResults}
          onChange={(e) => setMaxResults(Number(e.target.value))}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Search engine</label>
        <select
          value={searchEngine}
          onChange={(e) => setSearchEngine(e.target.value as 'duckduckgo' | 'mock')}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        >
          <option value="duckduckgo">DuckDuckGo (live)</option>
          <option value="mock">Mock (sample URLs)</option>
        </select>
      </div>
      <button
        type="submit"
        className="w-full rounded-lg border border-emerald-400/50 bg-emerald-500/20 px-3 py-2 text-sm font-semibold text-emerald-50 hover:border-emerald-300 hover:bg-emerald-500/30"
        disabled={createTopicMutation.isPending}
      >
        {createTopicMutation.isPending ? 'Creating...' : 'Create Topic'}
      </button>
      {error && <p className="text-xs text-amber-300">{error}</p>}
      {createTopicMutation.isError && (
        <p className="text-xs text-amber-300">{(createTopicMutation.error as Error).message}</p>
      )}
    </form>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === 'completed'
      ? 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40'
      : status === 'searching'
        ? 'bg-cyan-500/20 text-cyan-100 border-cyan-300/40'
        : status === 'failed'
          ? 'bg-red-500/20 text-red-100 border-red-300/50'
          : 'bg-slate-500/20 text-slate-100 border-slate-300/50';
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold capitalize ${color}`}
    >
      {status}
    </span>
  );
}
