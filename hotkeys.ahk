; hotkeys.ahk - С ручными хоткеями для тестирования
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

; Логирование (оставляем для отладки)
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
        TrayTip, AHK Debug, No ElementClient windows found!, 2, 1
        return
    }
    
    MouseGetPos, xpos, ypos
    WinGet, active_id, ID, A
    
    Log("Mouse position: " . xpos . ", " . ypos)
    Log("Active window: " . Format("0x{:x}", active_id))
    
    CoordMode, Mouse, Screen
    
    clicked := 0
    for index, window_id in element_windows {
        if (window_id != active_id) && WinExist("ahk_id " . window_id) {
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, 1, NA
            clicked++
            Log("Clicked window: " . Format("0x{:x}", window_id))
        }
    }
    Log("Total clicks: " . clicked)
    TrayTip, AHK Debug, Clicked %clicked% windows at (%xpos%, %ypos%), 1, 1
}

; Отправить клавишу во все окна
SendKeyToAll(key) {
    global element_windows
    Log("KEY command received: " . key)
    UpdateWindowList()
    
    if (element_windows.Length() = 0) {
        Log("No windows found")
        TrayTip, AHK Debug, No ElementClient windows found!, 2, 1
        return
    }
    
    WinGet, active_id, ID, A
    
    sent := 0
    for index, window_id in element_windows {
        if (window_id != active_id) && WinExist("ahk_id " . window_id) {
            ControlSend, , {%key%}, ahk_id %window_id%
            sent++
            Log("Sent key to window: " . Format("0x{:x}", window_id))
        }
    }
    Log("Total keys sent: " . sent)
    TrayTip, AHK Debug, Sent '%key%' to %sent% windows, 1, 1
}

; === РУЧНЫЕ ХОТКЕИ ДЛЯ ТЕСТИРОВАНИЯ ===
F1::
    Log("=== F1 pressed - Manual CLICK test ===")
    ClickAtMouse()
return

F2::
    Log("=== F2 pressed - Manual SPACE test ===")
    SendKeyToAll("Space")
return

F3::
    Log("=== F3 pressed - Test info ===")
    UpdateWindowList()
    global element_windows
    
    if (element_windows.Length() = 0) {
        MsgBox, No ElementClient windows found!
    } else {
        msg := "Found " . element_windows.Length() . " windows:`n`n"
        for index, window_id in element_windows {
            WinGetTitle, title, ahk_id %window_id%
            msg .= index . ". " . Format("0x{:x}", window_id) . " - " . title . "`n"
        }
        MsgBox, %msg%
    }
return

F4::
    Log("=== F4 pressed - EXIT ===")
    MsgBox, 4, AHK Exit, Exit AHK script?
    IfMsgBox Yes
        ExitApp
return

; === ИНИЦИАЛИЗАЦИЯ ===
Log("=== AHK Script Started ===")
Log("Script dir: " . script_dir)
Log("Command file: " . command_file)
TrayTip, AHK Started, F1=Click | F2=Space | F3=Info | F4=Exit, 3, 1

; Удаляем старый файл команд при запуске
if FileExist(command_file) {
    FileDelete, %command_file%
    Log("Deleted old command file")
}

; === ТАЙМЕР ДЛЯ ПРОВЕРКИ КОМАНД ===
SetTimer, CheckCommand, 50
return

CheckCommand:
    global command_file
    if FileExist(command_file) {
        FileRead, command, %command_file%
        FileDelete, %command_file%
        
        if (command = "") {
            Log("Empty command received")
            return
        }
        
        Log("Command received: " . command)
        
        ; Выполняем команду
        if (command = "CLICK") {
            ClickAtMouse()
        }
        else if (command = "SPACE") {
            SendKeyToAll("Space")
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