'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Campaign,
  createCampaign,
  getCampaign,
  getCampaigns,
  updateCampaignStatus,
} from '@/lib/api-client';

export function useCampaigns() {
  const queryClient = useQueryClient();
  const campaignsQuery = useQuery<Campaign[]>({
    queryKey: ['campaigns'],
    queryFn: getCampaigns,
  });

  const createCampaignMutation = useMutation({
    mutationFn: createCampaign,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: (params: { id: string; status: string }) => updateCampaignStatus(params.id, params.status),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      queryClient.invalidateQueries({ queryKey: ['campaigns', variables.id] });
    },
  });

  const campaignQuery = (id: string | undefined) =>
    useQuery<Campaign>({
      queryKey: ['campaigns', id],
      queryFn: () => getCampaign(id as string),
      enabled: Boolean(id),
    });

  return { campaignsQuery, createCampaignMutation, updateStatusMutation, campaignQuery };
}
