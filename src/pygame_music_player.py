from threading import Thread
import pygame.mixer
from pygame.locals import USEREVENT
from music_library_ms import MusicLibrary
from music_player_constants import *


def create_pygame_handle(path_to_wav_file):
    # Handles are the paths themselves
    return path_to_wav_file


class MusicPlayer:
    def __init__(self, precache_clips):
        self.precached = True  # Different kind of precaching than MusicLibrary's precaching
        self.CLIP_FINISHED_EVENT = pygame.locals.USEREVENT + 1
        self.music_library = MusicLibrary(create_pygame_handle, precache_clips)

        if self.precached:
            # Use pygame Music, to play file paths:
            pygame.mixer.set_num_channels(0)
            self.player_impl = pygame.mixer.music
        else:
            # Use pygame Channel, to play Sound objects:
            pygame.mixer.set_num_channels(1)
            self.player_impl = pygame.mixer.Channel(0)

        # TODO: when implementing volume, use this - values from 0 to 1
        # self.player_impl.set_volume(1)

        self.player_impl.set_endevent(self.CLIP_FINISHED_EVENT)

        self.last_played_song_id = None
        self.next_clip_id_to_queue = None
        self.egg = 0x00
        Thread(target=self._poll_music_update_routine).start()

    def play_music(self, song_id):
        if song_id == PSEUDOSONG_DO_NOTHING:
            return True  # Success; this case is a noop

        self.stop_music()
        if song_id == PSEUDOSONG_STOP_MUSIC:
            return True  # Success; music is stopped

        if song_id == 0x4A:
            song_id ^= self.egg
            self.egg ^= 0xC0

        metadata_to_play = self.music_library.get_metadata(song_id)
        if not metadata_to_play:
            print(f'Warning: missing mapping for song ID {hex(song_id)}')
            return False  # Failure; missing the requested song

        clip_to_play = self.music_library.get_handle_from_metadata(metadata_to_play)
        if not clip_to_play:
            print(f'Warning: clip for song ID {hex(song_id)} is unavailable')
            return False

        if self.precached:
            self.player_impl.load(clip_to_play)
            self.player_impl.play(fade_ms=200)
        else:
            self.player_impl.play(clip_to_play, fade_ms=200)
        print(f"Played clip ({hex(metadata_to_play.clip_id)}) : ({metadata_to_play.description})")

        # Note: Picking up the Stick should return to Overworld Theme, not Monkeys Build a Bridge (0x36)
        # This is easiest since we don't maintain the game's music map or even know where the player is
        # This will fail gracefully if you load a save state right before giving Kiki the bananas,
        # But that one's on you
        # TODO: does this work correctly?
        if metadata_to_play.clip_id == 0x4E:  # Fanfare when getting Marin (0x4E) should be followed by silence
            print('Sitting on Beach with Marin; clearing last played song')
            self.last_played_song_id = PSEUDOSONG_STOP_MUSIC
        elif metadata_to_play.next_clip_id != PSEUDOSONG_PREVIOUS_SONG and metadata_to_play.clip_id not in SONGS_TO_IGNORE_AS_PREVIOUS:
            self.last_played_song_id = metadata_to_play.clip_id

        self.next_clip_id_to_queue = metadata_to_play.next_clip_id
        self._queue_next_clip()

        return True  # Success; music is playing

    def stop_music(self):
        # We need to make sure that pygame sends no event in this case
        # since we rely on the presence of a SOUND_FINISHED_EVENT
        # to know when to queue the next song. If we don't do this,
        # pygame sends the endevent even when playback is stopped manually
        # and the event thread queues an extra song unnecessarily
        self.player_impl.set_endevent()
        self.player_impl.fadeout(200)
        self.player_impl.set_endevent(self.CLIP_FINISHED_EVENT)

    def set_speed(self, speed_ratio):
        print(f'Warning: Pygame MusicPlayer does not support changing the playback speed (Unsupported by Pygame)')

    def set_left_volume(self, volume):
        print(f'Warning: Pygame MusicPlayer does not support changing the volume (NYI)')

    def set_right_volume(self, volume):
        print(f'Warning: Pygame MusicPlayer does not support changing the volume (NYI)')

    def _queue_next_clip(self):
        if self.next_clip_id_to_queue == PSEUDOSONG_PREVIOUS_SONG:
            print(f'Previous song plays after this track; queueing clip of previous song')
            self.next_clip_id_to_queue = self.last_played_song_id
            # Deliberate fallthrough

        if not self.next_clip_id_to_queue:
            print('Warning: Queue routine called but next_clip_id_to_queue is empty')
            return False

        if self.next_clip_id_to_queue == PSEUDOSONG_STOP_MUSIC:
            print('No music plays after this track; skipping Queue routine')
            return True

        metadata_to_queue = self.music_library.get_metadata(self.next_clip_id_to_queue)
        handle = self.music_library.get_handle_from_metadata(metadata_to_queue)
        if not handle:
            print(f'Warning: clip for song ID {hex(self.next_clip_id_to_queue)} is unavailable')
            return False

        self.player_impl.queue(handle)
        print(f"Queued clip ({hex(metadata_to_queue.clip_id)}) : ({metadata_to_queue.description})")

        self.next_clip_id_to_queue = metadata_to_queue.next_clip_id
        return True

    def _poll_music_update_routine(self):
        print('MusicPlayer Polling Routine Started')
        while True:
            event = pygame.event.wait()
            if event.type == self.CLIP_FINISHED_EVENT:
                print(f'Pygame finished playing clip')
                self._queue_next_clip()
            elif event.type == pygame.QUIT:
                print('Error: Pygame broadcast quit event for some reason')
                raise SystemExit


if __name__ == "__main__":
    player = MusicPlayer(False)
    player.play_music(0x61)
    while True:
        user_input = input('Gimme song:')
        try:
            song_id = int(user_input, 16)
            player.play_music(song_id)
        except ValueError:
            print('Parse error')
