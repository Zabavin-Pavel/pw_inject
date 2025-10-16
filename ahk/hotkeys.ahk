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
    CoordMode, Mouse, Screen
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
        }
    }
}


FollowLider() {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }

    WinGet, active_id, ID, A
    CoordMode, Mouse, Screen
    
    for index, window_id in element_windows {
        if (window_id != active_id) && WinExist("ahk_id " . window_id) {
            ControlClick, x411 y666, ahk_id %window_id%, , R, NA
            ControlClick, x451 y706, ahk_id %window_id%, , L, NA
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