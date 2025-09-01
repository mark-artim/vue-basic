@echo off
echo Setting up Ship54 integration...
echo.

cd auth-backend

echo Running Ship54 setup script...
node scripts/setupShip54Complete.js

echo.
echo Running verification test...
node scripts/testShip54Setup.js

echo.
echo Setup complete! Press any key to exit.
pause