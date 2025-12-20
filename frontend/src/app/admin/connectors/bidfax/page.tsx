"use client";

import { useEffect, useMemo, useState } from "react";
import {
  bidfaxCreateJobs,
  bidfaxDiscover,
  bidfaxListVehicles,
  bidfaxParse,
  bidfaxRunAll,
  bidfaxExportCsvUrl,
  getProjects,
  createProject,
  Project,
  listDomainPolicies,
  stopProject,
} from "@/lib/api-client";

export default function BidFaxPage() {
  const [baseUrl, setBaseUrl] = useState("https://en.bidfax.info/nissan/");
  const [maxUrls, setMaxUrls] = useState(10);
  const [urls, setUrls] = useState<string[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(() => new Set());
  const [sampleUrls, setSampleUrls] = useState<string[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [creating, setCreating] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [lastRun, setLastRun] = useState<Date | null>(null);
  const [foundCount, setFoundCount] = useState<number>(0);
  const [pagesScraped, setPagesScraped] = useState<number>(0);
  const [parseResult, setParseResult] = useState<any>(null);
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [vehicles, setVehicles] = useState<any[]>([]);
  const [policy, setPolicy] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await getProjects();
        setProjects(data);
        const defaultProj =
          data.find((p) => p.name?.toLowerCase().includes("bidfax")) ||
          data.find((p) => (p.allowed_domains || []).includes("bidfax.info")) ||
          data[0];
        if (defaultProj) setProjectId(defaultProj.id);
      } catch (e: any) {
        setError(e?.message || "Failed to load projects");
      }
    };
    loadProjects();
  }, []);

  const loadPolicy = async () => {
    try {
      const policies = await listDomainPolicies();
      const p = policies.find((p) => p.domain === "bidfax.info" || p.domain === "en.bidfax.info");
      setPolicy(p || null);
    } catch (e: any) {
      setError(e?.message || "Failed to load policy");
    }
  };

  useEffect(() => {
    loadPolicy();
  }, []);

  const handleDiscover = async () => {
    setDiscovering(true);
    setError(null);
    try {
      const res = await bidfaxDiscover({ base_url: baseUrl, max_urls: maxUrls });
      setUrls(res.urls || []);
      setSelectedUrls(new Set());
      setSampleUrls(res.sample_urls || res.urls || []);
      setFoundCount(res.count);
      setPagesScraped(res.pages_scraped);
      setLastRun(new Date());
    } catch (e: any) {
      setError(e?.message || "Discover failed");
    } finally {
      setDiscovering(false);
    }
  };

  const handleCreateJobs = async () => {
    if (!projectId) {
      setError("Select a project first");
      return;
    }
    const toCreate = Array.from(selectedUrls);
    if (toCreate.length === 0) {
      setError("No URLs selected");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const res = await bidfaxCreateJobs({ project_id: projectId, urls: toCreate });
      setError(`Created ${res.created} jobs, Rejected ${res.rejected.length}`);
    } catch (e: any) {
      setError(e?.message || "Create jobs failed");
    } finally {
      setCreating(false);
    }
  };

  const handleParse = async (url?: string) => {
    setParsing(true);
    setError(null);
    try {
      const target = url || Array.from(selectedUrls)[0] || urls[0];
      if (!target) {
        setError("Pick a URL to parse");
        setParsing(false);
        return;
      }
      const res = await bidfaxParse({ url: target });
      setParseResult(res);
    } catch (e: any) {
      setError(e?.message || "Parse failed");
    } finally {
      setParsing(false);
    }
  };

  const loadVehicles = async () => {
    try {
      const res = await bidfaxListVehicles(projectId);
      setVehicles(res);
    } catch (e: any) {
      setError(e?.message || "Load vehicles failed");
    }
  };

  const handleCreateProject = async () => {
    setError(null);
    try {
      const proj = await createProject({
        name: "bidfax",
        description: "BidFax auction vehicles",
        allowed_domains: ["bidfax.info", "en.bidfax.info"],
      });
      setProjects((prev) => [proj, ...prev]);
      setProjectId(proj.id);
    } catch (e: any) {
      setError(e?.message || "Create project failed");
    }
  };

  const toggleSelect = (url: string) => {
    setSelectedUrls((prev) => {
      const next = new Set(prev);
      if (next.has(url)) {
        next.delete(url);
      } else {
        next.add(url);
      }
      return next;
    });
  };

  const allSelected = useMemo(() => urls.length > 0 && selectedUrls.size === urls.length, [urls, selectedUrls]);

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedUrls(new Set());
    } else {
      setSelectedUrls(new Set(urls));
    }
  };

  return (
    <div className="space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-white">BidFax Vehicles</h1>
        <p className="text-sm text-slate-300">
          Discover auction vehicle URLs, create scrape jobs, parse sample pages, and export CSV.
        </p>
      </div>

      {policy && (
        <section className="rounded-lg border border-emerald-300/30 bg-emerald-500/10 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Policy: bidfax.info</h2>
            <div className="flex gap-2">
              <button
                onClick={loadPolicy}
                className="rounded-md border border-white/20 bg-white/5 px-3 py-1 text-xs text-slate-100 hover:border-emerald-300/60"
              >
                Reload policy
              </button>
              <a
                className="rounded-md border border-emerald-300/50 bg-emerald-500/20 px-3 py-1 text-xs text-emerald-100 hover:border-emerald-200"
                href="/admin/policies?domain=bidfax.info"
              >
                Edit Policies
              </a>
            </div>
          </div>
          <p className="text-sm text-slate-200">
            method: {policy.method} · proxy: {policy.use_proxy ? "on" : "off"} · delay: {policy.request_delay_ms} ms ·
            concurrency: {policy.max_concurrency} · UA: {policy.user_agent || "default"}
          </p>
        </section>
      )}

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">1) Discover Vehicle URLs</h2>
        <div className="space-y-2">
          <label className="text-sm text-slate-200">Base URL (category page)</label>
          <input
            className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://en.bidfax.info/nissan/"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm text-slate-200">Max URLs to discover (10 per page)</label>
          <input
            type="number"
            className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={maxUrls}
            onChange={(e) => setMaxUrls(parseInt(e.target.value) || 10)}
            min={1}
            max={1000}
          />
          <p className="text-xs text-slate-400">
            BidFax shows 10 listings per page. Enter 50 to scrape 5 pages.
          </p>
        </div>
        <button
          onClick={handleDiscover}
          disabled={discovering}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {discovering ? "Discovering..." : "Discover"}
        </button>
        <p className="text-sm text-slate-300">
          Found: {urls.length} URLs across {pagesScraped} pages
        </p>
        {lastRun && (
          <p className="text-xs text-slate-400">
            Last run: {lastRun.toLocaleString()} · Total reported: {foundCount}
          </p>
        )}
        {urls.length > 0 && (
          <div className="max-h-80 overflow-auto rounded-md border border-white/10 bg-slate-900/80 p-2 text-xs text-slate-200 space-y-1">
            <label className="flex items-center gap-2 text-xs text-emerald-200">
              <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} /> Select all ({selectedUrls.size})
            </label>
            {urls.slice(0, 100).map((u) => (
              <label key={u} className="flex items-center gap-2">
                <input type="checkbox" checked={selectedUrls.has(u)} onChange={() => toggleSelect(u)} />
                <span className="break-all">{u}</span>
              </label>
            ))}
            {urls.length > 100 && <div>... (+{urls.length - 100} more)</div>}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">2) Create Scrape Jobs</h2>
        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-200">Project</label>
          <select
            className="w-full rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
          >
            <option value="">Select project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="w-fit rounded-md border border-white/10 bg-white/5 px-3 py-1 text-sm text-emerald-100 hover:border-emerald-300/60"
            onClick={handleCreateProject}
          >
            Create bidfax project
          </button>
        </div>
        <button
          onClick={handleCreateJobs}
          disabled={creating || selectedUrls.size === 0 || !projectId}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {creating ? "Creating..." : `Create jobs for ${selectedUrls.size} selected URLs`}
        </button>
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">3) Test Parse (Preview)</h2>
        <p className="text-sm text-slate-400">Parse a single vehicle to preview data extraction (no job created)</p>
        <button
          onClick={() => handleParse()}
          disabled={parsing || urls.length === 0}
          className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
        >
          {parsing ? "Parsing..." : "Parse first selected URL"}
        </button>
        {parseResult && (
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-white">Parsed Vehicle Data:</h3>
            <div className="max-h-96 overflow-auto rounded-md border border-white/10 bg-slate-900/80 p-3 text-xs">
              <table className="min-w-full text-slate-200">
                <tbody>
                  {Object.entries(parseResult).map(([key, value]) => (
                    <tr key={key} className="border-b border-white/5">
                      <td className="py-1 pr-4 font-semibold text-emerald-300">{key}:</td>
                      <td className="py-1">{String(value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-white">Scraped Vehicles (from completed jobs)</h2>
          <div className="flex gap-2">
            <button
              onClick={loadVehicles}
              className="rounded-md border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-100 hover:border-emerald-300/60"
            >
              Refresh
            </button>
            <button
              onClick={() => window.open(bidfaxExportCsvUrl(projectId), "_blank")}
              className="rounded-md border border-emerald-300/50 bg-emerald-500/20 px-3 py-1 text-sm text-emerald-100 hover:border-emerald-200"
            >
              Export CSV
            </button>
          </div>
        </div>
        {vehicles.length === 0 && <p className="text-sm text-slate-300">No vehicles yet. Create and run jobs first.</p>}
        {vehicles.length > 0 && (
          <div className="overflow-auto rounded-md border border-white/10 bg-slate-900/80">
            <table className="min-w-full text-sm">
              <thead className="bg-white/10 text-slate-200">
                <tr>
                  <th className="px-2 py-1 text-left">Title</th>
                  <th className="px-2 py-1 text-left">Price</th>
                  <th className="px-2 py-1 text-left">VIN</th>
                  <th className="px-2 py-1 text-left">Auction</th>
                  <th className="px-2 py-1 text-left">Condition</th>
                  <th className="px-2 py-1 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {vehicles.map((v, idx) => (
                  <tr key={idx} className="border-t border-white/5">
                    <td className="px-2 py-1 text-white max-w-xs truncate">{v.title}</td>
                    <td className="px-2 py-1 text-emerald-200">${v.price}</td>
                    <td className="px-2 py-1 text-slate-200 font-mono text-xs">{v.vin}</td>
                    <td className="px-2 py-1 text-slate-200">{v.auction}</td>
                    <td className="px-2 py-1 text-slate-200">{v.condition}</td>
                    <td className="px-2 py-1 text-amber-200">{v.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {error && (
        <div className="rounded-lg bg-amber-500/10 border border-amber-500/20 px-4 py-3">
          <p className="text-sm text-amber-300">{error}</p>
        </div>
      )}
    </div>
  );
}
