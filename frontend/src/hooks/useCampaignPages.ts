'use client';

import { useQuery } from '@tanstack/react-query';
import { CrawledPage, getCampaignPages } from '@/lib/api-client';

export function useCampaignPages(params: { campaignId?: string; limit?: number; offset?: number; search?: string }) {
  return useQuery<CrawledPage[]>({
    queryKey: ['campaigns', params.campaignId, 'pages', params.limit, params.offset, params.search],
    queryFn: () =>
      getCampaignPages({
        campaignId: params.campaignId as string,
        limit: params.limit,
        offset: params.offset,
        search: params.search,
      }),
    enabled: Boolean(params.campaignId),
  });
}
