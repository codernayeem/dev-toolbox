' ==============================================================================
' WSL Silent Background Launcher
' Starts the WSL instance silently in the background without opening a terminal window.
' ==============================================================================

Set WshShell = CreateObject("WScript.Shell")

' Change "Ubuntu" to your installed distribution name, or use "wsl.exe" to launch the default distribution.
' WindowStyle: 0 = Hidden, bWaitOnReturn: False = Do not wait for completion
WshShell.Run "wsl.exe -d Ubuntu", 0, False

Set WshShell = Nothing