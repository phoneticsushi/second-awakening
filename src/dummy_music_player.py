class MusicPlayer:
    def __init__(self):
        print('Initialized Dummy MusicPlayer')

    def play_music(self, song_id):
        print(f'Dummy MusicPlayer: play_music {hex(song_id)}')
        return False

    def set_speed(self, speed_ratio):
        print(f'Dummy MusicPlayer: set_speed {speed_ratio}')

    def set_left_volume(self, volume):
        print(f'Dummy MusicPlayer: set_left_volume {volume}')

    def set_right_volume(self, volume):
        print(f'Dummy MusicPlayer: set_right_volume {volume}')

    def stop_music(self):
        print('Dummy MusicPlayer: stop_music')


if __name__ == "__main__":
    player = MusicPlayer()
    player.play_music(0x61)  # Does nothing