import { z } from 'zod';

const rawApiBase =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  'http://localhost:8000';
const API_BASE = rawApiBase.replace(/\/+$/, '');
const API_PREFIX = `${API_BASE}/api/v1`;

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    const text = await res.text();
    const message = text || res.statusText;
    const error = new Error(`HTTP ${res.status}: ${message}`);
    // @ts-expect-error attach status for callers
    error.status = res.status;
    throw error;
  }
  if (res.status === 204) {
    // No content
    return undefined as T;
  }
  return (await res.json()) as T;
}

// Schemas
export const projectSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string().nullable().optional(),
  content_type: z.string().nullable().optional(),
  extraction_schema: z.record(z.any()).nullable().optional(),
  allowed_domains: z.array(z.string()).nullable().optional(),
  url_include_patterns: z.array(z.string()).nullable().optional(),
  url_exclude_patterns: z.array(z.string()).nullable().optional(),
  max_urls_per_run: z.number().nullable().optional(),
  max_total_urls: z.number().nullable().optional(),
  deduplication_enabled: z.boolean().optional(),
  max_retries: z.number().optional(),
  request_timeout: z.number().optional(),
  respect_robots_txt: z.boolean().optional(),
  random_delay_min_ms: z.number().optional(),
  random_delay_max_ms: z.number().optional(),
  max_concurrent_jobs: z.number().optional(),
  output_formats: z.array(z.string()).optional(),
  output_grouping: z.string().optional(),
  max_rows_per_file: z.number().nullable().optional(),
  file_naming_template: z.string().nullable().optional(),
  compression_enabled: z.boolean().optional(),
  auto_export_enabled: z.boolean().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Project = z.infer<typeof projectSchema>;

