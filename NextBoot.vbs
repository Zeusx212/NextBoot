' NextBoot Silent Launcher (Launches GUI without command prompt window)
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
strCfgPath = strScriptDir & "\python_path.cfg"
strPython = ""

' Check python_path.cfg
If objFSO.FileExists(strCfgPath) Then
    Set objFile = objFSO.OpenTextFile(strCfgPath, 1)
    If Not objFile.AtEndOfStream Then
        strPython = Trim(objFile.ReadLine)
    End If
    objFile.Close
End If

' Fallback search if cfg not found
If strPython = "" Or Not objFSO.FileExists(strPython) Then
    strUserProf = objShell.ExpandEnvironmentStrings("%USERPROFILE%")
    strCandidate = strUserProf & "\AppData\Local\Programs\Python\Python311\python.exe"
    If objFSO.FileExists(strCandidate) Then
        strPython = strCandidate
    Else
        strPython = "python.exe"
    End If
End If

' Use pythonw.exe if available to avoid any console window
strPythonW = Replace(strPython, "python.exe", "pythonw.exe")
If objFSO.FileExists(strPythonW) Then
    strExe = strPythonW
Else
    strExe = strPython
End If

strMainPy = strScriptDir & "\main.py"
' Run with runas or normal (main.py will elevate via UAC if not admin)
objShell.Run """" & strExe & """ """ & strMainPy & """", 1, False
