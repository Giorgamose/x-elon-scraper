import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { postsApi, Post } from '../api/client';
import { format } from 'date-fns';
import { ArrowLeft, Heart, Repeat, MessageCircle, Image as ImageIcon } from 'lucide-react';

export default function PostDetail() {
  const { postId } = useParams<{ postId: string }>();
  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (postId) {
      loadPost();
    }
  }, [postId]);

  const loadPost = async () => {
    try {
      setLoading(true);
      const res = await postsApi.get(postId!);
      setPost(res.data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load post');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Loading post...</div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="space-y-4">
        <Link to="/posts" className="inline-flex items-center text-blue-600 hover:text-blue-700">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Posts
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error || 'Post not found'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link to="/posts" className="inline-flex items-center text-blue-600 hover:text-blue-700">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Posts
      </Link>

      <div className="bg-white rounded-lg shadow p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              @{post.author_username}
            </h2>
            <p className="text-gray-500 text-sm">
              {format(new Date(post.created_at), 'MMMM d, yyyy · HH:mm')}
            </p>
          </div>
          <span className={`px-3 py-1 text-sm rounded ${
            post.source === 'api' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
          }`}>
            {post.source}
          </span>
        </div>

        {/* Content */}
        <p className="text-lg text-gray-800 mb-6 whitespace-pre-wrap">{post.text}</p>

        {/* Media */}
        {post.has_media && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
              <ImageIcon className="w-4 h-4 mr-2" />
              Media ({post.media_urls.length})
            </h3>
            <div className="grid grid-cols-2 gap-4">
              {post.media_urls.map((url, idx) => (
                <a
                  key={idx}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block rounded-lg overflow-hidden border border-gray-200 hover:border-blue-500 transition"
                >
                  <img src={url} alt={`Media ${idx + 1}`} className="w-full h-auto" />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Engagement */}
        <div className="flex items-center space-x-8 py-4 border-t border-gray-200">
          <div className="flex items-center space-x-2 text-gray-600">
            <Heart className="w-5 h-5" />
            <span className="font-semibold">{post.like_count.toLocaleString()}</span>
            <span className="text-sm">Likes</span>
          </div>
          <div className="flex items-center space-x-2 text-gray-600">
            <Repeat className="w-5 h-5" />
            <span className="font-semibold">{post.retweet_count.toLocaleString()}</span>
            <span className="text-sm">Retweets</span>
          </div>
          <div className="flex items-center space-x-2 text-gray-600">
            <MessageCircle className="w-5 h-5" />
            <span className="font-semibold">{post.reply_count.toLocaleString()}</span>
            <span className="text-sm">Replies</span>
          </div>
          {post.quote_count > 0 && (
            <div className="flex items-center space-x-2 text-gray-600">
              <span className="font-semibold">{post.quote_count.toLocaleString()}</span>
              <span className="text-sm">Quotes</span>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Post ID:</span>
            <span className="ml-2 font-mono text-gray-900">{post.post_id}</span>
          </div>
          <div>
            <span className="text-gray-500">Collected:</span>
            <span className="ml-2 text-gray-900">
              {format(new Date(post.collected_at), 'MMM d, yyyy HH:mm')}
            </span>
          </div>
          {post.is_reply && (
            <div className="col-span-2">
              <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs">Reply</span>
            </div>
          )}
          {post.is_retweet && (
            <div className="col-span-2">
              <span className="px-2 py-1 bg-green-50 text-green-700 rounded text-xs">Retweet</span>
            </div>
          )}
          {post.is_quote && (
            <div className="col-span-2">
              <span className="px-2 py-1 bg-purple-50 text-purple-700 rounded text-xs">Quote Tweet</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