export const jobSchema = z.object({
  id: z.string(),
  project_id: z.string(),
  topic_id: z.string().nullable().optional(),
  name: z.string(),
  target_url: z.string(),
  status: z.string(),
  cron_expression: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
  scheduled_at: z.string().nullable().optional(),
  started_at: z.string().nullable().optional(),
  finished_at: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Job = z.infer<typeof jobSchema>;

export const resultSchema = z.object({
  id: z.string(),
  job_id: z.string(),
  project_id: z.string(),
  structured_data: z.record(z.any()).nullable().optional(),
  raw_html: z.string().nullable().optional(),
  raw_html_path: z.string().nullable().optional(),
  raw_html_checksum: z.string().nullable().optional(),
  raw_html_size: z.number().nullable().optional(),
  raw_html_compressed_size: z.number().nullable().optional(),
  http_status: z.number().nullable().optional(),
  blocked: z.boolean().nullable().optional(),
  block_reason: z.string().nullable().optional(),
  method_used: z.string().nullable().optional(),
  created_at: z.string().optional().nullable(),
  updated_at: z.string().optional().nullable(),
});
export type Result = z.infer<typeof resultSchema>;

export const domainPolicySchema = z.object({
  id: z.string(),
  domain: z.string(),
  enabled: z.boolean(),
  method: z.enum(['auto', 'http', 'playwright']),
  use_proxy: z.boolean(),
  request_delay_ms: z.number(),
  max_concurrency: z.number(),
  user_agent: z.string().nullable().optional(),
  block_resources: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type DomainPolicy = z.infer<typeof domainPolicySchema>;

export const motor3dProductSchema = z.object({
  url: z.string(),
  title: z.string().nullable().optional(),
  price_text: z.string().nullable().optional(),
  images: z.array(z.string()),
  specs: z.array(z.string()).optional(),
  categories: z.array(z.string()),
  tags: z.array(z.string()),
  description_html: z.string().nullable().optional(),
  sku: z.string().nullable().optional(),
  raw: z.record(z.any()),
});
export type Motor3DProduct = z.infer<typeof motor3dProductSchema>;

// Campaigns (kept for backend compatibility)
export const campaignSchema = z.object({
  id: z.string(),
  name: z.string(),
  query: z.string(),
  seed_urls: z.array(z.string()),
  allowed_domains: z.array(z.string()).nullable().optional(),
  max_pages: z.number(),
  pages_collected: z.number(),
  follow_links: z.boolean(),
  status: z.string(),
  started_at: z.string().nullable().optional(),
  finished_at: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Campaign = z.infer<typeof campaignSchema>;

export const crawledPageSchema = z.object({
  id: z.string(),
  campaign_id: z.string(),
  url: z.string(),
  title: z.string().nullable().optional(),
  raw_html: z.string().nullable().optional(),
  text_content: z.string().nullable().optional(),
  http_status: z.number().nullable().optional(),
  status: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type CrawledPage = z.infer<typeof crawledPageSchema>;

// Topics
export const topicSchema = z.object({
  id: z.string(),
  name: z.string(),
  query: z.string(),
  search_engine: z.string(),
  max_results: z.number(),
  category: z.string().nullable().optional(),
  directory_path: z.string().nullable().optional(),
  status: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Topic = z.infer<typeof topicSchema>;

export const topicUrlSchema = z.object({
  id: z.string(),
  topic_id: z.string(),
  url: z.string(),
  title: z.string().nullable().optional(),
  snippet: z.string().nullable().optional(),
  rank: z.number().nullable().optional(),
  selected_for_scraping: z.boolean(),
  scraped: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type TopicUrl = z.infer<typeof topicUrlSchema>;

// Exports
export const exportSchema = z.object({
  id: z.string(),
  project_id: z.string(),
  topic_id: z.string().nullable().optional(),
  name: z.string(),
  format: z.string(),
  file_path: z.string().nullable().optional(),
  file_size: z.number().nullable().optional(),
  record_count: z.number(),
  status: z.string(),
  error_message: z.string().nullable().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Export = z.infer<typeof exportSchema>;

// Settings
export const settingSchema = z.object({
  id: z.string(),
  key: z.string(),
  value: z.record(z.any()).nullable().optional(),
  description: z.string().nullable().optional(),
  category: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Setting = z.infer<typeof settingSchema>;

// Projects
export async function getProjects(): Promise<Project[]> {
  const data = await request<Project[]>(`${API_PREFIX}/projects/`);
  return z.array(projectSchema).parse(data);
}

export async function createProject(input: {
  name: string;
  description?: string;
  content_type?: string;
  extraction_schema?: object | null;
}): Promise<Project> {
  const data = await request<Project>(`${API_PREFIX}/projects/`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return projectSchema.parse(data);
}

export async function getProject(id: string): Promise<Project> {
  const data = await request<Project>(`${API_PREFIX}/projects/${id}`);
  return projectSchema.parse(data);
}

export async function updateProject(
  id: string,
  input: Partial<{
    name: string;
    description: string;
    content_type: string;
    extraction_schema: object | null;
    allowed_domains: string[];
    url_include_patterns: string[];
    url_exclude_patterns: string[];
    max_urls_per_run: number;
    max_total_urls: number;
    deduplication_enabled: boolean;
    max_retries: number;
    request_timeout: number;
    respect_robots_txt: boolean;
    random_delay_min_ms: number;
    random_delay_max_ms: number;
    max_concurrent_jobs: number;
    output_formats: string[];
    output_grouping: string;
    max_rows_per_file: number;
    file_naming_template: string;
    compression_enabled: boolean;
    auto_export_enabled: boolean;
  }>
): Promise<Project> {
  const data = await request<Project>(`${API_PREFIX}/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
  return projectSchema.parse(data);
}

export async function deleteProject(id: string): Promise<void> {
  await request<void>(`${API_PREFIX}/projects/${id}`, { method: 'DELETE' });
}

export async function stopProject(id: string): Promise<{ revoked: number; cancelled: number }> {
  return request<{ revoked: number; cancelled: number }>(`${API_PREFIX}/projects/${id}/stop`, {
    method: 'POST',
  });
}

// Jobs
export async function getJobs(): Promise<Job[]> {
  const data = await request<Job[]>(`${API_PREFIX}/jobs/`);
  return z.array(jobSchema).parse(data);
}

export async function getJob(id: string): Promise<Job> {
  const data = await request<Job>(`${API_PREFIX}/jobs/${id}`);
  return jobSchema.parse(data);
}

export async function createJob(input: {
  project_id: string;
  name: string;
  target_url: string;
  scheduled_at?: string | null;
  cron_expression?: string | null;
  topic_id?: string | null;
}): Promise<Job> {
  const data = await request<Job>(`${API_PREFIX}/projects/${input.project_id}/jobs`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return jobSchema.parse(data);
}

export async function createJobsBatch(input: {
  project_id: string;
  topic_id?: string;
  urls: string[];
  name_prefix?: string;
  allow_duplicates?: boolean;
}): Promise<{ created: Job[]; rejected: { url: string; reason: string }[] }> {
  const data = await request<{ created: Job[]; rejected: { url: string; reason: string }[] }>(
    `${API_PREFIX}/jobs/batch`,
    {
      method: 'POST',
      body: JSON.stringify({
        project_id: input.project_id,
        topic_id: input.topic_id,
        urls: input.urls,
        name_prefix: input.name_prefix,
        allow_duplicates: input.allow_duplicates,
      }),
    },
  );
  return {
    created: data.created.map((j) => jobSchema.parse(j)),
    rejected: data.rejected,
  };
}

// Results
export async function getJobResult(jobId: string): Promise<Result> {
  const data = await request<Result>(`${API_PREFIX}/jobs/${jobId}/results`);
  return resultSchema.parse(data);
}

// Domain policies (admin)
export async function listDomainPolicies(): Promise<DomainPolicy[]> {
  const data = await request<DomainPolicy[]>(`${API_PREFIX}/admin/domain-policies/`);
  return z.array(domainPolicySchema).parse(data);
}

export async function createDomainPolicy(input: {
  domain: string;
  enabled?: boolean;
  method?: 'auto' | 'http' | 'playwright';
  use_proxy?: boolean;
  request_delay_ms?: number;
  max_concurrency?: number;
  user_agent?: string | null;
  block_resources?: boolean;
}): Promise<DomainPolicy> {
  const data = await request<DomainPolicy>(`${API_PREFIX}/admin/domain-policies/`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return domainPolicySchema.parse(data);
}

// Motor3D connector
export async function motor3dDiscover(params?: {
  sitemap_url?: string;
  url_prefix?: string;
  limit?: number;
}): Promise<{ count: number; sample_urls: string[]; urls: string[] }> {
  const data = await request<{ count: number; sample_urls: string[]; urls: string[] }>(
    `${API_PREFIX}/admin/connectors/motor3d/discover`,
    {
      method: 'POST',
      body: JSON.stringify(params || {}),
    },
  );
  return data;
}

export async function motor3dCreateJobs(input: {
  project_id: string;
  urls: string[];
  policy_domain?: string;
  name_prefix?: string;
  allow_duplicates?: boolean;
}): Promise<{ created: number; rejected: { url: string; reason: string }[] }> {
  return request<{ created: number; rejected: { url: string; reason: string }[] }>(
    `${API_PREFIX}/admin/connectors/motor3d/create-jobs`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  );
}

export async function motor3dParse(input: {
  url: string;
  method?: 'auto' | 'http' | 'playwright';
  project_id?: string;
}) {
  return request<any>(`${API_PREFIX}/admin/connectors/motor3d/parse`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
}

export async function motor3dListProducts(): Promise<Motor3DProduct[]> {
  const data = await request<Motor3DProduct[]>(`${API_PREFIX}/admin/connectors/motor3d/products`);
  return z.array(motor3dProductSchema).parse(data);
}

export function motor3dExportCsvUrl(projectId?: string) {
  const url = new URL(`${API_PREFIX}/admin/connectors/motor3d/export-csv`);
  if (projectId) url.searchParams.set('project_id', projectId);
  return url.toString();
}

export async function motor3dRunAll(input: { project_id: string; max_urls?: number }) {
  return request<{ count: number; sample_urls: string[]; job_ids: string[] }>(
    `${API_PREFIX}/admin/connectors/motor3d/run`,
    {
      method: 'POST',
      body: JSON.stringify(input),
    },
  );
}

export async function updateDomainPolicy(
  id: string,
  input: {
    enabled?: boolean;
    method?: 'auto' | 'http' | 'playwright';
    use_proxy?: boolean;
    request_delay_ms?: number;
    max_concurrency?: number;
    user_agent?: string | null;
    block_resources?: boolean;
  },
) {
  const data = await request<DomainPolicy>(`${API_PREFIX}/admin/domain-policies/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(input),
  });
  return domainPolicySchema.parse(data);
}

// Campaigns
export async function getCampaigns(): Promise<Campaign[]> {
  const data = await request<Campaign[]>(`${API_PREFIX}/campaigns/`);
  return z.array(campaignSchema).parse(data);
}

export async function createCampaign(input: {
  name: string;
  query: string;
  seed_urls: string[];
  allowed_domains?: string[] | null;
  max_pages: number;
  follow_links: boolean;
}): Promise<Campaign> {
  const data = await request<Campaign>(`${API_PREFIX}/campaigns/`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return campaignSchema.parse(data);
}

export async function getCampaign(id: string): Promise<Campaign> {
  const data = await request<Campaign>(`${API_PREFIX}/campaigns/${id}`);
  return campaignSchema.parse(data);
}

export async function updateCampaignStatus(id: string, status: string): Promise<Campaign> {
  const data = await request<Campaign>(`${API_PREFIX}/campaigns/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
  return campaignSchema.parse(data);
}

export async function getCampaignPages(params: {
  campaignId: string;
  limit?: number;
  offset?: number;
  search?: string;
}): Promise<CrawledPage[]> {
  const url = new URL(`${API_PREFIX}/campaigns/${params.campaignId}/pages`);
  if (params.limit) url.searchParams.set('limit', params.limit.toString());
  if (params.offset) url.searchParams.set('offset', params.offset.toString());
  if (params.search) url.searchParams.set('search', params.search);
  const data = await request<CrawledPage[]>(url.toString());
  return z.array(crawledPageSchema).parse(data);
}

// Topics
export async function getTopics(): Promise<Topic[]> {
  const data = await request<Topic[]>(`${API_PREFIX}/topics/`);
  return z.array(topicSchema).parse(data);
}

export async function createTopic(input: {
  name: string;
  query: string;
  search_engine?: string;
  max_results?: number;
  category?: string | null;
  directory_path?: string | null;
}): Promise<Topic> {
  const data = await request<Topic>(`${API_PREFIX}/topics/`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return topicSchema.parse(data);
}

export async function getTopic(id: string): Promise<Topic> {
  const data = await request<Topic>(`${API_PREFIX}/topics/${id}`);
  return topicSchema.parse(data);
}

export async function deleteTopic(id: string): Promise<void> {
  await request<void>(`${API_PREFIX}/topics/${id}`, { method: 'DELETE' });
}

export async function getTopicUrls(params: {
  topicId: string;
  selected_for_scraping?: boolean;
  scraped?: boolean;
}): Promise<TopicUrl[]> {
  const url = new URL(`${API_PREFIX}/topics/${params.topicId}/urls`);
  if (params.selected_for_scraping !== undefined) {
    url.searchParams.set('selected_for_scraping', String(params.selected_for_scraping));
  }
  if (params.scraped !== undefined) {
    url.searchParams.set('scraped', String(params.scraped));
  }
  const data = await request<TopicUrl[]>(url.toString());
  return z.array(topicUrlSchema).parse(data);
}

export async function updateTopicUrlsSelection(input: {
  topicId: string;
  urlIds: string[];
  selected_for_scraping: boolean;
}): Promise<{ updated: number }> {
  return request<{ updated: number }>(`${API_PREFIX}/topics/${input.topicId}/urls/select`, {
    method: 'PATCH',
    body: JSON.stringify({ url_ids: input.urlIds, selected_for_scraping: input.selected_for_scraping }),
  });
}

export async function scrapeSelectedTopicUrls(input: {
  topicId: string;
  project_id: string;
}): Promise<{ jobs_created: number; rejected?: { url: string; reason: string }[] }> {
  return request<{ jobs_created: number; rejected?: { url: string; reason: string }[] }>(
    `${API_PREFIX}/topics/${input.topicId}/scrape-selected`,
    {
      method: 'POST',
      body: JSON.stringify({ project_id: input.project_id }),
    },
  );
}

// Settings
export async function getSettings(): Promise<Setting[]> {
  const data = await request<Setting[]>(`${API_PREFIX}/settings/`);
  return z.array(settingSchema).parse(data);
}

export async function getSetting(key: string): Promise<Setting> {
  const data = await request<Setting>(`${API_PREFIX}/settings/${key}`);
  return settingSchema.parse(data);
}

export async function updateSetting(key: string, value: Record<string, any>, description?: string): Promise<Setting> {
  const body: any = { value };
  if (description !== undefined) {
    body.description = description;
  }
  const data = await request<Setting>(`${API_PREFIX}/settings/${key}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
  return settingSchema.parse(data);
}

// Exports
export async function getExports(params?: {
  project_id?: string;
  topic_id?: string;
  status?: string;
  format?: string;
  date_from?: string;
  date_to?: string;
}): Promise<Export[]> {
  const url = new URL(`${API_PREFIX}/exports/`);
  if (params?.project_id) url.searchParams.set('project_id', params.project_id);
  if (params?.topic_id) url.searchParams.set('topic_id', params.topic_id);
  if (params?.status) url.searchParams.set('export_status', params.status);
  if (params?.format) url.searchParams.set('export_format', params.format);
  if (params?.date_from) url.searchParams.set('date_from', params.date_from);
  if (params?.date_to) url.searchParams.set('date_to', params.date_to);
  const data = await request<Export[]>(url.toString());
  return z.array(exportSchema).parse(data);
}

export async function getExport(id: string): Promise<Export> {
  const data = await request<Export>(`${API_PREFIX}/exports/${id}`);
  return exportSchema.parse(data);
}

export async function createExport(input: {
  project_id: string;
  topic_id?: string;
  name: string;
  format: string;
}): Promise<Export> {
  const data = await request<Export>(`${API_PREFIX}/exports/`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  return exportSchema.parse(data);
}

export function downloadExport(exportId: string): string {
  return `${API_PREFIX}/exports/${exportId}/download`;
}

export async function regenerateExport(exportId: string): Promise<Export> {
  const data = await request<Export>(`${API_PREFIX}/exports/${exportId}/regenerate`, {
    method: 'POST',
  });
  return exportSchema.parse(data);
}

export const apiBase = API_BASE;

// Delete job
export async function deleteJob(id: string): Promise<void> {
  await request<void>(`${API_PREFIX}/jobs/${id}`, { method: 'DELETE' });
}
