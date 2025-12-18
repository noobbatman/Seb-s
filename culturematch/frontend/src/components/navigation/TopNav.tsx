'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { Heart, ChevronLeft, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TopNavProps {
  title?: string;
  showBack?: boolean;
  showSettings?: boolean;
  className?: string;
}

export function TopNav({ title, showBack = false, showSettings = false, className }: TopNavProps) {
  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-40 bg-gray-900/95 backdrop-blur-lg border-b border-white/10',
        className
      )}
    >
      <div className="max-w-lg mx-auto px-4 h-16 flex items-center justify-between">
        {/* Left side */}
        <div className="w-12">
          {showBack && (
            <Link
              href="/discover"
              className="p-2 -ml-2 text-white/60 hover:text-white transition-colors"
            >
              <ChevronLeft className="w-6 h-6" />
            </Link>
          )}
        </div>

        {/* Center - Logo or Title */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2"
        >
          {title ? (
            <h1 className="text-xl font-bold text-white">{title}</h1>
          ) : (
            <>
              <div className="w-8 h-8 bg-gradient-to-br from-pink-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Heart className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-pink-500 to-purple-600 bg-clip-text text-transparent">
                CultureMatch
              </span>
            </>
          )}
        </motion.div>

        {/* Right side */}
        <div className="w-12 flex justify-end">
          {showSettings && (
            <Link
              href="/settings"
              className="p-2 -mr-2 text-white/60 hover:text-white transition-colors"
            >
              <Settings className="w-6 h-6" />
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
