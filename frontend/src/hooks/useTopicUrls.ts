'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getTopicUrls, updateTopicUrlsSelection, scrapeSelectedTopicUrls, TopicUrl } from '@/lib/api-client';

export function useTopicUrls(params: { topicId?: string; selected_for_scraping?: boolean; scraped?: boolean }) {
  const queryClient = useQueryClient();

  const urlsQuery = useQuery<TopicUrl[]>({
    queryKey: ['topics', params.topicId, 'urls', params.selected_for_scraping, params.scraped],
    queryFn: () =>
      getTopicUrls({
        topicId: params.topicId as string,
        selected_for_scraping: params.selected_for_scraping,
        scraped: params.scraped,
      }),
    enabled: Boolean(params.topicId),
  });

  const updateSelectionMutation = useMutation({
    mutationFn: (input: { urlIds: string[]; selected: boolean }) =>
      updateTopicUrlsSelection({
        topicId: params.topicId as string,
        urlIds: input.urlIds,
        selected_for_scraping: input.selected,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topics', params.topicId, 'urls'] });
    },
  });

  const scrapeSelectedMutation = useMutation({
    mutationFn: (input: { project_id?: string }) =>
      scrapeSelectedTopicUrls({ topicId: params.topicId as string, project_id: input.project_id }),
  });

  return { urlsQuery, updateSelectionMutation, scrapeSelectedMutation };
}
