' ============================================================
'  创建桌面快捷方式.vbs —— 双击运行一次即可
'  作用：在你的桌面生成「关闭屏幕」快捷方式，并把全局热键绑成 Ctrl+Alt+Q
'        （命令行加 quiet 参数则不弹提示窗，供脚本化调用）
' ============================================================
Option Explicit

Dim fso, sh, base, desk, lnkPath, lnk, exePath, quiet
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

quiet = False
If WScript.Arguments.Count > 0 Then
    If LCase(WScript.Arguments(0)) = "quiet" Then quiet = True
End If

base     = fso.GetParentFolderName(WScript.ScriptFullName)
exePath  = base & "\关闭屏幕.exe"
desk     = sh.SpecialFolders("Desktop")
lnkPath  = desk & "\关闭屏幕.lnk"

If Not fso.FileExists(exePath) Then
    If Not quiet Then MsgBox "没找到 关闭屏幕.exe，请确认本脚本和它放在同一个文件夹里。", 48, "提示"
    WScript.Quit 1
End If

Set lnk = sh.CreateShortcut(lnkPath)
lnk.TargetPath       = exePath
lnk.Arguments        = "--delay 1"
lnk.WorkingDirectory = base
lnk.Hotkey           = "CTRL+ALT+Q"
lnk.Description      = "只关显示器，不影响运行（全局热键 Ctrl+Alt+Q）"
' 图标：优先用 light 主题的独立 ico（命名独立，不受图标缓存影响），否则退回 exe 自带图标
If fso.FileExists(base & "\图标-light.ico") Then
    lnk.IconLocation = base & "\图标-light.ico,0"
ElseIf fso.FileExists(base & "\关闭屏幕.ico") Then
    lnk.IconLocation = base & "\关闭屏幕.ico,0"
Else
    lnk.IconLocation = exePath & ",0"
End If
lnk.Save

If Not quiet Then
    MsgBox "已在桌面创建快捷方式：关闭屏幕" & vbCrLf & _
           "全局热键：Ctrl+Alt+Q" & vbCrLf & vbCrLf & _
           "双击图标即可关屏（约 1 秒后黑屏）。", 64, "完成"
End If
