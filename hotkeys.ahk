; hotkeys.ahk - ИСПРАВЛЕННАЯ ВЕРСИЯ
#SingleInstance Force
#NoEnv
#Persistent
SetControlDelay -1
SetBatchLines -1

; Путь к командному файлу
if A_IsCompiled
    script_dir := A_ScriptDir
else
    script_dir := A_ScriptDir

global element_windows := []
global command_file := script_dir . "\ahk_command.txt"
global log_file := script_dir . "\ahk_log.txt"

; Логирование
Log(message) {
    global log_file
    FormatTime, timestamp, , yyyy-MM-dd HH:mm:ss
    FileAppend, %timestamp% - %message%`n, %log_file%
}

; Обновить список окон
UpdateWindowList() {
    global element_windows
    element_windows := []
    WinGet, id, list, ahk_class ElementClient Window
    Loop, %id%
    {
        this_id := id%A_Index%
        element_windows.Push(this_id)
    }
    Log("Updated window list: " . element_windows.Length() . " windows found")
}

; Кликнуть в текущей позиции мыши
ClickAtMouse() {
    global element_windows
    Log("CLICK command received")
    UpdateWindowList()
    
    if (element_windows.Length() = 0) {
        Log("No windows found")
        return
    }
    
    MouseGetPos, xpos, ypos
    WinGet, active_id, ID, A
    
    Log("Mouse position: " . xpos . ", " . ypos)
    Log("Active window: " . Format("0x{:x}", active_id))
    
    ; ВАЖНО: Сначала кликаем в активном окне
    Click, x%xpos% y%ypos%
    
    clicked := 0
    for index, window_id in element_windows {
        if WinExist("ahk_id " . window_id) {
            ; ВАЖНО: CoordMode перед каждым ControlClick
            CoordMode, Mouse, Screen
            ; ВАЖНО: Без лишней "1" в параметрах
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
            clicked++
            Log("Clicked window: " . Format("0x{:x}", window_id))
        }
    }
    Log("Total clicks: " . clicked)
}

; ИСПРАВЛЕНО: Отправить клавишу во все окна (включая активное) + повторения
SendKeyToAll(key, repeat_count := 1) {
    global element_windows
    Log("KEY command received: " . key . " x" . repeat_count)
    UpdateWindowList()
    
    if (element_windows.Length() = 0) {
        Log("No windows found")
        return
    }
    
    WinGet, active_id, ID, A
    
    sent := 0
    for index, window_id in element_windows {
        ; УБРАЛИ ПРОВЕРКУ (window_id != active_id) - теперь и активное окно получает
        if WinExist("ahk_id " . window_id) {
            ; Отправляем клавишу repeat_count раз
            Loop, %repeat_count%
            {
                ControlSend, , {%key%}, ahk_id %window_id%
            }
            sent++
            Log("Sent key to window: " . Format("0x{:x}", window_id) . " x" . repeat_count)
        }
    }
    Log("Total keys sent to " . sent . " windows")
}

; === ИНИЦИАЛИЗАЦИЯ ===
Log("=== AHK Script Started ===")
Log("Script dir: " . script_dir)
Log("Command file: " . command_file)

; Удаляем старый файл команд при запуске
if FileExist(command_file) {
    FileDelete, %command_file%
    Log("Deleted old command file")
}

; === ТАЙМЕР ДЛЯ ПРОВЕРКИ КОМАНД ===
SetTimer, CheckCommand, 1
return

CheckCommand:
    global command_file
    if FileExist(command_file) {
        FileRead, command, %command_file%
        FileDelete, %command_file%
        
        if (command = "") {
            return
        }
        
        Log("Command received: " . command)
        
        ; Выполняем команду
        if (command = "CLICK") {
            ClickAtMouse()
        }
        else if (command = "EXIT") {
            Log("EXIT command received")
            ExitApp
        }
        else if (InStr(command, "KEY:") = 1) {
            key := SubStr(command, 5)
            SendKeyToAll(key)
        }
        else {
            Log("Unknown command: " . command)
        }
    }
return