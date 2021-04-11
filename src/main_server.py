import socket
import sys
from threading import Thread
import traceback
import select
from enum import Enum

from soloud_music_player import MusicPlayer
from music_player_constants import *

# Server code adapted from http://danielhnyk.cz/simple-server-client-aplication-python-3/

GBC_STOP_MUSIC_PAYLOAD = bytes([PSEUDOSONG_STOP_MUSIC])
LADX_MINIMUM_VOLUME = 0x0
LADX_MAXIMUM_VOLUME = 0x7


class MusicSpeed(Enum):
    NORMAL_SPEED = 0
    DOUBLE_SPEED = 1
    HALF_SPEED = 2


def send_music_payload(payload, conn):
    conn.send(payload)
    print(f'SEND: {payload}')


def handle_music_change(song_id, conn):
    if song_id != PSEUDOSONG_DO_NOTHING:
        if song_id != PSEUDOSONG_STOP_MUSIC:
            send_music_payload(GBC_STOP_MUSIC_PAYLOAD, conn)  # Silence GBC as fast as possible

        print(f'Handle Music Changed: song {hex(song_id)}')
        if song_id == 0x01:
            # Do not attempt to play Title after Shipwreck (0x01) as the player will handle it
            pass
        elif not player.play_music(song_id):
            # We can't handle this music, so play on GBC:
            original_song_payload = bytes([song_id])
            send_music_payload(original_song_payload, conn)
            print(f'NO MUSIC for song {hex(song_id)}; playing on GBC...')


def normalize_ladx_timing(ladx_timing):
    speed = MusicSpeed(ladx_timing)
    if speed == MusicSpeed.NORMAL_SPEED:
        return 1.0
    elif speed == MusicSpeed.HALF_SPEED:
        return 0.5
    elif speed == MusicSpeed.DOUBLE_SPEED:
        return 2.0


def normalize_ladx_volume(ladx_volume_nybble):
    ladx_clamped_volume = max(LADX_MINIMUM_VOLUME, min(ladx_volume_nybble, LADX_MAXIMUM_VOLUME))
    return ladx_clamped_volume / LADX_MAXIMUM_VOLUME


def handle_client_event(event, value, conn):
    if 's' == event:  # Song Update
        handle_music_change(value, conn)
    elif 't' == event:  # Timing Update
        player.set_speed(normalize_ladx_timing(value))
    elif 'l' == event:  # Left Channel Volume Update
        player.set_left_volume(normalize_ladx_volume(value))
    elif 'r' == event:  # Right Channel Volume Update
        player.set_right_volume(normalize_ladx_volume(value))
    else:
        print(f'Warning: No handler for payload type {event}')


def auto_music_thread(conn, ip, port):
    print(f'Created thread to handle socket {ip}:{port} - waiting for data...')

    while conn:
        # Blocks until data is ready
        readable, writable, exceptional = select.select([conn], [], [])

        if readable:
            try:
                client_payload = conn.recv(2)
            except ConnectionResetError:
                break

            # TODO: check payload size?
            print(f'RECV: {client_payload}')
            handle_client_event(chr(client_payload[0]), client_payload[1], conn)

    print(f'Connection {ip}:{port} closed')
    player.stop_music()


def start_server(listen_ip, listen_port):
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this is for easy starting/killing the app
    soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print('Socket created')

    try:
        soc.bind((listen_ip, listen_port))
        print('Socket bind complete')
    except socket.error as msg:
        print('Bind failed. Error : ' + str(sys.exc_info()))
        sys.exit()

    # Start listening on socket
    soc.listen(1)
    print(f'Socket now listening on {listen_ip}:{listen_port}')

    while True:
        conn, addr = soc.accept()
        ip, port = str(addr[0]), str(addr[1])
        print('Accepting connection from ' + ip + ':' + port)
        try:
            Thread(target=auto_music_thread, args=(conn, ip, port)).start()
        except:
            print("Terrible error!")
            traceback.print_exc()
            break

    soc.close()


def manual_music_thread(conn, ip, port):
    while conn:
        user_input = input('Gimme song:')
        try:
            song_id = int(user_input, 16)
            song_payload = bytes([song_id])
            conn.send(song_payload)
        except ValueError:
            print('Parse error')

    print (f'Connection to {ip}:{port} closed')


if __name__ == "__main__":
    # All threads share the same music player
    # No reason to play two songs at once
    # Allows restarting client application without restarting this server
    player = MusicPlayer(True)
    start_server(listen_ip='127.0.0.1', listen_port=19938)
