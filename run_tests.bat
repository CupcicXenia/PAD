@echo off
echo === RUNNING UNIT TESTS ===

set PASSED=0
set FAILED=0

echo.
echo Testing Hotel Search Service...
cd services\hotel-search-service
python test_app.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Hotel Search Service tests passed
    set /a PASSED+=1
) else (
    echo [FAIL] Hotel Search Service tests failed
    set /a FAILED+=1
)
cd ..\..

echo.
echo Testing Frontend Service...
cd services\frontend-service
python test_app.py
if %ERRORLEVEL% EQU 0 (
    echo [OK] Frontend Service tests passed
    set /a PASSED+=1
) else (
    echo [FAIL] Frontend Service tests failed
    set /a FAILED+=1
)
cd ..\..

echo.
echo === TEST SUMMARY ===
echo Passed: %PASSED%
echo Failed: %FAILED%

if %FAILED% EQU 0 (
    echo.
    echo All tests passed!
    exit /b 0
) else (
    echo.
    echo Some tests failed!
    exit /b 1
)

