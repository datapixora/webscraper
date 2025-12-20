"use client";

import { useEffect, useMemo, useState } from "react";
import {
  motor3dCreateJobs,
  motor3dDiscover,
  motor3dListProducts,
  motor3dParse,
  getProjects,
  createProject,
  Project,
  listDomainPolicies,
  Motor3DProduct,
  motor3dRunAll,
  stopProject,
} from "@/lib/api-client";

export default function Motor3DPage() {
  const [sitemapUrl, setSitemapUrl] = useState("https://motor3dmodel.ir/wp-sitemap.xml");
  const [urlPrefix, setUrlPrefix] = useState("https://motor3dmodel.ir/product/");
  const [urls, setUrls] = useState<string[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(() => new Set());
  const [sampleUrls, setSampleUrls] = useState<string[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const [creating, setCreating] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [lastRun, setLastRun] = useState<Date | null>(null);
  const [foundCount, setFoundCount] = useState<number>(0);
  const [parseUrl, setParseUrl] = useState("");
  const [parseResult, setParseResult] = useState<any>(null);
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [policy, setPolicy] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProjects = async () => {
      try {
        const data = await getProjects();
        setProjects(data);
        const defaultProj =
          data.find((p) => p.name?.toLowerCase().includes("motor3d")) ||
          data.find((p) => (p.allowed_domains || []).includes("motor3dmodel.ir")) ||
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
      const p = policies.find((p) => p.domain === "motor3dmodel.ir");
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
      const res = await motor3dDiscover({ sitemap_url: sitemapUrl, url_prefix: urlPrefix });
      setUrls(res.urls || []);
      setSelectedUrls(new Set());
      setSampleUrls(res.sample_urls || res.urls || []);
      setFoundCount(res.count);
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
      setError("No URLs to create jobs");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      console.debug("motor3d create jobs", { selectedUrls: toCreate, projectId });
      const res = await motor3dCreateJobs({ project_id: projectId, urls: toCreate });
      setError(`Created ${res.created}, Rejected ${res.rejected.length}`);
    } catch (e: any) {
      setError(e?.message || "Create jobs failed");
    } finally {
      setCreating(false);
    }
  };

  const handleParse = async () => {
    setParsing(true);
    setError(null);
    try {
      const target = parseUrl || Array.from(selectedUrls)[0] || urls[0];
      if (!target) {
        setError("Pick a URL to parse");
        setParsing(false);
        return;
      }
      const res = await motor3dParse({ url: target, project_id: projectId });
      setParseResult(res);
    } catch (e: any) {
      setError(e?.message || "Parse failed");
    } finally {
      setParsing(false);
    }
  };

  const loadProducts = async () => {
    try {
      const res = await motor3dListProducts();
      setProducts(res);
    } catch (e: any) {
      setError(e?.message || "Load products failed");
    }
  };

  const handleCreateProject = async () => {
    setError(null);
    try {
      const proj = await createProject({ name: "motor3d", description: "Motor3D products" });
      setProjects((prev) => [proj, ...prev]);
      setProjectId(proj.id);
    } catch (e: any) {
      setError(e?.message || "Create project failed (maybe already exists)");
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
        <h1 className="text-2xl font-semibold text-white">Motor3D Products</h1>
        <p className="text-sm text-slate-300">
          Discover product URLs, create scrape jobs, parse sample pages, and export CSV.
        </p>
      </div>
      {policy && (
        <section className="rounded-lg border border-emerald-300/30 bg-emerald-500/10 p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Policy: motor3dmodel.ir</h2>
            <div className="flex gap-2">
              <button
                onClick={loadPolicy}
                className="rounded-md border border-white/20 bg-white/5 px-3 py-1 text-xs text-slate-100 hover:border-emerald-300/60"
              >
                Reload policy
              </button>
              <a
                className="rounded-md border border-emerald-300/50 bg-emerald-500/20 px-3 py-1 text-xs text-emerald-100 hover:border-emerald-200"
                href="/admin/policies?domain=motor3dmodel.ir"
              >
                Edit Policies
              </a>
            </div>
          </div>
          <p className="text-sm text-slate-200">
            method: {policy.method} | proxy: {policy.use_proxy ? "on" : "off"} | delay: {policy.request_delay_ms} ms |
            concurrency: {policy.max_concurrency} | UA: {policy.user_agent || "default"}
          </p>
        </section>
      )}

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">1) Discover product URLs</h2>
        <div className="grid gap-2 md:grid-cols-2">
            <input
              className="rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={sitemapUrl}
              onChange={(e) => setSitemapUrl(e.target.value)}
            />
            <input
              className="rounded-md border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white"
              value={urlPrefix}
              onChange={(e) => setUrlPrefix(e.target.value)}
            />
          </div>
        <button
          onClick={handleDiscover}
          disabled={discovering}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {discovering ? "Discovering..." : "Discover"}
        </button>
        <p className="text-sm text-slate-300">Found: {urls.length}</p>
        {lastRun && (
          <p className="text-xs text-slate-400">
            Last run: {lastRun.toLocaleString()} | Total reported: {foundCount}
          </p>
        )}
        {sampleUrls.length > 0 && (
          <div className="max-h-60 overflow-auto rounded-md border border-white/10 bg-slate-900/80 p-2 text-xs text-slate-200 space-y-1">
            <label className="flex items-center gap-2 text-xs text-emerald-200">
              <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} /> Select all ({selectedUrls.size})
            </label>
            {urls.map((u) => (
              <label key={u} className="flex items-center gap-2">
                <input type="checkbox" checked={selectedUrls.has(u)} onChange={() => toggleSelect(u)} />
                <span className="break-all">{u}</span>
              </label>
            ))}
            {urls.length > 50 && <div>... (+{urls.length - 50} more)</div>}
          </div>
        )}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">2) Create jobs</h2>
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
            Create motor3d project
          </button>
        </div>
        {!projectId && <p className="text-xs text-amber-300">Select or create a project to enable actions.</p>}
        <button
          onClick={handleCreateJobs}
          disabled={creating || selectedUrls.size === 0 || !projectId}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {creating ? "Creating..." : "Create jobs for selected URLs"}
        </button>
        {selectedUrls.size === 0 && <p className="text-xs text-amber-300">Select at least one URL first.</p>}
        <button
          onClick={async () => {
            if (!projectId) {
              setError("Select a project first");
              return;
            }
            try {
              const res = await stopProject(projectId);
              setError(`Stop requested. Cancelled: ${res.cancelled}, revoked: ${res.revoked}`);
            } catch (e: any) {
              setError(e?.message || "Stop failed");
            }
          }}
          disabled={!projectId}
          className="rounded-md border border-white/20 bg-white/5 px-3 py-2 text-sm font-semibold text-white hover:border-emerald-300/60 disabled:opacity-60"
        >
          Stop all jobs for this project
        </button>
      </section>
      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <h2 className="text-lg font-semibold text-white">3) Run all (discover + create jobs + scrape)</h2>
        <button
          onClick={async () => {
            if (!projectId) {
              setError("Select a project first");
              return;
            }
            setParsing(true);
            setError(null);
            try {
              const res = await motor3dRunAll({ project_id: projectId, max_urls: 2000 });
              setFoundCount(res.count);
              setSampleUrls(res.sample_urls || []);
              setUrls(res.sample_urls || []);
              setParseResult(res);
            } catch (e: any) {
              setError(e?.message || "Run all failed");
            } finally {
              setParsing(false);
            }
          }}
          disabled={parsing}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-500 disabled:opacity-60"
        >
          {parsing ? "Running..." : "Run all (discover + create jobs + scrape)"}
        </button>
        {parseResult && (
          <pre className="max-h-64 overflow-auto rounded-md border border-white/10 bg-slate-900/80 p-3 text-xs text-slate-200">
            {JSON.stringify(parseResult, null, 2)}
          </pre>
        )}
      </section>

      <section className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-white">Parsed products (latest)</h2>
          <div className="flex gap-2">
            <button
              onClick={loadProducts}
              className="rounded-md border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-100 hover:border-emerald-300/60"
            >
              Refresh
            </button>
            <button
              onClick={() =>
                window.open(
                  `/api/v1/admin/connectors/motor3d/export-csv${projectId ? `?project_id=${projectId}` : ""}`,
                  "_blank",
                )
              }
              className="rounded-md border border-emerald-300/50 bg-emerald-500/20 px-3 py-1 text-sm text-emerald-100 hover:border-emerald-200"
            >
              Export CSV
            </button>
          </div>
        </div>
        {products.length === 0 && <p className="text-sm text-slate-300">None yet.</p>}
        {products.length > 0 && (
          <div className="overflow-auto rounded-md border border-white/10 bg-slate-900/80">
            <table className="min-w-full text-sm">
              <thead className="bg-white/10 text-slate-200">
                <tr>
                  <th className="px-2 py-1 text-left">Title</th>
                  <th className="px-2 py-1 text-left">Price</th>
                  <th className="px-2 py-1 text-left">URL</th>
                  <th className="px-2 py-1 text-left">Specs</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.url} className="border-t border-white/5">
                    <td className="px-2 py-1 text-white">{p.title}</td>
                    <td className="px-2 py-1 text-slate-200">{p.price_text}</td>
                    <td className="px-2 py-1 text-emerald-200 break-all">{p.url}</td>
                    <td className="px-2 py-1 text-slate-200">{(p.specs || []).join(" | ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {error && <p className="text-sm text-amber-300">{error}</p>}
    </div>
  );
}
