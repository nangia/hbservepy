
rem hbserve starter batch file


:loop
c:
cd \hbserve
processmsg.exe processmsg.cfg
rem in case an exit happens wait for some time and start again
timeout 10
goto :loop

