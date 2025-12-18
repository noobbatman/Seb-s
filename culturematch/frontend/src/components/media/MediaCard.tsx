'use client';

import { useState } from 'react';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Star, Music, Film, X, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { MediaItem } from '@/types';

interface MediaCardProps {
  media: MediaItem | {
    id?: string;
    title: string;
    image_url?: string | null;
    media_type?: string;
    artist?: string;
    year?: number;
  };
  rating?: number | null;
  onAdd?: () => void;
  onRemove?: () => void;
  onClick?: () => void;
  isSelected?: boolean;
  showActions?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function MediaCard({
  media,
  rating,
  onAdd,
  onRemove,
  onClick,
  isSelected = false,
  showActions = true,
  size = 'md',
  className,
}: MediaCardProps) {
  const sizes = {
    sm: 'w-24 h-36',
    md: 'w-32 h-48',
    lg: 'w-40 h-60',
  };

  const isMusic = media.media_type === 'artist' || media.media_type === 'track' || media.media_type === 'album';
  const [imageError, setImageError] = useState(false);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      whileHover={{ scale: 1.05 }}
      onClick={onClick}
      className={cn(
        'relative group cursor-pointer rounded-xl overflow-hidden',
        sizes[size],
        isSelected && 'ring-2 ring-pink-500 ring-offset-2 ring-offset-gray-900',
        className
      )}
    >
      {/* Image */}
      {media.image_url && !imageError ? (
        <Image
          src={media.image_url}
          alt={media.title}
          fill
          sizes="(max-width: 640px) 96px, (max-width: 1024px) 128px, 160px"
          loading="eager"
          unoptimized
          className="object-cover"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="w-full h-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center">
          {isMusic ? (
            <Music className="w-8 h-8 text-white/40" />
          ) : (
            <Film className="w-8 h-8 text-white/40" />
          )}
        </div>
      )}

      {/* Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

      {/* Content */}
      <div className="absolute bottom-0 left-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <p className="text-white text-sm font-medium truncate">{(('title' in media && media.title) || ('name' in media && media.name) || 'Unknown') as string}</p>
        {'artist' in media && media.artist && (
          <p className="text-white/60 text-xs truncate">{media.artist}</p>
        )}
        {'year' in media && media.year && (
          <p className="text-white/60 text-xs">{media.year}</p>
        )}
      </div>

      {/* Rating badge */}
      {rating && (
        <div className="absolute top-2 left-2 flex items-center gap-1 bg-black/60 backdrop-blur-sm rounded-full px-2 py-0.5">
          <Star className="w-3 h-3 text-yellow-400 fill-yellow-400" />
          <span className="text-white text-xs font-medium">{rating}</span>
        </div>
      )}

      {/* Actions */}
      {showActions && (
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          {isSelected || onRemove ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRemove?.();
              }}
              className="p-1.5 bg-red-500/80 hover:bg-red-500 rounded-full backdrop-blur-sm transition-colors"
            >
              <X className="w-4 h-4 text-white" />
            </button>
          ) : onAdd ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAdd();
              }}
              className="p-1.5 bg-green-500/80 hover:bg-green-500 rounded-full backdrop-blur-sm transition-colors"
            >
              <Plus className="w-4 h-4 text-white" />
            </button>
          ) : null}
        </div>
      )}
    </motion.div>
  );
}
