'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { ChevronRight, ChevronLeft, Sparkles, Loader2 } from 'lucide-react';
import { usersApi } from '@/lib/api';
import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';
import type { VibeQuestion, VibeAnswer } from '@/types';

const VIBE_QUESTIONS: VibeQuestion[] = [
  {
    id: 'subtitles',
    question: 'Subtitles on or off?',
    options: [
      { value: 'on', label: 'Always on', emoji: '📖' },
      { value: 'off', label: 'Never', emoji: '🎬' },
      { value: 'foreign', label: 'Only for foreign films', emoji: '🌍' },
    ],
  },
  {
    id: 'music_discovery',
    question: 'How do you discover new music?',
    options: [
      { value: 'algorithm', label: 'Algorithm knows me', emoji: '🤖' },
      { value: 'friends', label: 'Friends\' recommendations', emoji: '👥' },
      { value: 'deep_dive', label: 'I dig deep myself', emoji: '⛏️' },
      { value: 'radio', label: 'Radio / Playlists', emoji: '📻' },
    ],
  },
  {
    id: 'movie_night',
    question: 'Ideal movie night?',
    options: [
      { value: 'theater', label: 'Cinema experience', emoji: '🎭' },
      { value: 'couch', label: 'Couch + snacks', emoji: '🛋️' },
      { value: 'outdoor', label: 'Outdoor screening', emoji: '🌙' },
      { value: 'marathon', label: 'Movie marathon', emoji: '🍿' },
    ],
  },
  {
    id: 'concert_vibe',
    question: 'At a concert, you\'re...',
    options: [
      { value: 'front', label: 'Front row energy', emoji: '🔥' },
      { value: 'middle', label: 'Vibing in the middle', emoji: '🎵' },
      { value: 'back', label: 'Chilling in the back', emoji: '😎' },
      { value: 'vip', label: 'VIP section', emoji: '✨' },
    ],
  },
  {
    id: 'genre_mood',
    question: 'What genre matches your mood right now?',
    options: [
      { value: 'upbeat', label: 'Upbeat pop/dance', emoji: '💃' },
      { value: 'chill', label: 'Lo-fi / Chill', emoji: '🌊' },
      { value: 'intense', label: 'Rock / Metal', emoji: '🎸' },
      { value: 'nostalgic', label: 'Throwback classics', emoji: '📼' },
    ],
  },
  {
    id: 'rewatcher',
    question: 'Are you a rewatcher?',
    options: [
      { value: 'always', label: 'Comfort rewatches always', emoji: '🔄' },
      { value: 'sometimes', label: 'For the really good ones', emoji: '⭐' },
      { value: 'never', label: 'Too much to watch!', emoji: '📺' },
    ],
  },
  {
    id: 'soundtrack',
    question: 'Soundtracks: love \'em or skip \'em?',
    options: [
      { value: 'love', label: 'Playlist staples', emoji: '🎼' },
      { value: 'some', label: 'Only the iconic ones', emoji: '🎹' },
      { value: 'skip', label: 'I separate the art', emoji: '🚫' },
    ],
  },
];

export default function VibeCheckPage() {
  const router = useRouter();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<VibeAnswer[]>([]);

  const currentQuestion = VIBE_QUESTIONS[currentIndex];
  const isLastQuestion = currentIndex === VIBE_QUESTIONS.length - 1;
  const progress = ((currentIndex + 1) / VIBE_QUESTIONS.length) * 100;

  const { mutate: submitVibeCheck, isPending } = useMutation({
    mutationFn: async (vibeAnswers: VibeAnswer[]) => {
      const response = await usersApi.submitVibeCheck(vibeAnswers);
      return response.data;
    },
    onSuccess: () => {
      router.push('/discover');
    },
  });

  const handleSelect = (value: string) => {
    const newAnswer: VibeAnswer = {
      question_id: currentQuestion.id,
      answer: value,
    };

    const updatedAnswers = [
      ...answers.filter((a) => a.question_id !== currentQuestion.id),
      newAnswer,
    ];
    setAnswers(updatedAnswers);

    // Auto-advance after short delay
    setTimeout(() => {
      if (isLastQuestion) {
        submitVibeCheck(updatedAnswers);
      } else {
        setCurrentIndex((prev) => prev + 1);
      }
    }, 300);
  };

  const currentAnswer = answers.find((a) => a.question_id === currentQuestion.id)?.answer;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-gray-950 p-6">
      {/* Progress bar */}
      <div className="fixed top-0 left-0 right-0 h-1 bg-white/10">
        <motion.div
          className="h-full bg-gradient-to-r from-pink-500 to-purple-600"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
        />
      </div>

      <div className="max-w-lg mx-auto pt-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl mb-4">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Vibe Check</h1>
          <p className="text-white/60">
            Question {currentIndex + 1} of {VIBE_QUESTIONS.length}
          </p>
        </motion.div>

        {/* Question */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentQuestion.id}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            className="space-y-6"
          >
            <h2 className="text-2xl font-semibold text-white text-center">
              {currentQuestion.question}
            </h2>

            <div className="space-y-3">
              {currentQuestion.options.map((option) => (
                <motion.button
                  key={option.value}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleSelect(option.value)}
                  className={cn(
                    'w-full p-4 rounded-2xl text-left transition-all',
                    'border-2 flex items-center gap-4',
                    currentAnswer === option.value
                      ? 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 border-purple-500'
                      : 'bg-white/5 border-white/10 hover:border-white/20'
                  )}
                >
                  <span className="text-2xl">{option.emoji}</span>
                  <span className="text-white font-medium">{option.label}</span>
                </motion.button>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        <div className="flex justify-between mt-12">
          <Button
            variant="ghost"
            onClick={() => setCurrentIndex((prev) => prev - 1)}
            disabled={currentIndex === 0}
          >
            <ChevronLeft className="w-5 h-5 mr-1" />
            Back
          </Button>

          {isLastQuestion && currentAnswer && (
            <Button onClick={() => submitVibeCheck(answers)} disabled={isPending}>
              {isPending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  Finish
                  <ChevronRight className="w-5 h-5 ml-1" />
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
