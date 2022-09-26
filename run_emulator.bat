@echo off


if not exist "res\musicReference.ods" (
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
)

set LUA_PATH=%CD%\src\bizhawk_bindings.lua
set EMUHAWK_PATH_FILE=path_to_emuhawk.txt

if exist "$EMUHAWK_PATH_FILE" (
    set /p PATH_TO_EMUHAWK=<"$EMUHAWK_PATH_FILE"
)

:find_emuhawk_loop
if defined PATH_TO_EMUHAWK if not exist "$PATH_TO_EMUHAWK" (
    echo "EmuHawk not found"
    set /p PATH_TO_EMUHAWK=Enter absolute path to Emuhawk: 
    echo "$PATH_TO_EMUHAWK" > "$EMUHAWK_PATH_FILE"
    goto find_emuhawk_loop
)

echo Trying to run Emuhawk...
"$EMUHAWK_LINK_NAME" --socket_ip=127.0.0.1 --socket_port=19938 --lua="%LUA_PATH%" || pause
