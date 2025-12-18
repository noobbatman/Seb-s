'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Heart, Film, Music, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui';

const steps = [
  {
    icon: Film,
    title: 'Add Your Top 4 Movies',
    description: 'Share your all-time favorites',
    color: 'from-purple-500 to-blue-500',
  },
  {
    icon: Music,
    title: 'Connect Spotify',
    description: 'Import your top artists automatically',
    color: 'from-green-500 to-emerald-500',
  },
  {
    icon: Sparkles,
    title: 'Take the Vibe Check',
    description: 'Quick questions about your taste',
    color: 'from-pink-500 to-purple-500',
  },
];

export default function OnboardingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-purple-950/20 to-gray-950 p-6 flex flex-col">
      <div className="flex-1 flex flex-col items-center justify-center max-w-lg mx-auto">
        {/* Welcome */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-pink-500 to-purple-600 rounded-2xl mb-4">
            <Heart className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Welcome to CultureMatch!</h1>
          <p className="text-white/60">Let&apos;s set up your profile in 3 easy steps</p>
        </motion.div>

        {/* Steps */}
        <div className="w-full space-y-4 mb-12">
          {steps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/10"
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center flex-shrink-0`}>
                <step.icon className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{step.title}</h3>
                <p className="text-sm text-white/60">{step.description}</p>
              </div>
              <div className="ml-auto text-white/30 text-lg font-bold">
                {index + 1}
              </div>
            </motion.div>
          ))}
        </div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="w-full"
        >
          <Button
            size="lg"
            className="w-full group"
            onClick={() => router.push('/onboarding/vibe-check')}
          >
            Let&apos;s Go
            <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
          </Button>

          <button
            onClick={() => router.push('/discover')}
            className="w-full mt-4 text-white/50 hover:text-white/80 text-sm transition-colors"
          >
            Skip for now
          </button>
        </motion.div>
      </div>
    </div>
  );
}
