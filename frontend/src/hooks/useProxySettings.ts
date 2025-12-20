import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

interface ProxySettings {
  proxy_enabled: boolean;
  proxy_provider: string;
  proxy_type: string;
  proxy_country: string;
  proxy_sticky_enabled: boolean;
  proxy_sticky_ttl_sec: number;
  proxy_rotation_strategy: 'per_job' | 'on_failure' | 'per_request';
  proxy_retry_count: number;
  request_delay_min_ms: number;
  request_delay_max_ms: number;
  scrape_method_policy: 'http' | 'browser' | 'auto';
}

interface ProxySettingsUpdate {
  proxy_enabled?: boolean;
  proxy_provider?: string;
  proxy_type?: string;
  proxy_country?: string;
  proxy_sticky_enabled?: boolean;
  proxy_sticky_ttl_sec?: number;
  proxy_rotation_strategy?: 'per_job' | 'on_failure' | 'per_request';
  proxy_retry_count?: number;
  request_delay_min_ms?: number;
  request_delay_max_ms?: number;
  scrape_method_policy?: 'http' | 'browser' | 'auto';
}

async function fetchProxySettings(): Promise<ProxySettings> {
  const response = await fetch(`${API_BASE}/api/v1/admin/settings/proxy`);
  if (!response.ok) {
    throw new Error('Failed to fetch proxy settings');
  }
  return response.json();
}

async function updateProxySettings(settings: ProxySettingsUpdate): Promise<ProxySettings> {
  const response = await fetch(`${API_BASE}/api/v1/admin/settings/proxy`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(settings),
  });
  if (!response.ok) {
    throw new Error('Failed to update proxy settings');
  }
  return response.json();
}

export function useProxySettings() {
  const queryClient = useQueryClient();

  const settingsQuery = useQuery({
    queryKey: ['proxySettings'],
    queryFn: fetchProxySettings,
  });

  const updateMutation = useMutation({
    mutationFn: updateProxySettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['proxySettings'] });
    },
  });

  return {
    settingsQuery,
    updateMutation,
  };
}
