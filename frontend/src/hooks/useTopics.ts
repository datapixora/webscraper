'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createTopic, getTopic, getTopics, Topic } from '@/lib/api-client';

export function useTopics() {
  const queryClient = useQueryClient();
  const topicsQuery = useQuery<Topic[]>({
    queryKey: ['topics'],
    queryFn: getTopics,
  });

  const createTopicMutation = useMutation({
    mutationFn: createTopic,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['topics'] });
    },
  });

  const topicQuery = (id?: string) =>
    useQuery<Topic>({
      queryKey: ['topics', id],
      queryFn: () => getTopic(id as string),
      enabled: Boolean(id),
    });

  return { topicsQuery, createTopicMutation, topicQuery };
}
