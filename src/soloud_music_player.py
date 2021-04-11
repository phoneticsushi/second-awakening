import time
from threading import Thread
from soloud import soloud
from music_library_ms import MusicLibrary
from music_player_constants import *


def create_soloud_handle(path_to_wav_file):
    wav_stream = soloud.WavStream()
    wav_stream.load(path_to_wav_file)
    return wav_stream


class MusicPlayer:
    def __init__(self, precache_clips):
        # Set up Soloud
        self.audiolib = soloud.Soloud()
        # TODO: change cargo-culted defaults?
        self.audiolib.init(self.audiolib.CLIP_ROUNDOFF | self.audiolib.ENABLE_VISUALIZATION)
        self.audiolib.set_global_volume(1)

        self.music_library = MusicLibrary(create_soloud_handle, precache_clips)

        self.active_channel = None

        self.sl_queue = soloud.Queue()
        self.sl_queue.set_params(44100, 2)

        self.left_volume = 1.0
        self.right_volume = 1.0
        self.speed_ratio = 1

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

        handle_to_play = self.music_library.get_handle_from_metadata(metadata_to_play)
        if not handle_to_play:
            print(f'Warning: clip for song ID {hex(song_id)} is unavailable')
            return False

        self.active_channel = self.audiolib.play_background(self.sl_queue)
        self.audiolib.set_relative_play_speed(self.active_channel, self.speed_ratio)
        self.sl_queue.play(handle_to_play)
        print(f"Played clip ({hex(metadata_to_play.clip_id)}) : ({metadata_to_play.description}) on Soloud channel {self.active_channel}")

        # Note: Some fanfares should return to the previous area theme, not the cutscene song that preceded them.
        # Since we don't maintain the game's music map or even know where the player is,
        # we maintain the SONGS_TO_IGNORE_AS_PREVIOUS list to get the desired effect.
        # If you load a save state immediately before giving Kiki the bananas, for example,
        # this will end up playing the wrong song, but that one's on you.
        if metadata_to_play.clip_id == 0x4E:  # Fanfare when getting Marin (0x4E) should be followed by silence
            print('Sitting on Beach with Marin; clearing last played song')
            self.last_played_song_id = PSEUDOSONG_STOP_MUSIC
        elif metadata_to_play.next_clip_id != PSEUDOSONG_PREVIOUS_SONG and metadata_to_play.clip_id not in SONGS_TO_IGNORE_AS_PREVIOUS:
            self.last_played_song_id = metadata_to_play.clip_id

        self.next_clip_id_to_queue = metadata_to_play.next_clip_id
        self._queue_next_clip()

        return True  # Success; music is playing

    def stop_music(self):
        self.active_channel = None  # To prevent contention if music update routine fires while we're stopping the music
        self.sl_queue.stop()
        # Hack: the Soloud API doesn't provide a way to clear the queue, so we just create a new one
        self.sl_queue.destroy()
        self.sl_queue = soloud.Queue()
        self.sl_queue.set_params(44100, 2)

    def set_speed(self, speed_ratio):
        # print(f'DEBUG: SET SPEED, old={self.speed_ratio} new={speed_ratio}')
        if speed_ratio != self.speed_ratio:
            self.speed_ratio = speed_ratio
            if self.active_channel:
                self.audiolib.set_relative_play_speed(self.active_channel, self.speed_ratio)

    def set_left_volume(self, volume):
        self.left_volume = volume
        self._apply_volume()

    def set_right_volume(self, volume):
        self.right_volume = volume
        self._apply_volume()

    # Haven't yet figured out how to set volume on the left and right channels separately,
    # though the effect would probably be worse than what we're doing here,
    # which is to just average the two volumes
    def _apply_volume(self):
        avg_volume = (self.left_volume + self.right_volume) / 2
        # TODO: probably cleaner not to use global, but setting volume on self.slqueue has no noticeable effect
        self.audiolib.set_global_volume(avg_volume)

    def _queue_next_clip(self):
        if not self.active_channel:
            print('Warning: _queue_next_clip() called but no channel is active')
            return False

        if self.next_clip_id_to_queue == PSEUDOSONG_PREVIOUS_SONG:
            print(f'Previous song plays after this track; queueing clip of previous song {hex(self.last_played_song_id)}')
            self.next_clip_id_to_queue = self.last_played_song_id
            # Deliberate fallthrough

        if not self.next_clip_id_to_queue:
            print('Warning: Queue routine called but next_clip_id_to_queue is empty')
            return False

        if self.next_clip_id_to_queue == PSEUDOSONG_STOP_MUSIC:
            # Skip queue routine as no music should play after this clip
            return True

        metadata_to_queue = self.music_library.get_metadata(self.next_clip_id_to_queue)
        handle = self.music_library.get_handle_from_metadata(metadata_to_queue)
        if not handle:
            print(f'Warning: clip for song ID {hex(self.next_clip_id_to_queue)} is unavailable')
            return False

        self.sl_queue.play(handle)
        print(f"Queued clip ({hex(metadata_to_queue.clip_id)}) : ({metadata_to_queue.description})")

        self.next_clip_id_to_queue = metadata_to_queue.next_clip_id
        return True

    def _poll_music_update_routine(self):
        print('MusicPlayer Polling Routine Started')
        while True:
            #print(f'DEBUG: active channel is {self.active_channel}')
            if self.active_channel:
                queued = self.sl_queue.get_queue_count()
                if queued == 0:
                    self.active_channel = None  # Cleanup from song end
                elif queued == 1:
                    self._queue_next_clip()
                # elif queued == 2:
                #     print('DEBUG: skipping queue as 2 clips already queued')
                elif queued > 2:
                    print(f'Warning: expected queued clips <= 2, got {queued}')
            time.sleep(1)  # Non-busy Wait TODO: is there some way to be notified when a clip finishes?


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
