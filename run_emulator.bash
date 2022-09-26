#! /bin/bash

if [ ! -f "res/musicReference.ods" ]; then
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
fi

LUA_PATH="$(pwd)/src/bizhawk_bindings.lua"
EMUHAWK_PATH_FILE="path_to_emuhawk.txt"

if [ -f "$EMUHAWK_PATH_FILE" ]; then
    PATH_TO_EMUHAWK=$(cat $EMUHAWK_PATH_FILE)
fi

while [ ! -z "$PATH_TO_EMUHAWK" ] && [ ! -f "$PATH_TO_EMUHAWK" ]; do
    echo "EmuHawk not found"
    read -p "Enter absolute path to Emuhawk: " PATH_TO_EMUHAWK
    echo "$PATH_TO_EMUHAWK" > "$EMUHAWK_PATH_FILE"
done

echo Trying to run Emuhawk from "$PATH_TO_EMUHAWK"...
"$PATH_TO_EMUHAWK" --socket_ip=127.0.0.1 --socket_port=19938 --lua="$LUA_PATH"
