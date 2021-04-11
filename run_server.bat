@echo off

if not exist venv (
    echo "Virtual environment not found; creating one in 'venv'..."
    python -m venv venv
)

echo Activating venv...
call .\venv\Scripts\activate.bat

echo Synchronizing packages...
pip install -r requirements.txt

echo Running Music Server...
python src/main_server.py