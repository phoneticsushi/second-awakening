#! /bin/bash

if [ ! -f "res/musicReference.ods" ]; then
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
fi

if [ $(which python) ]; then
    PYTHON_EXECUTABLE="python"
elif [ $(which python3) ]; then
    PYTHON_EXECUTABLE="python3"
else
    echo "Could not determine that python is installed on the system"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Virtual environment not found; creating one in 'venv'..."
    "$PYTHON_EXECUTABLE" -m venv venv
fi

echo Activating venv...
source "./venv/bin/activate"

echo Synchronizing packages...
pip install -r requirements.txt

echo Downloading tracks...
youtube-dl -o "res/tracks/%(playlist_index)s - %(title)s - %(id)s.%(ext)s" --no-overwrite --download-archive "res/tracks/download_archive.txt" https://soundcloud.com/jeremiah-sun/sets/link-awakening-orchestral-arrangement

echo Running Music Server...
"$PYTHON_EXECUTABLE" src/main_server.py