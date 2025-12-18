'use client';

import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Loader2, Sparkles, MessageCircle } from 'lucide-react';
import { matchesApi } from '@/lib/api';
import { Avatar, Button } from '@/components/ui';
import { cn, getCompatibilityColor, formatRelativeTime } from '@/lib/utils';
import type { Match } from '@/types';

export default function MatchesPage() {
  const { data: matches, isLoading } = useQuery({
    queryKey: ['matches'],
    queryFn: async () => {
      const response = await matchesApi.getMatches('accepted');
      return response.data as Match[];
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  if (!matches || matches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
        <div className="w-20 h-20 bg-gradient-to-br from-pink-500/20 to-purple-600/20 rounded-3xl flex items-center justify-center mb-6">
          <Sparkles className="w-10 h-10 text-purple-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">No matches yet</h2>
        <p className="text-white/60 mb-8">
          Keep swiping in Discover to find your cultural soulmates!
        </p>
        <Link href="/discover">
          <Button>Start Discovering</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="py-6 space-y-4">
      <h1 className="text-2xl font-bold text-white mb-6">Your Matches</h1>
      
      {matches.map((match, index) => (
        <motion.div
          key={match.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Link href={`/chat/${match.id}`}>
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-4 border border-white/10 hover:border-purple-500/30 transition-colors">
              <div className="flex items-center gap-4">
                <Avatar
                  src={match.matched_user.avatar_url}
                  name={match.matched_user.display_name}
                  size="lg"
                />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-semibold text-white truncate">
                      {match.matched_user.display_name || 'Anonymous'}
                    </h3>
                    <span className={cn(
                      'text-sm font-bold',
                      getCompatibilityColor(match.compatibility_score)
                    )}>
                      {Math.round(match.compatibility_score)}%
                    </span>
                  </div>
                  
                  {match.icebreaker_prompt && (
                    <p className="text-sm text-white/60 truncate">
                      💬 {match.icebreaker_prompt}
                    </p>
                  )}
                  
                  <p className="text-xs text-white/40 mt-1">
                    Matched {formatRelativeTime(match.created_at)}
                  </p>
                </div>
                
                <div className="p-2 bg-purple-500/20 rounded-xl">
                  <MessageCircle className="w-5 h-5 text-purple-400" />
                </div>
              </div>
              
              {/* Shared items preview */}
              {match.shared_items.length > 0 && (
                <div className="flex gap-1 mt-3 overflow-hidden">
                  {match.shared_items.slice(0, 4).map((item) => (
                    <div
                      key={item.media.id}
                      className="w-10 h-10 rounded-lg overflow-hidden bg-gray-700 flex-shrink-0"
                    >
                      {item.media.image_url && (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={item.media.image_url}
                          alt={item.media.title}
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                  ))}
                  {match.shared_items.length > 4 && (
                    <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center text-xs text-white/60">
                      +{match.shared_items.length - 4}
                    </div>
                  )}
                </div>
              )}
            </div>
          </Link>
        </motion.div>
      ))}
    </div>
  );
}
