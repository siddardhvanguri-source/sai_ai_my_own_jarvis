' Sai Background Assistant Runner
' Runs Sai in the background without a command prompt window, waiting for "Hey Sai" or 'Home' key.
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\saisi\my-agent\fullstack-agent"
WshShell.Run "cmd /c start.bat voice", 0, False

