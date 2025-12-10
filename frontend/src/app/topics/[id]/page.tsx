'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useTopicUrls } from '@/hooks/useTopicUrls';
import { useTopics } from '@/hooks/useTopics';
import { TopicUrl, apiBase } from '@/lib/api-client';

export default function TopicDetailPage() {
  const params = useParams<{ id: string | string[] }>();
  const topicId = Array.isArray(params?.id) ? params?.id[0] : params?.id;
  const { topicQuery } = useTopics();
  const topic = topicQuery(topicId);
  const { urlsQuery, updateSelectionMutation, scrapeSelectedMutation } = useTopicUrls({ topicId });
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [downloading, setDownloading] = useState(false);

  const urls = useMemo(() => urlsQuery.data ?? [], [urlsQuery.data]);
  const allSelected = urls.length > 0 && selectedIds.size === urls.length;

  useEffect(() => {
    // initialize selected IDs from server state
    const selected = new Set<string>();
    urls.forEach((u) => u.selected_for_scraping && selected.add(u.id));
    setSelectedIds(selected);
  }, [urls]);

  const toggleSelection = (id: string) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
    updateSelectionMutation.mutate({ urlIds: [id], selected: next.has(id) });
  };

  const toggleSelectAll = (checked: boolean) => {
    const ids = urls.map((u) => u.id);
    setSelectedIds(checked ? new Set(ids) : new Set());
    if (ids.length > 0) {
      updateSelectionMutation.mutate({ urlIds: ids, selected: checked });
    }
  };

  const triggerScrape = () => {
    scrapeSelectedMutation.mutate({ project_id: undefined });
  };

  const downloadAllResults = async () => {
    if (!topicId) return;
    try {
      setDownloading(true);
      const res = await fetch(`${apiBase}/api/v1/topics/${topicId}/results/export`);
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `topic_${topicId}_results.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert((err as Error).message || 'Download failed');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs text-emerald-200/80 uppercase tracking-[0.16em]">Topic</p>
            {topic.isLoading && <p className="text-sm text-slate-300">Loading topic...</p>}
            {topic.data && (
              <>
                <h2 className="text-xl font-semibold text-white">{topic.data.name}</h2>
                <p className="text-sm text-slate-300">{topic.data.query}</p>
                <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-200">
                  <span className="rounded-lg border border-white/10 px-2 py-1">
                    Status: <StatusPill status={topic.data.status} />
                  </span>
                  <span className="rounded-lg border border-white/10 px-2 py-1">
                    Engine: {topic.data.search_engine}
                  </span>
                  <span className="rounded-lg border border-white/10 px-2 py-1">Max results: {topic.data.max_results}</span>
                </div>
              </>
            )}
            {topic.isError && <p className="text-sm text-amber-300">Failed: {(topic.error as Error).message}</p>}
          </div>
          <Link className="text-sm text-emerald-300 hover:underline" href="/topics">
            ← Back
          </Link>
        </div>
      </div>

      <div className="rounded-xl border border-white/5 bg-white/5 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-white">Discovered URLs</h3>
            <p className="text-sm text-slate-300">Select URLs to create scraping jobs.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-slate-200">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={(e) => toggleSelectAll(e.target.checked)}
              />
              Select all
            </label>
            <button
              onClick={downloadAllResults}
              className="rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm font-semibold text-slate-100 hover:border-emerald-200 hover:bg-emerald-500/10 disabled:opacity-60"
              disabled={downloading}
            >
              {downloading ? 'Downloading...' : 'Download All Results'}
            </button>
            <button
              onClick={triggerScrape}
              className="rounded-md border border-emerald-300/50 bg-emerald-500/10 px-3 py-2 text-sm font-semibold text-emerald-100 hover:border-emerald-200 hover:bg-emerald-500/20 disabled:opacity-60"
              disabled={scrapeSelectedMutation.isPending}
            >
              {scrapeSelectedMutation.isPending ? 'Triggering...' : 'Create scraping jobs for selected'}
            </button>
          </div>
        </div>
        {urlsQuery.isLoading && <p className="mt-3 text-sm text-slate-300">Loading URLs...</p>}
        {urlsQuery.isError && (
          <p className="mt-3 text-sm text-amber-300">Failed to load URLs: {(urlsQuery.error as Error).message}</p>
        )}
        {urls.length === 0 && !urlsQuery.isLoading && <p className="mt-3 text-sm text-slate-300">No URLs yet.</p>}
        {urls.length > 0 && (
          <div className="mt-3 overflow-x-auto">
            <table className="min-w-full divide-y divide-white/5 text-sm">
              <thead className="bg-white/5 text-left text-slate-200">
                <tr>
                  <th className="px-3 py-2">Pick</th>
                  <th className="px-3 py-2">Rank</th>
                  <th className="px-3 py-2">URL</th>
                  <th className="px-3 py-2">Title</th>
                  <th className="px-3 py-2">Snippet</th>
                  <th className="px-3 py-2">Scraped</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-slate-100">
                {urls.map((u) => (
                  <TopicUrlRow
                    key={u.id}
                    url={u}
                    selected={selectedIds.has(u.id)}
                    onToggle={() => toggleSelection(u.id)}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function TopicUrlRow({ url, selected, onToggle }: { url: TopicUrl; selected: boolean; onToggle: () => void }) {
  return (
    <tr className={selected ? 'bg-white/10' : 'hover:bg-white/5'}>
      <td className="px-3 py-2">
        <input type="checkbox" checked={selected} onChange={onToggle} />
      </td>
      <td className="px-3 py-2 text-slate-200">{url.rank ?? '-'}</td>
      <td className="px-3 py-2 max-w-[320px] truncate text-emerald-200">{url.url}</td>
      <td className="px-3 py-2 text-slate-300">{url.title ?? '-'}</td>
      <td className="px-3 py-2 max-w-[320px] truncate text-slate-400">{url.snippet ?? '-'}</td>
      <td className="px-3 py-2 text-slate-300">{url.scraped ? 'Yes' : 'No'}</td>
    </tr>
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
