; hotkeys.ahk - принимает путь к command_file как аргумент
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

; === ФУНКЦИИ ДЛЯ РАБОТЫ С PID ===

SendKeyToPIDs(key, pids_string) {
    ; pids_string = "12345,67890,11111" - строка с PID через запятую
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        ; Убираем пробелы
        target_pid := Trim(target_pid)
        
        if (target_pid = "") {
            continue
        }
        
        ; Найти окно по PID
        WinGet, id, list, ahk_class ElementClient Window
        Loop, %id% {
            this_id := id%A_Index%
            WinGet, window_pid, PID, ahk_id %this_id%
            
            if (window_pid = target_pid) {
                ; Кликнуть для активации
                CoordMode, Mouse, Screen
                ControlClick, x140 y120, ahk_id %this_id%, , L, NA
                
                ; Отправить клавишу
                ControlSend, , {%key%}, ahk_id %this_id%
                break
            }
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
        
        WinGet, id, list, ahk_class ElementClient Window
        Loop, %id% {
            this_id := id%A_Index%
            WinGet, window_pid, PID, ahk_id %this_id%
            
            if (window_pid = target_pid) {
                CoordMode, Mouse, Screen
                ControlClick, x%x% y%y%, ahk_id %this_id%, , L, NA
                break
            }
        }
    }
}

Headhunter(pids_string) {
    ; Tab + ЛКМ по координатам для указанных PID
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "") {
            continue
        }
        
        WinGet, id, list, ahk_class ElementClient Window
        Loop, %id% {
            this_id := id%A_Index%
            WinGet, window_pid, PID, ahk_id %this_id%
            
            if (window_pid = target_pid) {
                ; Tab
                ControlSend, , {Tab}, ahk_id %this_id%
                Sleep, 50
                ; ЛКМ
                CoordMode, Mouse, Screen
                ControlClick, x100 y100, ahk_id %this_id%, , L, NA
                break
            }
        }
    }
}

FollowLider(pids_string) {
    ; ЛКМ + ПКМ по координатам для указанных PID
    pids := StrSplit(pids_string, ",")
    
    for index, target_pid in pids {
        target_pid := Trim(target_pid)
        
        if (target_pid = "") {
            continue
        }
        
        WinGet, id, list, ahk_class ElementClient Window
        Loop, %id% {
            this_id := id%A_Index%
            WinGet, window_pid, PID, ahk_id %this_id%
            
            if (window_pid = target_pid) {
                CoordMode, Mouse, Screen
                ; ЛКМ
                ControlClick, x100 y100, ahk_id %this_id%, , L, NA
                Sleep, 50
                ; ПКМ
                ControlClick, x100 y100, ahk_id %this_id%, , R, NA
                break
            }
        }
    }
}


; === ИНИЦИАЛИЗАЦИЯ ===
if FileExist(command_file) {
    FileDelete, %command_file%
}

UpdateWindowList()

SetTimer, CheckCommand, 50
return

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
        ; CLICK:100:200:12345,67890 - клик по координатам
        else if (InStr(command, "CLICK:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() >= 4) {
                x := parts[2]
                y := parts[3]
                pids := parts[4]
                ClickToPIDs(x, y, pids)
            }
        }
        ; HEADHUNTER:12345,67890 - headhunter для указанных PID
        else if (InStr(command, "HEADHUNTER:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() = 2) {
                pids := parts[2]
                Headhunter(pids)
            }
        }
        ; FOLLOW_LIDER:12345,67890 - follow lider для указанных PID
        else if (InStr(command, "FOLLOW_LIDER:") = 1) {
            parts := StrSplit(command, ":")
            if (parts.Length() = 2) {
                pids := parts[2]
                FollowLider(pids)
            }
        }
        ; KEY:W:12345,67890 - отправить клавишу W в окна с PID 12345 и 67890
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