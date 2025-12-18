'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Loader2, MessageCircle } from 'lucide-react';
import { matchesApi } from '@/lib/api';
import { Avatar } from '@/components/ui';
import { formatRelativeTime } from '@/lib/utils';
import type { Match } from '@/types';

export default function ChatListPage() {
  const { data: matches, isLoading } = useQuery({
    queryKey: ['matches', 'matched'],
    queryFn: async () => {
      const response = await matchesApi.getMatches('matched');
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
          <MessageCircle className="w-10 h-10 text-purple-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">No conversations yet</h2>
        <p className="text-white/60">
          When you and a match both accept, you can start chatting here!
        </p>
      </div>
    );
  }

  return (
    <div className="py-6">
      <h1 className="text-2xl font-bold text-white mb-6">Messages</h1>
      
      <div className="space-y-2">
        {matches.map((match, index) => (
          <motion.div
            key={match.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Link href={`/chat/${match.id}`}>
              <div className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 hover:bg-white/10 transition-colors">
                <Avatar
                  src={match.matched_user.avatar_url}
                  name={match.matched_user.display_name}
                  size="lg"
                />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-white truncate">
                      {match.matched_user.display_name || 'Anonymous'}
                    </h3>
                    <span className="text-xs text-white/40">
                      {formatRelativeTime(match.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-white/60 truncate mt-0.5">
                    Start the conversation! 💬
                  </p>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
