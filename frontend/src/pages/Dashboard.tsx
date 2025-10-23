import { useEffect, useState } from 'react';
import { postsApi, jobsApi, PostStats, Job } from '../api/client';
import { TrendingUp, FileText, Activity, Clock } from 'lucide-react';
import { format } from 'date-fns';

export default function Dashboard() {
  const [stats, setStats] = useState<PostStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsRes, jobsRes] = await Promise.all([
        postsApi.stats(),
        jobsApi.list({ limit: 5 }),
      ]);
      setStats(statsRes.data);
      setRecentJobs(jobsRes.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const triggerCollection = async () => {
    try {
      await jobsApi.create({
        job_type: 'collect_posts',
        params: { max_posts: 100 },
      });
      alert('Collection job started!');
      loadData();
    } catch (err: any) {
      alert(`Failed to start job: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <button
          onClick={triggerCollection}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          Start Collection
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Posts"
          value={stats?.total_posts || 0}
          icon={FileText}
          color="blue"
        />
        <StatCard
          title="Total Likes"
          value={stats?.total_likes.toLocaleString() || 0}
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          title="Avg Likes/Post"
          value={stats?.avg_likes_per_post.toFixed(1) || 0}
          icon={Activity}
          color="purple"
        />
        <StatCard
          title="Last 24h"
          value={stats?.posts_last_24h || 0}
          icon={Clock}
          color="orange"
        />
      </div>

      {/* Sources Breakdown */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Collection Sources
        </h2>
        <div className="space-y-3">
          {stats?.posts_by_source &&
            Object.entries(stats.posts_by_source).map(([source, count]) => (
              <div key={source} className="flex items-center justify-between">
                <span className="text-gray-700 capitalize">{source}</span>
                <span className="font-semibold text-gray-900">
                  {count.toLocaleString()}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">Recent Jobs</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {recentJobs.map((job) => (
            <div key={job.id} className="px-6 py-4 flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900">{job.job_type}</div>
                <div className="text-sm text-gray-500">
                  {format(new Date(job.created_at), 'MMM d, yyyy HH:mm')}
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-500">
                  {job.posts_collected} collected
                </div>
                <StatusBadge status={job.status} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'blue' | 'green' | 'purple' | 'orange';
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    orange: 'bg-orange-50 text-orange-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${colors[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  };

  return (
    <span className={`px-2 py-1 text-xs font-semibold rounded ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
}
