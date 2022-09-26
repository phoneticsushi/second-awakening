@echo off


if not exist "res\musicReference.ods" (
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
)

set LUA_PATH=%CD%\src\bizhawk_bindings.lua
set EMUHAWK_LINK_NAME="link_to_emuhawk"

if not exist "$EMUHAWK_LINK_NAME" (
    set /p PATH_TO_EMUHAWK=Enter path to Emuhawk.exe:
    mklink "$EMUHAWK_LINK_NAME" "$PATH_TO_EMUHAWK"
)

echo Trying to run Emuhawk...
"$EMUHAWK_LINK_NAME" --socket_ip=127.0.0.1 --socket_port=19938 --lua="%LUA_PATH%" || pause
