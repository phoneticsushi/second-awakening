import socket
import sys
from threading import Thread
import traceback
import select
from enum import Enum

from soloud_music_player import MusicPlayer
from music_player_constants import *

# Server code adapted from http://danielhnyk.cz/simple-server-client-aplication-python-3/

LADX_MINIMUM_VOLUME = 0x0
LADX_MAXIMUM_VOLUME = 0x7


class MusicSpeed(Enum):
    NORMAL_SPEED = 0
    DOUBLE_SPEED = 1
    HALF_SPEED = 2


def send_music_payload_bizhawk(song_id: int, conn):
    """
    Sends a music payload in Bizhawk's 

    BizHawk format for socket conections is:
    '[payload_length] [payload]' - note the space!
    Only ASCII text is accepted, i.e. each byte must be <= 0x7F
    """
    bizhawk_payload = bytes([0x31, 0x20, song_id])  # '1', 'space', song_id
    conn.send(bizhawk_payload)
    print(f'SEND: {bizhawk_payload}')


def handle_music_change(song_id: int, conn):
    """
    BizHawk blocks when trying to read the socket,
    so the LUA script is set to poll only when submitting a music change.
    
    This function must reply to the client exactly once
    for each time it's called
    """
    if song_id in [PSEUDOSONG_DO_NOTHING, PSEUDOSONG_STOP_MUSIC]:
        send_music_payload_bizhawk(song_id, conn)
    else:
        print(f'Handle Music Changed: song {hex(song_id)}')
        if song_id == 0x01:
            # Do not attempt to play Title after Shipwreck (0x01) as the player will handle it
            send_music_payload_bizhawk(PSEUDOSONG_STOP_MUSIC, conn)
        elif player.play_music(song_id):
            # We can handle this music, so silence the GBC
            send_music_payload_bizhawk(PSEUDOSONG_STOP_MUSIC, conn)
        else:
            # We can't handle this music, so play on GBC:
            send_music_payload_bizhawk(song_id, conn)
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
                # The client will always send two bytes,
                # resulting in a four-byte payload from BizHawk.
                # The format is:
                # '2', space, event, value
                client_payload = conn.recv(4)
            except ConnectionResetError:
                break

            print(f'RECV: {client_payload}')
            if 0 == len(client_payload):
                # Connection is closed
                break
            # Read only the event and value
            handle_client_event(chr(client_payload[2]), client_payload[3], conn)

    print(f'Connection from {ip}:{port} is closed')
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
