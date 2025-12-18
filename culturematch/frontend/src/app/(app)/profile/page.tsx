'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { 
  Loader2, Settings, LogOut, Music, Film, Sparkles, 
  Plus, Edit2, ExternalLink, Check
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { usersApi, spotifyApi, mediaApi } from '@/lib/api';
import { Button, Avatar, Modal, Input } from '@/components/ui';
import { MediaCard, MediaSearch } from '@/components/media';
import type { UserProfile, UserInteraction, MediaSearchResult } from '@/types';

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [isEditingBio, setIsEditingBio] = useState(false);
  const [bio, setBio] = useState('');
  const [showMediaModal, setShowMediaModal] = useState(false);
  const [mediaType, setMediaType] = useState<'movie' | 'artist'>('movie');

  // Fetch user profile with interactions
  const { data: profile, isLoading } = useQuery({
    queryKey: ['profile'],
    queryFn: async () => {
      const response = await usersApi.getProfile();
      return response.data as UserProfile;
    },
  });

  // Fetch interactions
  const { data: interactions } = useQuery({
    queryKey: ['interactions'],
    queryFn: async () => {
      const response = await usersApi.getInteractions({ interaction_type: 'top4' });
      return response.data as UserInteraction[];
    },
  });

  // Update profile mutation
  const { mutate: updateProfile } = useMutation({
    mutationFn: async (data: { bio?: string }) => {
      const response = await usersApi.updateProfile(data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profile'] });
      setIsEditingBio(false);
    },
  });

  // Add to top 4 mutation
  const { mutate: addToTop4 } = useMutation({
    mutationFn: async (item: MediaSearchResult) => {
      const mediaData: any = {
        external_id: item.id,
        media_type: mediaType,
        title: item.title || item.name || 'Unknown',
      };
      if (item.image_url) {
        mediaData.image_url = item.image_url;
      }
      console.log('Adding to top 4:', { mediaData, item });
      const response = await mediaApi.logInteraction({
        media: mediaData,
        interaction_type: 'top4',
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
      setShowMediaModal(false);
    },
    onError: (error: any) => {
      console.error('Error adding to top 4:', error);
      if (error.response?.data) {
        console.error('Response data:', error.response.data);
      }
    },
  });

  // Remove from top 4 mutation
  const { mutate: removeFromTop4 } = useMutation({
    mutationFn: async (interactionId: string) => {
      await mediaApi.removeInteraction(interactionId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
    },
  });

  // Connect Spotify
  const { mutate: connectSpotify } = useMutation({
    mutationFn: async () => {
      const response = await spotifyApi.getAuthUrl();
      window.location.href = response.data.auth_url;
    },
  });

  // Import from Spotify
  const { mutate: importSpotify, isPending: isImporting } = useMutation({
    mutationFn: async () => {
      const response = await spotifyApi.importTopItems();
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interactions'] });
    },
  });

  const topMovies = interactions?.filter((i) => i.media.media_type === 'movie') || [];
  const topArtists = interactions?.filter((i) => i.media.media_type === 'artist') || [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-purple-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="py-6 space-y-8">
      {/* Profile header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center"
      >
        <Avatar
          src={profile?.avatar_url}
          name={profile?.display_name || user?.email}
          size="xl"
          className="mx-auto mb-4"
        />
        <h1 className="text-2xl font-bold text-white">
          {profile?.display_name || 'Anonymous'}
        </h1>
        <p className="text-white/60">{user?.email}</p>

        {/* Bio */}
        <div className="mt-4">
          {isEditingBio ? (
            <div className="flex gap-2">
              <Input
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell us about yourself..."
                className="flex-1"
              />
              <Button
                size="sm"
                onClick={() => updateProfile({ bio })}
              >
                <Check className="w-4 h-4" />
              </Button>
            </div>
          ) : (
            <button
              onClick={() => {
                setBio(profile?.bio || '');
                setIsEditingBio(true);
              }}
              className="text-white/60 hover:text-white flex items-center gap-2 mx-auto"
            >
              {profile?.bio || 'Add a bio'}
              <Edit2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </motion.div>

      {/* Spotify connection */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="bg-gradient-to-r from-green-500/20 to-green-600/10 rounded-2xl p-4 border border-green-500/20"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500 rounded-xl flex items-center justify-center">
              <Music className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-white">Spotify</h3>
              <p className="text-sm text-white/60">
                {profile?.spotify_connected ? 'Connected' : 'Not connected'}
              </p>
            </div>
          </div>
          {profile?.spotify_connected ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => importSpotify()}
              disabled={isImporting}
            >
              {isImporting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  Import <ExternalLink className="w-4 h-4 ml-1" />
                </>
              )}
            </Button>
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => connectSpotify()}
            >
              Connect
            </Button>
          )}
        </div>
      </motion.div>

      {/* Top 4 Movies */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Film className="w-5 h-5 text-purple-400" />
            Top 4 Movies
          </h2>
          {topMovies.length < 4 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setMediaType('movie');
                setShowMediaModal(true);
              }}
            >
              <Plus className="w-4 h-4" />
            </Button>
          )}
        </div>
        <div className="grid grid-cols-4 gap-3">
          {topMovies.map((interaction) => (
            <MediaCard
              key={interaction.id}
              media={interaction.media}
              size="sm"
              onRemove={() => removeFromTop4(interaction.id)}
            />
          ))}
          {topMovies.length < 4 && (
            <button
              onClick={() => {
                setMediaType('movie');
                setShowMediaModal(true);
              }}
              className="aspect-[2/3] rounded-xl border-2 border-dashed border-white/20 flex items-center justify-center hover:border-purple-500/50 transition-colors"
            >
              <Plus className="w-6 h-6 text-white/40" />
            </button>
          )}
        </div>
      </motion.section>

      {/* Top 4 Artists */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Music className="w-5 h-5 text-pink-400" />
            Top 4 Artists
          </h2>
          {topArtists.length < 4 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setMediaType('artist');
                setShowMediaModal(true);
              }}
            >
              <Plus className="w-4 h-4" />
            </Button>
          )}
        </div>
        <div className="grid grid-cols-4 gap-3">
          {topArtists.map((interaction) => (
            <MediaCard
              key={interaction.id}
              media={interaction.media}
              size="sm"
              onRemove={() => removeFromTop4(interaction.id)}
            />
          ))}
          {topArtists.length < 4 && (
            <button
              onClick={() => {
                setMediaType('artist');
                setShowMediaModal(true);
              }}
              className="aspect-[2/3] rounded-xl border-2 border-dashed border-white/20 flex items-center justify-center hover:border-pink-500/50 transition-colors"
            >
              <Plus className="w-6 h-6 text-white/40" />
            </button>
          )}
        </div>
      </motion.section>

      {/* Vibe Check */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <a href="/onboarding/vibe-check">
          <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-2xl p-4 border border-purple-500/20 hover:border-purple-500/40 transition-colors">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-medium text-white">Vibe Check</h3>
                <p className="text-sm text-white/60">
                  {profile?.vibe_answers ? 'Update your answers' : 'Complete to improve matches'}
                </p>
              </div>
              <div className="text-white/40">→</div>
            </div>
          </div>
        </a>
      </motion.section>

      {/* Logout */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="pt-4"
      >
        <Button
          variant="ghost"
          className="w-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
          onClick={logout}
        >
          <LogOut className="w-5 h-5 mr-2" />
          Sign Out
        </Button>
      </motion.div>

      {/* Media Search Modal */}
      <Modal
        isOpen={showMediaModal}
        onClose={() => setShowMediaModal(false)}
        title={`Add ${mediaType === 'movie' ? 'Movie' : 'Artist'}`}
      >
        <MediaSearch
          mediaType={mediaType}
          onSelect={(item) => addToTop4(item)}
          placeholder={`Search ${mediaType}s...`}
        />
      </Modal>
    </div>
  );
}
