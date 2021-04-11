import os
import time
import math
from pathlib import Path
import wave
import pandas as pd
import pygame.mixer
from pydub import AudioSegment

project_root_path = Path(__file__).resolve().parents[1]
print(project_root_path)
music_dir_path = project_root_path.joinpath('res/tracks')
clip_dir_path = project_root_path.joinpath('res/clips')

MUSIC_LIBRARY_SILENCE_TRACK = 99

# TODO: remove pygame dependency for creating wav files; switch to PyDub instead?
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=4096)
pygame.init()


# TODO: make this more efficient / Use Pathlib?
def get_track_path(track_number):
    if track_number == MUSIC_LIBRARY_SILENCE_TRACK:
        return "silence"

    for root, dirs, files in os.walk(music_dir_path):
        for file in files:
            if file.startswith(str(track_number).zfill(2)) and (file.endswith('.mp3') or file.endswith('.wav')):
                audio_file_path = os.path.join(root, file)
                return audio_file_path
    raise FileNotFoundError(f'(MusicLibrary) no file for track {track_number}')


def write_sliced_clip_with_pydub(track_path, start_ms, end_ms, output_path):
    print(f'Slicing ({track_path}) between ({start_ms}, {end_ms}) -> ({output_path})')
    if track_path == 'silence':
        silence_duration = end_ms - start_ms
        # TODO: un-hardcode rates when migrating to PyDub
        slience_segment = AudioSegment.silent(duration=silence_duration).set_frame_rate(44100).set_sample_width(2)
        slience_segment.export(output_path, format="wav")
    else:
        raise Exception("Pydub Slice Actual Tracks TODO NYI")


def slice_clip_with_pygame(track_path, start_ms, end_ms):
    # Note: constructing the Sound from a file here causes pygame to skip the audio!
    # No clue why.  Don't call this while playing audio using the Pygame MusicPlayer.
    song = pygame.mixer.Sound(file=track_path)
    len_ms = song.get_length() * 1000
    samples = song.get_raw()

    # These are decimal values
    start_samples_percentage = start_ms / len_ms * len(samples)
    end_samples_percentage = end_ms / len_ms * len(samples)

    # Sanitize input
    if math.isnan(start_samples_percentage) or start_samples_percentage < 0:
        start_samples_percentage = 0
    if math.isnan(end_samples_percentage) or end_samples_percentage > len(samples):
        end_samples_percentage = len(samples)

    # Note: the shifts here are to round to the nearest even number
    # Since the samples are 16-bit, using an odd number here will mis-slice the samples
    start_samples = (int(start_samples_percentage) >> 1) << 1
    end_samples = (int(end_samples_percentage) >> 1) << 1

    print(f'start_ms={start_ms} | end_ms={end_ms} | len_ms={len_ms} | start_samples={start_samples} | end_samples={end_samples} | total_samples={len(samples)}')
    assert(start_samples < end_samples)
    assert (start_samples <= len(samples))
    assert (end_samples <= len(samples))
    sliced_samples = samples[int(start_samples):int(end_samples)]
    # Note: Constructing the Sound from a buffer here does NOT cause pygame to skip the audio, even when playing
    return pygame.mixer.Sound(buffer=sliced_samples)


