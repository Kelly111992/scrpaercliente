@echo off
echo Starting G-Maps Lead Extractor...

:: Start Backend
start cmd /k "cd backend && venv\Scripts\activate && python main.py"

:: Start Frontend
start cmd /k "cd frontend && npm start"

echo Services are starting. Please open http://localhost:3000 in your browser.
pause
