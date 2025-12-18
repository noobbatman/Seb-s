'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Input } from '@/components/ui';
import { MediaCard } from './MediaCard';
import { mediaApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import type { MediaSearchResult } from '@/types';

interface MediaSearchProps {
  mediaType: 'movie' | 'artist' | 'track';
  onSelect: (item: MediaSearchResult) => void;
  placeholder?: string;
  className?: string;
}

export function MediaSearch({ mediaType, onSelect, placeholder, className }: MediaSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MediaSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const searchApi = useCallback(async (q: string) => {
    if (!q.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      let response;
      switch (mediaType) {
        case 'movie':
          response = await mediaApi.searchMovies(q);
          break;
        case 'artist':
          response = await mediaApi.searchArtists(q);
          break;
        case 'track':
          response = await mediaApi.searchTracks(q);
          break;
      }
      setResults(response.data);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [mediaType]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      searchApi(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchApi]);

  const handleSelect = (item: MediaSearchResult) => {
    onSelect(item);
    setQuery('');
    setResults([]);
    setIsOpen(false);
  };

  return (
    <div className={cn('relative', className)}>
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
        <Input
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder || `Search ${mediaType}s...`}
          className="pl-12 pr-10"
        />
        {query && (
          <button
            onClick={() => {
              setQuery('');
              setResults([]);
            }}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Results dropdown */}
      <AnimatePresence>
        {isOpen && (query || results.length > 0) && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute top-full left-0 right-0 mt-2 bg-gray-900 rounded-xl border border-white/10 shadow-2xl overflow-hidden z-50"
          >
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-purple-500 animate-spin" />
              </div>
            ) : results.length > 0 ? (
              <div className="max-h-80 overflow-y-auto p-3">
                <div className="grid grid-cols-4 gap-3">
                  {results.map((item) => (
                    <MediaCard
                      key={item.id}
                      media={{
                        ...item,
                        media_type: mediaType,
                      }}
                      size="sm"
                      showActions={false}
                      onClick={() => handleSelect(item)}
                    />
                  ))}
                </div>
              </div>
            ) : query ? (
              <div className="py-8 text-center text-white/60">
                No results found for &quot;{query}&quot;
              </div>
            ) : null}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
