@echo off

set LUA_PATH=%CD%\src\bizhawk_bindings.lua

"path/to/Emuhawk.exe" --socket_ip=127.0.0.1 --socket_port=19938 --lua="%LUA_PATH%"