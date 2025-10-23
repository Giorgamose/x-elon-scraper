import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { postsApi, Post } from '../api/client';
import { format } from 'date-fns';
import { Search, Heart, Repeat, MessageCircle, Image } from 'lucide-react';

export default function Posts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [sourceFilter, setSourceFilter] = useState<string>('');

  useEffect(() => {
    loadPosts();
  }, [sourceFilter]);

  const loadPosts = async () => {
    try {
      setLoading(true);
      const params: any = { limit: 50 };
      if (sourceFilter) params.source = sourceFilter;

      const res = await postsApi.list(params);
      setPosts(res.data);
    } catch (err) {
      console.error('Failed to load posts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadPosts();
      return;
    }

    try {
      setLoading(true);
      const params: any = { q: searchQuery, limit: 50 };
      if (sourceFilter) params.source = sourceFilter;

      const res = await postsApi.search(params);
      setPosts(res.data);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <h1 className="text-3xl font-bold text-gray-900">Posts</h1>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search posts..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
          </div>
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
          >
            <option value="">All Sources</option>
            <option value="api">API</option>
            <option value="scraper">Scraper</option>
          </select>
          <button
            onClick={handleSearch}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            Search
          </button>
        </div>
      </div>

      {/* Posts List */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Loading posts...</div>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
          {posts.length === 0 && (
            <div className="text-center py-12 text-gray-500">
              No posts found. Try adjusting your filters.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PostCard({ post }: { post: Post }) {
  return (
    <Link
      to={`/posts/${post.post_id}`}
      className="block bg-white rounded-lg shadow hover:shadow-md transition p-6"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span className="font-semibold text-gray-900">
              @{post.author_username}
            </span>
            <span className="text-gray-500 text-sm">·</span>
            <span className="text-gray-500 text-sm">
              {format(new Date(post.created_at), 'MMM d, yyyy')}
            </span>
            <span className={`px-2 py-0.5 text-xs rounded ${
              post.source === 'api' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
            }`}>
              {post.source}
            </span>
          </div>
          <p className="text-gray-800 mb-3">{post.text}</p>
          {post.has_media && (
            <div className="flex items-center text-sm text-gray-500 mb-3">
              <Image className="w-4 h-4 mr-1" />
              {post.media_urls.length} {post.media_urls.length === 1 ? 'image' : 'images'}
            </div>
          )}
          <div className="flex items-center space-x-6 text-sm text-gray-500">
            <div className="flex items-center space-x-1">
              <Heart className="w-4 h-4" />
              <span>{post.like_count.toLocaleString()}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Repeat className="w-4 h-4" />
              <span>{post.retweet_count.toLocaleString()}</span>
            </div>
            <div className="flex items-center space-x-1">
              <MessageCircle className="w-4 h-4" />
              <span>{post.reply_count.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
