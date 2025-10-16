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

global element_windows := []

; Обновить список окон
UpdateWindowList() {
    global element_windows
    element_windows := []
    WinGet, id, list, ahk_class ElementClient Window
    Loop, %id%
    {
        this_id := id%A_Index%
        if WinExist("ahk_id " . this_id) {
            element_windows.Push(this_id)
        }
    }
}

; Кликнуть в текущей позиции мыши
ClickAtMouse() {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    MouseGetPos, xpos, ypos
    WinGet, active_id, ID, A
    
    Click, x%xpos% y%ypos%
    
    for index, window_id in element_windows {
        if (window_id != active_id) && WinExist("ahk_id " . window_id) {
            CoordMode, Mouse, Screen
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
        }
    }
}

; Отправить клавишу во все окна
SendKeyToAll(key, repeat_count := 1) {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            CoordMode, Mouse, Screen
            ControlClick, x140 y120, ahk_id %window_id%, , L, NA
        }
    }
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            Loop, %repeat_count%
            {
                ControlSend, , {%key%}, ahk_id %window_id%
            }
        }
    }
}

; Отправить клавишу конкретному окну по PID
SendKeyToPID(key, target_pid) {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            WinGet, window_pid, PID, ahk_id %window_id%
            
            if (window_pid = target_pid) {
                CoordMode, Mouse, Screen
                ControlClick, x140 y120, ahk_id %window_id%, , L, NA
                ControlSend, , {%key%}, ahk_id %window_id%
                return
            }
        }
    }
}

; НОВОЕ: Headhunter - Tab + ЛКМ по координатам 100, 100
Headhunter() {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            WinGet, window_pid, PID, ahk_id %window_id%
            
            if (window_pid = target_pid) {
                ; Отправляем Tab
                ControlSend, , {Tab}, ahk_id %window_id%
                Sleep, 50
                ; ЛКМ по координатам 100, 100
                ControlClick, x100 y100, ahk_id %window_id%, , L, NA
                return
            }
        }
    }
}

; НОВОЕ: Follow Lider - ЛКМ + ПКМ по координатам 100, 100
FollowLider() {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            CoordMode, Mouse, Screen
            ; ЛКМ по координатам 100, 100
            ControlClick, x100 y100, ahk_id %window_id%, , L, NA
            Sleep, 50
            ; ПКМ по координатам 100, 100
            ControlClick, x100 y100, ahk_id %window_id%, , R, NA
        }
    }
}

; === ИНИЦИАЛИЗАЦИЯ ===
if FileExist(command_file) {
    FileDelete, %command_file%
}

UpdateWindowList()

SetTimer, CheckCommand, 10
return

CheckCommand:
    if FileExist(command_file) {
        FileRead, command, %command_file%
        FileDelete, %command_file%
        
        if (command = "") {
            return
        }
        
        if (command = "CLICK") {
            ClickAtMouse()
        }
        else if (command = "REFRESH") {
            UpdateWindowList()
        }
        else if (command = "EXIT") {
            ExitApp
        }
        else if (InStr(command, "HEADHUNTER:") = 1) {
            ; НОВОЕ: Формат HEADHUNTER:12345
            parts := StrSplit(command, ":")
            if (parts.Length() = 2) {
                pid := parts[2]
                Headhunter(pid)
            }
        }
        else if (command = "FOLLOW_LIDER") {
            FollowLider()
        }
        else if (InStr(command, "KEY_PID:") = 1) {
            ; Формат KEY_PID:W:12345
            parts := StrSplit(command, ":")
            if (parts.Length() = 3) {
                key := parts[2]
                pid := parts[3]
                SendKeyToPID(key, pid)
            }
        }
        else if (InStr(command, "KEY:") = 1) {
            key := SubStr(command, 5)
            SendKeyToAll(key)
        }
    }
return