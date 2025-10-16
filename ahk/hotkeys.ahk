; hotkeys.ahk - принимает путь к command_file как аргумент
; #NoTrayIcon
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
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            ControlClick, x140 y120, ahk_id %window_id%, , L, NA

            Loop, %repeat_count%
            {
                ControlSend, , {%key%}, ahk_id %window_id%
            }
        }
    }
}

; ===================================================
; HEADHUNTER FUNCTIONS
; ===================================================

; StartHeadhunter() {
;     global headhunter_active
;     global headhunter_window_id
    
;     ; Если уже активен - выходим
;     if (headhunter_active) {
;         return
;     }
    
;     ; Ждем пока активное окно станет ElementClient (5 секунд)
;     WinWaitActive, ahk_class ElementClient Window, , 5
    
;     if (ErrorLevel) {
;         ; Таймаут - окно не стало активным за 5 секунд
;         ; ОТЛАДКА: можно раскомментировать
;         ; MsgBox, Headhunter: No ElementClient window became active within 5 seconds
;         return
;     }
    
;     ; Сохраняем ID активного окна
;     WinGet, headhunter_window_id, ID, A
    
;     ; Проверяем что окно валидное
;     if (!headhunter_window_id || headhunter_window_id = 0) {
;         ; ОТЛАДКА: можно раскомментировать
;         ; MsgBox, Headhunter: Invalid window ID
;         return
;     }
    
;     ; ОТЛАДКА: можно раскомментировать для проверки
;     ; MsgBox, Headhunter started for window ID: %headhunter_window_id%
    
;     ; Активируем режим
;     headhunter_active := true
    
;     ; Запускаем таймер (200мс)
;     SetTimer, HeadhunterLoop, 200
; }

; StopHeadhunter() {
;     global headhunter_active
;     global headhunter_window_id
    
;     ; Останавливаем таймер
;     SetTimer, HeadhunterLoop, Off
    
;     ; Сбрасываем флаги
;     headhunter_active := false
;     headhunter_window_id := 0
; }

; HeadhunterLoop:
;     global headhunter_active
;     global headhunter_window_id
    
;     ; Проверяем что режим активен
;     if (!headhunter_active) {
;         return
;     }
    
;     ; Проверяем что окно существует
;     if (!WinExist("ahk_id " . headhunter_window_id)) {
;         ; Окно закрыто - останавливаем
;         ; ОТЛАДКА: можно раскомментировать
;         ; MsgBox, Headhunter: Window closed, stopping
;         StopHeadhunter()
;         return
;     }
    
;     ; ОТЛАДКА: раскомментируйте чтобы увидеть работает ли цикл
;     ; ToolTip, Headhunter: Sending Tab + Click to window %headhunter_window_id%
    
;     ; Отправляем Tab в конкретное окно
;     ControlSend, , {Tab}, ahk_id %headhunter_window_id%
    
;     ; Небольшая задержка между Tab и кликом
;     Sleep, 50
    
;     ; Кликаем по (100, 100) В КОНКРЕТНОМ ОКНЕ
;     ; NA = NoActivate (не активировать окно)
;     ControlClick, x100 y100, ahk_id %headhunter_window_id%, , L, 1, NA
    
;     return


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
        ; else if (command = "HEADHUNTER_START") {
        ;     StartHeadhunter()
        ; }
        ; else if (command = "HEADHUNTER_STOP") {
        ;     StopHeadhunter()
        ; }
    }
return