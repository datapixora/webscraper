'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createProject, getProjects, Project } from '@/lib/api-client';

export function useProjects() {
  const queryClient = useQueryClient();
  const projectsQuery = useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: getProjects,
  });

  const createProjectMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });

  return { projectsQuery, createProjectMutation };
}
