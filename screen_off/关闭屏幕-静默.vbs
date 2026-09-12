' ============================================================
'  关闭屏幕-静默.vbs —— 双击后约 1 秒关屏，全程无黑窗口闪现
'  便携写法：只认"和自己放在同一个文件夹里的 关闭屏幕.exe"，
'           找不到 exe 时才退回用系统里的 pythonw 跑同目录的 py 源码。
'           里面没有任何本机专属路径，拷到别的电脑也能直接用。
' ============================================================
Option Explicit

Dim fso, sh, base, exePath, py
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

base    = fso.GetParentFolderName(WScript.ScriptFullName)
exePath = base & "\关闭屏幕.exe"
py      = base & "\screen_off.py"

If fso.FileExists(exePath) Then
    ' 首选：打包好的独立 exe（自带 Python，无需任何依赖）
    sh.Run """" & exePath & """", 0, False
ElseIf fso.FileExists(py) Then
    ' 兜底：本机已装 Python 时，用 pythonw 静默运行源码
    sh.Run "pythonw """ & py & """ --delay 2", 0, False
Else
    MsgBox "没找到 关闭屏幕.exe。" & vbCrLf & _
           "请把本文件和 关闭屏幕.exe 放在同一个文件夹里再双击。", 48, "关闭屏幕"
End If
