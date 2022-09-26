@echo off

if not exist "res\musicReference.ods" (
    echo "musicReference.ods not found;"
    echo "Are you executing this script from the root of the repo?"
    exit 1
)

if not exist venv (
    echo "Virtual environment not found; creating one in 'venv'..."
    python -m venv venv
)

echo Activating venv...
call .\venv\Scripts\activate.bat

echo Synchronizing packages...
pip install -r requirements.txt

echo Running Music Server...
python src/main_server.py || pause