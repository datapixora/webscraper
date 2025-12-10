'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useCampaigns } from '@/hooks/useCampaigns';

export default function CampaignsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start">
        <div className="flex-1 rounded-xl border border-white/5 bg-white/5 p-5">
          <h2 className="text-lg font-semibold text-white">Topic Campaigns</h2>
          <p className="text-sm text-slate-300">Auto-crawl pages for a topic.</p>
          <CampaignsList />
        </div>
        <div className="w-full md:w-96 rounded-xl border border-white/5 bg-white/5 p-5">
          <h3 className="text-md font-semibold text-white">New Campaign</h3>
          <CampaignForm />
        </div>
      </div>
    </div>
  );
}

function CampaignsList() {
  const { campaignsQuery } = useCampaigns();
  if (campaignsQuery.isLoading) {
    return <p className="mt-3 text-sm text-slate-300">Loading campaigns...</p>;
  }
  if (campaignsQuery.isError) {
    return (
      <p className="mt-3 text-sm text-amber-300">
        Failed to load campaigns: {(campaignsQuery.error as Error).message}
      </p>
    );
  }
  const campaigns = campaignsQuery.data ?? [];
  return (
    <div className="mt-4 overflow-x-auto">
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
          {campaigns.map((c) => (
            <tr key={c.id} className="hover:bg-white/5">
              <td className="px-3 py-2 font-semibold text-white">
                <Link className="hover:underline" href={`/campaigns/${c.id}`}>
                  {c.name}
                </Link>
                <div className="text-xs text-slate-400">{c.query}</div>
              </td>
              <td className="px-3 py-2">
                <StatusPill status={c.status} />
              </td>
              <td className="px-3 py-2">{c.pages_collected}</td>
              <td className="px-3 py-2 text-slate-300">{c.max_pages}</td>
              <td className="px-3 py-2 text-slate-400">{new Date(c.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CampaignForm() {
  const { createCampaignMutation } = useCampaigns();
  const [name, setName] = useState('');
  const [query, setQuery] = useState('');
  const [seedUrlsText, setSeedUrlsText] = useState('');
  const [allowedDomainsText, setAllowedDomainsText] = useState('');
  const [maxPages, setMaxPages] = useState(50);
  const [followLinks, setFollowLinks] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const seed_urls = seedUrlsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (!seed_urls.length) {
      setError('Add at least one seed URL');
      return;
    }
    const allowed_domains = allowedDomainsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    createCampaignMutation.mutate({
      name,
      query,
      seed_urls,
      allowed_domains: allowed_domains.length ? allowed_domains : undefined,
      max_pages: maxPages,
      follow_links: followLinks,
    });
    setName('');
    setQuery('');
    setSeedUrlsText('');
    setAllowedDomainsText('');
    setMaxPages(50);
    setFollowLinks(true);
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
          placeholder="Campaign name"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Query / Topic</label>
        <input
          required
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          placeholder="e.g. EV motors"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Seed URLs (one per line)</label>
        <textarea
          required
          rows={4}
          value={seedUrlsText}
          onChange={(e) => setSeedUrlsText(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
        />
      </div>
      <div className="space-y-1">
        <label className="text-sm text-slate-200">Allowed domains (optional, one per line)</label>
        <textarea
          rows={2}
          value={allowedDomainsText}
          onChange={(e) => setAllowedDomainsText(e.target.value)}
          className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          placeholder="example.com"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1">
          <label className="text-sm text-slate-200">Max pages</label>
          <input
            type="number"
            min={1}
            max={5000}
            value={maxPages}
            onChange={(e) => setMaxPages(Number(e.target.value))}
            className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus:border-emerald-400 focus:outline-none"
          />
        </div>
        <label className="mt-6 flex items-center gap-2 text-sm text-slate-200">
          <input
            type="checkbox"
            checked={followLinks}
            onChange={(e) => setFollowLinks(e.target.checked)}
            className="h-4 w-4"
          />
          Follow links
        </label>
      </div>
      <button
        type="submit"
        className="w-full rounded-lg border border-emerald-400/50 bg-emerald-500/20 px-3 py-2 text-sm font-semibold text-emerald-50 hover:border-emerald-300 hover:bg-emerald-500/30"
        disabled={createCampaignMutation.isPending}
      >
        {createCampaignMutation.isPending ? 'Creating...' : 'Create Campaign'}
      </button>
      {error && <p className="text-xs text-amber-300">{error}</p>}
      {createCampaignMutation.isError && (
        <p className="text-xs text-amber-300">{(createCampaignMutation.error as Error).message}</p>
      )}
    </form>
  );
}

function StatusPill({ status }: { status: string }) {
  const color =
    status === 'active'
      ? 'bg-emerald-500/20 text-emerald-100 border-emerald-300/40'
      : status === 'paused'
        ? 'bg-amber-500/20 text-amber-100 border-amber-300/50'
        : status === 'failed'
          ? 'bg-red-500/20 text-red-100 border-red-300/50'
          : 'bg-cyan-500/20 text-cyan-100 border-cyan-300/40';
  return (
    <span
      className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold capitalize ${color}`}
    >
      {status}
    </span>
  );
}
