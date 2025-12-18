'use client';

import { useState, useRef, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Send, Loader2, ChevronLeft } from 'lucide-react';
import Link from 'next/link';
import { matchesApi } from '@/lib/api';
import { Avatar, Input } from '@/components/ui';
import { useAuthStore } from '@/store/auth';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { Match, Message } from '@/types';

export default function ChatRoomPage() {
  const params = useParams();
  const matchId = params.id as string;
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [message, setMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch match details
  const { data: matches } = useQuery({
    queryKey: ['matches'],
    queryFn: async () => {
      const response = await matchesApi.getMatches();
      return response.data as Match[];
    },
  });

  const match = matches?.find((m) => m.id === matchId);

  // Fetch messages
  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', matchId],
    queryFn: async () => {
      const response = await matchesApi.getMessages(matchId);
      return response.data as Message[];
    },
    refetchInterval: 3000, // Poll every 3 seconds
  });

  // Send message mutation
  const { mutate: sendMessage, isPending } = useMutation({
    mutationFn: async (content: string) => {
      const response = await matchesApi.sendMessage(matchId, content);
      return response.data;
    },
    onSuccess: () => {
      setMessage('');
      queryClient.invalidateQueries({ queryKey: ['messages', matchId] });
    },
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isPending) {
      sendMessage(message.trim());
    }
  };

  if (!match) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="fixed inset-0 flex flex-col bg-gray-950">
      {/* Header */}
      <header className="flex items-center gap-4 p-4 bg-gray-900 border-b border-white/10">
        <Link href="/chat" className="p-1 text-white/60 hover:text-white">
          <ChevronLeft className="w-6 h-6" />
        </Link>
        <Avatar
          src={match.matched_user.avatar_url}
          name={match.matched_user.display_name}
          size="md"
        />
        <div>
          <h2 className="font-semibold text-white">
            {match.matched_user.display_name || 'Anonymous'}
          </h2>
          <p className="text-xs text-white/50">
            {Math.round(match.compatibility_score)}% match
          </p>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 text-purple-500 animate-spin" />
          </div>
        ) : messages && messages.length > 0 ? (
          messages.map((msg, index) => {
            const isOwn = msg.sender_id === user?.id;
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={cn(
                  'flex',
                  isOwn ? 'justify-end' : 'justify-start'
                )}
              >
                {msg.is_system_message ? (
                  <div className="text-center text-white/40 text-sm py-2">
                    {msg.content}
                  </div>
                ) : (
                  <div
                    className={cn(
                      'max-w-[75%] rounded-2xl px-4 py-2',
                      isOwn
                        ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white'
                        : 'bg-white/10 text-white'
                    )}
                  >
                    <p>{msg.content}</p>
                    <p className={cn(
                      'text-xs mt-1',
                      isOwn ? 'text-white/70' : 'text-white/40'
                    )}>
                      {formatRelativeTime(msg.created_at)}
                    </p>
                  </div>
                )}
              </motion.div>
            );
          })
        ) : (
          <div className="text-center py-8">
            <p className="text-white/40 mb-2">No messages yet</p>
            {match.icebreaker_prompt && (
              <p className="text-sm text-purple-400">
                💡 Try: &quot;{match.icebreaker_prompt}&quot;
              </p>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 bg-gray-900 border-t border-white/10">
        <div className="flex gap-3">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1"
          />
          <button
            type="submit"
            disabled={!message.trim() || isPending}
            className={cn(
              'p-3 rounded-xl transition-colors',
              message.trim()
                ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white'
                : 'bg-white/10 text-white/40'
            )}
          >
            {isPending ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
