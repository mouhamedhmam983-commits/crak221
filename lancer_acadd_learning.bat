@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo       ACADD Learning - Demarrage
echo ==========================================
echo.

python -c "import flask, flask_sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo Installation des dependances necessaires...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERREUR : impossible d'installer les dependances.
        echo Verifiez que Python est installe et accessible.
        pause
        exit /b 1
    )
)

echo L'application va demarrer.
echo Ouvrez http://127.0.0.1:5000 dans votre navigateur.
echo Pour arreter l'application, fermez cette fenetre ou appuyez sur Ctrl+C.
echo.

start "" http://127.0.0.1:5000
python acadd_learning_app.py

echo.
echo L'application s'est arretee. Consultez le message ci-dessus.
pause