class MusicLibrary:
    # f_create_handle_from_path(path_to_wav_file) -> [handle in the caller's preferred format]
    def __init__(self, f_create_handle_from_path, precache_clips):
        self.f_create_handle_from_path = f_create_handle_from_path
        music_reference_path = project_root_path.joinpath('res/musicReference.ods')
        music_df = pd.read_excel(music_reference_path)

        # Remove clips with no start or end specified
        music_df = music_df[music_df['clip_start_ms'].notnull()]
        music_df = music_df[music_df['clip_end_ms'].notnull()]

        # Remove songs without track mappings
        music_df = music_df[music_df['track_id'].notnull()]

        # Convert to ints
        music_df['clip_id'] = music_df['clip_id'].astype(str).apply(int, base=16)
        music_df['track_id'] = music_df['track_id'].astype(int)
        music_df['next_clip_id'] = music_df['next_clip_id'].fillna(0).astype(str).apply(int, base=16)

        print(f'Loading {len(music_df)} clips...')
        self.all_clip_metadata = {
            row['clip_id']:
            ClipMetadata(
                row['clip_id'],
                row['song_description'],
                get_track_path(row['track_id']),
                row['clip_start_ms'],
                row['clip_end_ms'],
                row['next_clip_id'],
                None
            ) for index, row in music_df.iterrows()
        }

        clip_dir_path.mkdir(parents=True, exist_ok=True)
        if precache_clips:
            print('MusicLibrary generating handles for all clips...')
            for clip_id, clip_meta in self.all_clip_metadata.items():
                clip_meta.clip_handle = self._get_handle_for_clip(clip_meta)
        else:
            print('MusicLibrary will generate handles when clip chains are requested')

    def get_metadata(self, clip_id):
        return self.all_clip_metadata.get(clip_id)

    def get_handle_from_metadata(self, clip_meta):
        if not clip_meta:
            return None

        if clip_meta.clip_handle:
            print(f"Returning memoed clip [{hex(clip_meta.clip_id)} : {clip_meta.description}]")
            return clip_meta.clip_handle

        tic = time.perf_counter()
        clip_meta.clip_handle = self._get_handle_for_clip(clip_meta)
        toc = time.perf_counter()
        print(f"Loaded clip for song [{hex(clip_meta.clip_id)} : {clip_meta.description}] in {toc - tic:0.4f} seconds")

        # Pre-load entire clip chain for this song to prevent loading while audio is playing
        # This is recursive until the end of the chain is loaded
        # The only reason this is here is to prevent skipping when using the Pygame music player
        # TODO: remove this if dropping pygame support
        self.get_handle_from_metadata(self.all_clip_metadata.get(clip_meta.next_clip_id))

        return clip_meta.clip_handle

    def _get_handle_for_clip(self, clip_meta):
        clip_filename = '{:02x}.wav'.format(clip_meta.clip_id)
        clip_path = clip_dir_path.joinpath(clip_filename)
        clip_path_str = str(clip_path)

        if not clip_path.exists():
            # TODO: remove if condition when migrating entirely to PyDub
            if clip_meta.track_path == 'silence':
                write_sliced_clip_with_pydub(clip_meta.track_path, clip_meta.start_ms, clip_meta.end_ms, clip_path_str)
            else:
                # Generate the file with pygame
                this_clip = slice_clip_with_pygame(clip_meta.track_path, clip_meta.start_ms, clip_meta.end_ms)

                # open new wave file
                clip_wav_file = wave.open(clip_path_str, 'wb')

                # set the parameters
                # TODO: un-hardcode this?
                clip_wav_file.setframerate(44100)
                clip_wav_file.setnchannels(2)
                clip_wav_file.setsampwidth(2)

                # write raw PyGame sound buffer to wave file
                clip_wav_file.writeframesraw(this_clip.get_raw())

                # Hint to Python to evict this from RAM to avoid taking up all of the system's resources
                del this_clip
            print(f'Created missing wav file {clip_path_str} ({clip_meta.description})...')

        return self.f_create_handle_from_path(clip_path_str)


class ClipMetadata:
    def __init__(self, clip, desc, path, start, end, following, handle):
        self.clip_id = clip  # Song ID or PseudoSong ID
        self.description = desc  # Human-readable name/description of the clip
        self.track_path = path  # Path to 2N audio file
        self.start_ms = start  # time clip starts in file (milliseconds)
        self.end_ms = end  # time clip ends in file (milliseconds)
        self.next_clip_id = following  # Clip that's played after this one
        self.clip_handle = handle  # Player-dependent
