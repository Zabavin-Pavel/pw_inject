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

global headhunter_x, headhunter_y
global leader_x, leader_y
global element_windows := []

LoadSettings() {
    global headhunter_x, headhunter_y
    global leader_x, leader_y

    EnvGet, LocalAppData, LOCALAPPDATA
    settings_file := LocalAppData . "\xvocmuk\settings.ini"

    IniRead, headhunter_x, %settings_file%, Coordinates, headhunter_x, 394
    IniRead, headhunter_y, %settings_file%, Coordinates, headhunter_y, 553
    IniRead, leader_x, %settings_file%, Coordinates, leader_x, 411
    IniRead, leader_y, %settings_file%, Coordinates, leader_y, 666
    ; MsgBox, excluded_windows = %excluded_windows%
}

; НОВОЕ: Функция проверки исключения - читает файл каждый раз
IsExcluded(window_pid) {
    EnvGet, LocalAppData, LOCALAPPDATA
    settings_file := LocalAppData . "\xvocmuk\settings.ini"
    
    ; Читаем список PIDs через запятую
    IniRead, excluded_windows_str, %settings_file%, Excluded, windows, 0
    
    ; Если "0" или пусто - никого не исключаем
    if (excluded_windows_str = "0" || excluded_windows_str = "") {
        return false
    }
    
    ; Парсим список и проверяем наличие PID
    Loop, Parse, excluded_windows_str, `,
    {
        if (A_LoopField = window_pid) {
            return true
        }
    }
    
    return false
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
    global element_windows, leader_x, leader_y
    
    if (element_windows.Length() = 0) {
        return
    }

    ; Вычисляем координаты с offset
    offset_x := leader_x + 30
    assist_y := leader_y + 65
    follow_y := leader_y + 50

    for index, window_id in element_windows {
        WinGet, window_pid, PID, ahk_id %window_id%
        
        ; IsExcluded теперь сам читает актуальный список
        if (!IsExcluded(window_pid)) && WinExist("ahk_id " . window_id) {
            CoordMode, Mouse, Screen
            ControlClick, x%leader_x% y%leader_y%, ahk_id %window_id%, , R, NA
            ControlClick, x%offset_x% y%assist_y%, ahk_id %window_id%, , L, NA
            ControlClick, x%leader_x% y%leader_y%, ahk_id %window_id%, , R, NA
            ControlClick, x%offset_x% y%follow_y%, ahk_id %window_id%, , L, NA
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
                global headhunter_x, headhunter_y
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
                        ControlClick, x%headhunter_x% y%headhunter_y%, ahk_id %window_id%, , L, 1, NA
                        Sleep, 1100
                    }
                }
            }
        }
    }
return


; ; Добавь в начало файла после глобальных переменных:
; global headhunter_active := false
; global headhunter_window_id := 0

; CheckCommand:
;     if FileExist(command_file) {
;         FileRead, command, %command_file%
;         FileDelete, %command_file%
        
;         if (command = "") {
;             return
;         }
        
;         if (command = "CLICK") {
;             ClickAtMouse()
;         }
;         else if (command = "REFRESH") {
;             UpdateWindowList()
;         }
;         else if (command = "EXIT") {
;             ExitApp
;         }
;         else if (InStr(command, "KEY:") = 1) {
;             key := SubStr(command, 5)
;             SendKeyToAll(key)
;         }
;         else if (command = "FOLLOW") {
;             FollowLider()
;         }
;         else if (command = "HEADHUNTER_START") {
;             global headhunter_active, headhunter_window_id
            
;             ; Получаем активное окно ElementClient
;             WinGet, active_id, ID, A
;             if WinExist("ahk_id " . active_id) {
;                 WinGetClass, active_class, ahk_id %active_id%
;                 if (active_class = "ElementClient Window") {
;                     headhunter_window_id := active_id
;                     headhunter_active := true
;                     SetTimer, HeadhunterLoop, 500
;                 }
;             }
;         }
;         else if (command = "HEADHUNTER_STOP") {
;             global headhunter_active
;             headhunter_active := false
;             SetTimer, HeadhunterLoop, Off
;         }
;     }
; return

; HeadhunterLoop:
;     global headhunter_active, headhunter_window_id, headhunter_x, headhunter_y
    
;     if (!headhunter_active) {
;         SetTimer, HeadhunterLoop, Off
;         return
;     }
    
;     ; Проверка что окно еще существует
;     if (!WinExist("ahk_id " . headhunter_window_id)) {
;         headhunter_active := false
;         SetTimer, HeadhunterLoop, Off
;         return
;     }
    
;     CoordMode, Mouse, Screen
;     ControlClick, x115 y75, ahk_id %headhunter_window_id%, , L, NA
;     ControlSend, , {tab}, ahk_id %headhunter_window_id%
;     ControlClick, x%headhunter_x% y%headhunter_y%, ahk_id %headhunter_window_id%, , L, 1, NA
; return