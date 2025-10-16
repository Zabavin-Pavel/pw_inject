; hotkeys.ahk - ИСПРАВЛЕНО: проверены все скобки
#NoTrayIcon
#SingleInstance Force
#NoEnv
#Persistent
SetControlDelay -1
SetBatchLines -1

; Получаем путь к command_file из аргументов командной строки
if A_Args[1]
    command_file := A_Args[1]
else
    command_file := A_ScriptDir . "\ahk_command.txt"

; === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

GetWindowByPID(target_pid) {
    WinGet, id, list, ahk_class ElementClient Window
    Loop, %id% {
        this_id := id%A_Index%
        WinGet, window_pid, PID, ahk_id %this_id%
        
        if (window_pid = target_pid)
            return this_id
    }
    return 0
}

; === ОСНОВНЫЕ ФУНКЦИИ ===

SendKeyToPIDs(key, pids_string) {
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "")
            continue
        
        hwnd := GetWindowByPID(target_pid)
        if (hwnd) {
            CoordMode, Mouse, Screen
            ControlClick, x140 y120, ahk_id %hwnd%, , L, NA
            ControlSend, , {%key%}, ahk_id %hwnd%
        }
    }
}

ClickToPIDs(x, y, pids_string) {
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "")
            continue
        
        hwnd := GetWindowByPID(target_pid)
        if (hwnd) {
            CoordMode, Mouse, Screen
            ControlClick, x%x% y%y%, ahk_id %hwnd%, , L, NA
        }
    }
}

Headhunter(pid) {
    
    hwnd := GetWindowByPID(pid)
    
    
    if (!hwnd) {
        asd
        return
    }
    
    ; ControlSend, , {Tab}, ahk_id %hwnd%
    ; Sleep, 50
    
    CoordMode, Mouse, Screen
    ControlClick, x50 y50, ahk_id %hwnd%, , L, NA
}

FollowLider(pids_string) {
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "")
            continue
        
        hwnd := GetWindowByPID(target_pid)
        if (!hwnd)
            continue
        
        CoordMode, Mouse, Screen
        ControlClick, x100 y100, ahk_id %hwnd%, , L, NA
        Sleep, 50
        ControlClick, x100 y100, ahk_id %hwnd%, , R, NA
    }
}

; === ОБРАБОТКА КОМАНД ===

CheckCommand:
    if FileExist(command_file) {
        FileRead, command, %command_file%
        FileDelete, %command_file%
        
        FileAppend, === COMMAND: [%command%]`n, C:\ahk_debug.txt
        
        if (command = "") {
            FileAppend, Command is EMPTY`n, C:\ahk_debug.txt
            return
        }
        
        if (command = "EXIT") {
            FileAppend, EXIT received`n, C:\ahk_debug.txt
            ExitApp
        }
        
        if (InStr(command, "CLICK:") = 1) {
            FileAppend, CLICK detected`n, C:\ahk_debug.txt
            parts := StrSplit(command, ":")
            parts_count := parts.MaxIndex()
            if (parts_count >= 4) {
                x := parts[2]
                y := parts[3]
                pids := parts[4]
                ClickToPIDs(x, y, pids)
            }
            return
        }
        
        if (InStr(command, "HEADHUNTER:") = 1) {
            FileAppend, HEADHUNTER detected`n, C:\ahk_debug.txt
            parts := StrSplit(command, ":")
            parts_count := parts.MaxIndex()
            FileAppend, Parts count: %parts_count%`n, C:\ahk_debug.txt
            if (parts_count = 2) {
                pid := parts[2]
                FileAppend, Calling Headhunter with PID: %pid%`n, C:\ahk_debug.txt
                Headhunter(pid)
            } else {
                FileAppend, ERROR: Wrong parts count`n, C:\ahk_debug.txt
            }
            return
        }
        
        if (InStr(command, "FOLLOW_LIDER:") = 1) {
            FileAppend, FOLLOW_LIDER detected`n, C:\ahk_debug.txt
            parts := StrSplit(command, ":")
            parts_count := parts.MaxIndex()
            if (parts_count = 2) {
                pids := parts[2]
                FollowLider(pids)
            }
            return
        }
        
        if (InStr(command, "KEY:") = 1) {
            FileAppend, KEY detected`n, C:\ahk_debug.txt
            parts := StrSplit(command, ":")
            parts_count := parts.MaxIndex()
            if (parts_count >= 3) {
                key := parts[2]
                pids := parts[3]
                SendKeyToPIDs(key, pids)
            }
            return
        }
        
        FileAppend, UNKNOWN command`n, C:\ahk_debug.txt
    }
return

; === ИНИЦИАЛИЗАЦИЯ ===
if FileExist(command_file)
    FileDelete, %command_file%

SetTimer, CheckCommand, 50
return