; hotkeys.ahk - ФИНАЛЬНАЯ ВЕРСИЯ БЕЗ ЛОГИРОВАНИЯ
#SingleInstance Force
#NoEnv
#Persistent
SetControlDelay -1
SetBatchLines -1

if A_IsCompiled
    script_dir := A_ScriptDir
else
    script_dir := A_ScriptDir

global element_windows := []
global command_file := script_dir . "\ahk_command.txt"

; Обновить список окон (вызывается только по команде REFRESH)
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
    
    ; Сначала кликаем в активном окне
    Click, x%xpos% y%ypos%
    
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            CoordMode, Mouse, Screen
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
        }
    }
}

; Отправить клавишу во все окна (С КОСТЫЛЁМ - КЛИК ПО 140,120)
SendKeyToAll(key, repeat_count := 1) {
    global element_windows
    
    if (element_windows.Length() = 0) {
        return
    }
    
    ; === КОСТЫЛЬ: Сначала кликаем по (140, 120) во всех окнах ===
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            CoordMode, Mouse, Screen
            ControlClick, x140 y120, ahk_id %window_id%, , L, NA
        }
    }
    
    ; === Отправляем клавиши ===
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
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

; Начальное обновление списка окон
UpdateWindowList()

SetTimer, CheckCommand, 50
return

CheckCommand:
    global command_file
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
    }
return