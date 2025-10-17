; hotkeys.ahk - принимает путь к command_file как аргумент
#NoTrayIcon
#SingleInstance Force
#NoEnv
#Persistent
SetControlDelay -1
SetBatchLines -1

; Получаем путь к command_file из аргументов командной строки
; Если аргумент не передан - используем текущую папку
if (A_Args.Length() > 0) {
    command_file := A_Args[1]
} else {
    command_file := A_ScriptDir . "\ahk_command.txt"
}

global static_x, static_y
global headhunter_x, headhunter_y
global leader_x, leader_y
global excluded_windows := 0
global element_windows := []

LoadSettings() {
    global static_x, static_y, headhunter_x, headhunter_y
    global leader_x, leader_y
    global excluded_windows

    EnvGet, LocalAppData, LOCALAPPDATA
    settings_file := LocalAppData . "\xvocmuk\settings.ini"
    
    IniRead, static_x, %settings_file%, Coordinates, static_x, 115
    IniRead, static_y, %settings_file%, Coordinates, static_y, 75
    IniRead, headhunter_x, %settings_file%, Coordinates, headhunter_x, 394
    IniRead, headhunter_y, %settings_file%, Coordinates, headhunter_y, 553
    IniRead, leader_x, %settings_file%, Coordinates, leader_x, 411
    IniRead, leader_y, %settings_file%, Coordinates, leader_y, 666
    IniRead, excluded_windows, %settings_file%, Excluded, windows, 0
    ; MsgBox, excluded_windows = %excluded_windows%
}

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
    LoadSettings()
}

; Кликнуть в текущей позиции мыши
ClickAtMouse() {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    MouseGetPos, xpos, ypos
    CoordMode, Mouse, Screen
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
        }
    }
}


FollowLider() {
    global element_windows, excluded_windows, leader_x, leader_y
    
    if (element_windows.Length() = 0) {
        return
    }

    CoordMode, Mouse, Screen

    ; Вычисляем координаты с offset
    x2 := leader_x + 50
    y2 := leader_y + 50
    ; MsgBox, excluded_windows = %excluded_windows%
    for index, window_id in element_windows {
        WinGet, window_pid, PID, ahk_id %window_id%
        if (window_pid != excluded_windows) && WinExist("ahk_id " . window_id) {
            ControlClick, x%leader_x% y%leader_y%, ahk_id %window_id%, , R, NA
            ControlClick, x%x2% y%y2%, ahk_id %window_id%, , L, NA
        }
    }
}

; Отправить клавишу во все окна
SendKeyToAll(key, repeat_count := 1) {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    CoordMode, Mouse, Screen
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            ControlClick, x115 y75, ahk_id %window_id%, , L, NA
            Sleep, 10
            ControlClick, x115 y75, ahk_id %window_id%, , L, NA

            Loop, %repeat_count%
            {
                ControlSend, , {%key%}, ahk_id %window_id%
            }
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
        else if (InStr(command, "KEY:") = 1) {
            key := SubStr(command, 5)
            SendKeyToAll(key)
        }
        else if (command = "FOLLOW") {
            FollowLider()
        }
        else if (command = "HEADHUNTER_START") {
            ; Ждем окно ElementClient (5 секунд)
            WinWaitActive, ahk_class ElementClient Window, , 5
            
            if (!ErrorLevel) {
                ; Получаем ID окна
                WinGet, window_id, ID, A
                CoordMode, Mouse, Screen
                
                if (window_id) {
                    ; Цикл headhunter
                    Loop {
                        ; Проверяем команды на остановку
                        if FileExist(command_file) {
                            FileRead, stop_command, %command_file%
                            FileDelete, %command_file%
                            
                            if (stop_command = "HEADHUNTER_STOP") {
                                break
                            }
                        }
                        
                        ; Проверка что окно еще существует
                        if (!WinExist("ahk_id " . window_id)) {
                            break
                        }
                        
                        ControlClick, x115 y75, ahk_id %window_id%, , L, NA
                        ControlSend, , {tab}, ahk_id %window_id%
                        ; Задержка 100 мс
                        Sleep, 100
                        ; Клик левой кнопкой по координатам
                        ControlClick, x394 y553, ahk_id %window_id%, , L, 1, NA
                    }
                }
            }
        }
    }
return