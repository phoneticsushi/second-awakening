#! /bin/bash

if [ ! -f "res/musicReference.ods" ]; then
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
fi

LUA_PATH="$(pwd)/src/bizhawk_bindings.lua"
EMUHAWK_LINK_NAME="link_to_emuhawk"

if [ ! -f "$EMUHAWK_LINK_NAME" ]; then
    read -p "Enter path to Emuhawk.exe: " PATH_TO_EMUHAWK
    ln "$PATH_TO_EMUHAWK" "$EMUHAWK_LINK_NAME"
fi

echo Trying to run Emuhawk...
"./$EMUHAWK_LINK_NAME" --socket_ip=127.0.0.1 --socket_port=19938 --lua="$LUA_PATH"
