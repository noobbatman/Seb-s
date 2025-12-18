'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Heart, X, Loader2, Sparkles, RefreshCw } from 'lucide-react';
import { matchesApi } from '@/lib/api';
import { Button, Avatar } from '@/components/ui';
import { MediaCard } from '@/components/media';
import { cn, getCompatibilityColor, getCompatibilityLabel } from '@/lib/utils';
import type { PotentialMatch } from '@/types';

export default function DiscoverPage() {
  const queryClient = useQueryClient();
  const [currentIndex, setCurrentIndex] = useState(0);

  // Fetch potential matches
  const { data: matches, isLoading, refetch } = useQuery({
    queryKey: ['discover'],
    queryFn: async () => {
      const response = await matchesApi.discover(10);
      return response.data as PotentialMatch[];
    },
  });

  // Accept/reject mutation
  const { mutate: respondToMatch, isPending } = useMutation({
    mutationFn: async ({ userId, action }: { userId: string; action: 'accept' | 'reject' }) => {
      // First create the match, then respond
      const response = await matchesApi.respondToMatch(userId, action);
      return response.data;
    },
    onSuccess: () => {
      setCurrentIndex((prev) => prev + 1);
      queryClient.invalidateQueries({ queryKey: ['matches'] });
    },
  });

  const currentMatch = matches?.[currentIndex];
  const hasMoreMatches = matches && currentIndex < matches.length;

  const handleAction = (action: 'accept' | 'reject') => {
    if (!currentMatch) return;
    respondToMatch({ userId: currentMatch.user.id, action });
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin mb-4" />
        <p className="text-white/60">Finding your matches...</p>
      </div>
    );
  }

  if (!hasMoreMatches) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-6">
        <div className="w-20 h-20 bg-gradient-to-br from-pink-500/20 to-purple-600/20 rounded-3xl flex items-center justify-center mb-6">
          <Sparkles className="w-10 h-10 text-purple-400" />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">No more matches right now</h2>
        <p className="text-white/60 mb-8">
          Check back later or update your profile to find more cultural soulmates
        </p>
        <Button onClick={() => { setCurrentIndex(0); refetch(); }}>
          <RefreshCw className="w-5 h-5 mr-2" />
          Refresh
        </Button>
      </div>
    );
  }

  return (
    <div className="py-6">
      <AnimatePresence mode="wait">
        {currentMatch && (
          <motion.div
            key={currentMatch.user.id}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl overflow-hidden border border-white/10"
          >
            {/* User header */}
            <div className="p-6 text-center">
              <Avatar
                src={currentMatch.user.avatar_url}
                name={currentMatch.user.display_name}
                size="xl"
                className="mx-auto mb-4"
              />
              <h2 className="text-2xl font-bold text-white mb-1">
                {currentMatch.user.display_name || 'Anonymous'}
              </h2>
              
              {/* Compatibility score */}
              <div className="flex items-center justify-center gap-2 mt-4">
                <span className={cn(
                  'text-4xl font-bold',
                  getCompatibilityColor(currentMatch.compatibility_score)
                )}>
                  {Math.round(currentMatch.compatibility_score)}%
                </span>
                <span className="text-white/60">match</span>
              </div>
              <p className="text-white/50 text-sm mt-1">
                {getCompatibilityLabel(currentMatch.compatibility_score)}
              </p>
            </div>

            {/* Shared interests */}
            {currentMatch.shared_items.length > 0 && (
              <div className="px-6 pb-6">
                <h3 className="text-sm font-medium text-white/60 mb-3">
                  You both love
                </h3>
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {currentMatch.shared_items.map((item) => (
                    <MediaCard
                      key={item.media.id}
                      media={item.media}
                      size="sm"
                      showActions={false}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Icebreaker */}
            {currentMatch.icebreaker_prompt && (
              <div className="mx-6 mb-6 p-4 bg-purple-500/10 rounded-2xl border border-purple-500/20">
                <p className="text-sm text-purple-300 font-medium mb-1">💬 Icebreaker</p>
                <p className="text-white">{currentMatch.icebreaker_prompt}</p>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-4 p-6 pt-0">
              <Button
                variant="outline"
                size="lg"
                className="flex-1 border-red-500/30 text-red-400 hover:bg-red-500/10"
                onClick={() => handleAction('reject')}
                disabled={isPending}
              >
                <X className="w-6 h-6" />
              </Button>
              <Button
                size="lg"
                className="flex-1"
                onClick={() => handleAction('accept')}
                disabled={isPending}
              >
                <Heart className="w-6 h-6" />
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress indicator */}
      {matches && matches.length > 0 && (
        <div className="flex justify-center gap-1 mt-6">
          {matches.map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-2 h-2 rounded-full transition-colors',
                i === currentIndex ? 'bg-pink-500' : i < currentIndex ? 'bg-white/30' : 'bg-white/10'
              )}
            />
          ))}
        </div>
      )}
    </div>
  );
}
