; hotkeys.ahk - ОБНОВЛЕНО: все функции ожидают PID в аргументах
#NoTrayIcon
#SingleInstance Force
#NoEnv
#Persistent
SetControlDelay -1
SetBatchLines -1

; Получаем путь к command_file из аргументов командной строки
if (A_Args.Length() > 0) {
    command_file := A_Args[1]
} else {
    command_file := A_ScriptDir . "\ahk_command.txt"
}

; === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

GetWindowByPID(target_pid) {
    ; Найти HWND окна по PID
    WinGet, id, list, ahk_class ElementClient Window
    Loop, %id% {
        this_id := id%A_Index%
        WinGet, window_pid, PID, ahk_id %this_id%
        
        if (window_pid = target_pid) {
            return this_id
        }
    }
    return 0
}

; === ОСНОВНЫЕ ФУНКЦИИ ===

SendKeyToPIDs(key, pids_string) {
    ; Отправить клавишу окнам по списку PID
    ; pids_string = "12345,67890,11111"
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "") {
            continue
        }
        
        hwnd := GetWindowByPID(target_pid)
        if (hwnd) {
            ; Кликнуть для активации
            CoordMode, Mouse, Screen
            ControlClick, x140 y120, ahk_id %hwnd%, , L, NA
            
            ; Отправить клавишу
            ControlSend, , {%key%}, ahk_id %hwnd%
        }
    }
}

ClickToPIDs(x, y, pids_string) {
    ; Клик по координатам для указанных PID
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "") {
            continue
        }
        
        hwnd := GetWindowByPID(target_pid)
        if (hwnd) {
            CoordMode, Mouse, Screen
            ControlClick, x%x% y%y%, ahk_id %hwnd%, , L, NA
        }
    }
}

Headhunter(pid) {
    ; Tab + ЛКМ по 100,100 для указанного PID
    hwnd := GetWindowByPID(pid)
    if (!hwnd) {
        return
    }
    
    ; Tab
    ControlSend, , {Tab}, ahk_id %hwnd%
    Sleep, 50
    ; ЛКМ по 100,100
    CoordMode, Mouse, Screen
    ControlClick, x100 y100, ahk_id %hwnd%, , L, NA
}

FollowLider(pids_string) {
    ; ЛКМ + ПКМ по 100,100 для указанных PID
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "") {
            continue
        }
        
        hwnd := GetWindowByPID(target_pid)
        if (!hwnd) {
            continue
        }
        
        CoordMode, Mouse, Screen
        ; ЛКМ
        ControlClick, x100 y100, ahk_id %hwnd%, , L, NA
        Sleep, 50
        ; ПКМ
        ControlClick, x100 y100, ahk_id %hwnd%, , R, NA
    }
}

; === ОБРАБОТКА КОМАНД ===

CheckCommand:
    if FileExist(command_file) {
        FileRead, command, %command_file%
        FileDelete, %command_file%
        
        if (command = "") {
            return
        }
        else if (command = "EXIT") {
            ExitApp
        }
        ; CLICK:100:200:12345,67890
        else if (InStr(command, "CLICK:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() >= 4) {
                x := parts[2]
                y := parts[3]
                pids := parts[4]
                ClickToPIDs(x, y, pids)
            }
        }
        ; HEADHUNTER:12345
        else if (InStr(command, "HEADHUNTER:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() = 2) {
                pid := parts[2]
                Headhunter(pid)
            }
        }
        ; FOLLOW_LIDER:12345,67890
        else if (InStr(command, "FOLLOW_LIDER:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() = 2) {
                pids := parts[2]
                FollowLider(pids)
            }
        }
        ; KEY:W:12345,67890
        else if (InStr(command, "KEY:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() >= 3) {
                key := parts[2]
                pids := parts[3]
                SendKeyToPIDs(key, pids)
            }
        }
    }
return

; === ИНИЦИАЛИЗАЦИЯ ===
if FileExist(command_file) {
    FileDelete, %command_file%
}

SetTimer, CheckCommand, 50
return