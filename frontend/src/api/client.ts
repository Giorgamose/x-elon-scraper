import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Post {
  id: string;
  post_id: string;
  author_username: string;
  author_name?: string;
  text: string;
  created_at: string;
  collected_at: string;
  source: 'api' | 'scraper';
  reply_count: number;
  retweet_count: number;
  like_count: number;
  quote_count: number;
  is_reply: boolean;
  is_retweet: boolean;
  is_quote: boolean;
  media_urls: string[];
  has_media: boolean;
}

export interface Job {
  id: string;
  job_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  params: Record<string, any>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  posts_collected: number;
  posts_skipped: number;
  posts_failed: number;
  error_message?: string;
  duration_seconds?: number;
  success_rate: number;
}

export interface PostStats {
  total_posts: number;
  posts_by_source: Record<string, number>;
  total_likes: number;
  total_retweets: number;
  avg_likes_per_post: number;
  avg_retweets_per_post: number;
  posts_with_media: number;
  posts_with_media_percentage: number;
  posts_last_24h: number;
  posts_last_7d: number;
  posts_last_30d: number;
}

export const postsApi = {
  list: (params?: { limit?: number; offset?: number; source?: string }) =>
    api.get<Post[]>('/api/v1/posts', { params }),

  search: (params: {
    q?: string;
    source?: string;
    start_date?: string;
    end_date?: string;
    has_media?: boolean;
    limit?: number;
    offset?: number;
  }) => api.get<Post[]>('/api/v1/posts/search', { params }),

  get: (postId: string) => api.get<Post>(`/api/v1/posts/${postId}`),

  stats: () => api.get<PostStats>('/api/v1/posts/stats/overview'),
};

export const jobsApi = {
  list: (params?: { status?: string; limit?: number; offset?: number }) =>
    api.get<Job[]>('/api/v1/jobs', { params }),

  get: (jobId: string) => api.get<Job>(`/api/v1/jobs/${jobId}`),

  create: (data: { job_type: string; params?: Record<string, any> }) =>
    api.post<Job>('/api/v1/jobs', data),

  cancel: (jobId: string) => api.delete(`/api/v1/jobs/${jobId}`),
};

export const healthApi = {
  check: () => api.get('/health'),
};
