@echo off


if not exist "res\musicReference.ods" (
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
)

set LUA_PATH=%CD%\src\bizhawk_bindings.lua

echo Trying to run Emuhawk...
"path/to/Emuhawk.exe" --socket_ip=127.0.0.1 --socket_port=19938 --lua="%LUA_PATH%" || pause