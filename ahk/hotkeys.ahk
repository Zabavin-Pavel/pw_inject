; hotkeys.ahk - работа через Window ID без файлов
#NoTrayIcon
#SingleInstance Force
#NoEnv
#Persistent
SetControlDelay -1
SetBatchLines -1

; === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
global leader_x := 411
global leader_y := 666
global headhunter_x := 394
global headhunter_y := 553
global macros_spam_x := 0
global macros_spam_y := 0

; Получение списка всех окон ElementClient (кроме исключенных)
GetActiveWindows(excluded_pids := "") {
    windows := []
    
    ; Парсим список исключенных PIDs
    excluded_array := []
    if (excluded_pids != "") {
        Loop, Parse, excluded_pids, `,
        {
            excluded_array.Push(A_LoopField)
        }
    }
    
    ; Получаем все окна ElementClient
    WinGet, id, list, ahk_exe ElementClient.exe
    Loop, %id%
    {
        this_id := id%A_Index%
        WinGet, window_pid, PID, ahk_id %this_id%
        
        ; Проверяем не в списке исключений
        is_excluded := false
        for index, excluded_pid in excluded_array {
            if (window_pid = excluded_pid) {
                is_excluded := true
                break
            }
        }
        
        ; Добавляем если не исключен и существует
        if (!is_excluded && WinExist("ahk_id " . this_id)) {
            windows.Push(this_id)
        }
    }
    
    return windows
}

; === КОМАНДЫ ===

; Клик по текущей позиции мыши
ClickAtMouse(excluded_pids := "") {
    windows := GetActiveWindows(excluded_pids)
    
    if (windows.Length() = 0) {
        return
    }
    
    MouseGetPos, xpos, ypos
    CoordMode, Mouse, Screen
    
    for index, window_id in windows {
        if WinExist("ahk_id " . window_id) {
            ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
        }
    }
}

; Follow лидера (ПКМ + Ассист + ПКМ + Follow) - ОБНОВЛЕНО
FollowLeader(target_pids := "") {
    windows := []
    
    ; Парсим список целевых PIDs
    target_array := []
    if (target_pids != "") {
        Loop, Parse, target_pids, `,
        {
            target_array.Push(A_LoopField)
        }
    }
    
    if (target_array.Length() = 0) {
        return
    }
    
    ; Получаем все окна ElementClient
    WinGet, id, list, ahk_exe ElementClient.exe
    Loop, %id%
    {
        this_id := id%A_Index%
        WinGet, window_pid, PID, ahk_id %this_id%
        
        ; Проверяем что PID в списке целевых
        is_target := false
        for index, target_pid in target_array {
            if (window_pid = target_pid) {
                is_target := true
                break
            }
        }
        
        ; Добавляем только если в списке целевых
        if (is_target && WinExist("ahk_id " . this_id)) {
            windows.Push(this_id)
        }
    }
    
    if (windows.Length() = 0) {
        return
    }

    offset_x := leader_x + 30
    assist_y := leader_y + 65
    follow_y := leader_y + 50
    
    CoordMode, Mouse, Screen
    
    for index, window_id in windows {
        if WinExist("ahk_id " . window_id) {
            ; ПКМ по лидеру
            ControlClick, x%leader_x% y%leader_y%, ahk_id %window_id%, , R, NA
            Sleep, 50
            ; ЛКМ Ассист
            ControlClick, x%offset_x% y%assist_y%, ahk_id %window_id%, , L, NA
            Sleep, 50
            ; ПКМ по лидеру
            ControlClick, x%leader_x% y%leader_y%, ahk_id %window_id%, , R, NA
            Sleep, 50
            ; ЛКМ Follow
            ControlClick, x%offset_x% y%follow_y%, ahk_id %window_id%, , L, NA
        }
    }
}

; Атака цели лидера (ПКМ + Ассист + Guard)
AttackGuard(excluded_pids := "") {
    windows := GetActiveWindows(excluded_pids)
    
    if (windows.Length() = 0) {
        return
    }

    offset_x := leader_x + 30
    assist_y := leader_y + 65
    
    CoordMode, Mouse, Screen
    
    for index, window_id in windows {
        if WinExist("ahk_id " . window_id) {
            ; ПКМ по лидеру
            ControlClick, x%leader_x% y%leader_y%, ahk_id %window_id%, , R, NA
            Sleep, 50
            ; ЛКМ Ассист
            ControlClick, x%offset_x% y%assist_y%, ahk_id %window_id%, , L, NA
            Sleep, 50
            ; ЛКМ Guard макрос
            ControlClick, x%macros_spam_x% y%macros_spam_y%, ahk_id %window_id%, , L, NA
        }
    }
}

; Отправить клавишу в конкретные окна (по списку window_id)
SendKeyToWindows(key, window_ids := "", repeat_count := 1) {
    ; Парсим список window_ids
    windows := []
    if (window_ids != "") {
        Loop, Parse, window_ids, `,
        {
            windows.Push(A_LoopField)
        }
    }
    
    if (windows.Length() = 0) {
        return
    }
    
    CoordMode, Mouse, Screen
    
    for index, window_id in windows {
        if WinExist("ahk_id " . window_id) {
            ControlClick, x115 y75, ahk_id %window_id%, , L, NA
            Loop, %repeat_count%
            {
                ControlSend, , {%key%}, ahk_id %window_id%
            }
        }
    }
}

; Headhunter для активного окна
HeadhunterStart(excluded_pids := "") {
    ; Ждем активное окно ElementClient
    WinWaitActive, ahk_exe ElementClient.exe, , 5
    
    if (ErrorLevel) {
        return
    }
    
    ; Получаем ID активного окна
    WinGet, window_id, ID, A
    WinGet, window_pid, PID, ahk_id %window_id%
    
    ; Проверяем не в списке исключений
    excluded_array := []
    if (excluded_pids != "") {
        Loop, Parse, excluded_pids, `,
        {
            excluded_array.Push(A_LoopField)
        }
    }
    
    is_excluded := false
    for index, excluded_pid in excluded_array {
        if (window_pid = excluded_pid) {
            is_excluded := true
            break
        }
    }
    
    if (is_excluded) {
        return
    }
    
    CoordMode, Mouse, Screen
    
    ; Цикл headhunter
    Loop {
        ; Проверка что окно существует
        if (!WinExist("ahk_id " . window_id)) {
            break
        }
        
        ControlClick, x115 y75, ahk_id %window_id%, , L, NA
        ControlSend, , {tab}, ahk_id %window_id%
        ControlClick, x%headhunter_x% y%headhunter_y%, ahk_id %window_id%, , L, 1, NA
        Sleep, 1100
    }
}

; Обновить координаты UI
UpdateCoordinates(lx, ly, hx, hy, mx := 0, my := 0) {
    global leader_x, leader_y, headhunter_x, headhunter_y, macros_spam_x, macros_spam_y
    
    leader_x := lx
    leader_y := ly
    headhunter_x := hx
    headhunter_y := hy
    
    if (mx != 0) {
        macros_spam_x := mx
    }
    if (my != 0) {
        macros_spam_y := my
    }
}

; === COMMAND LINE INTERFACE ===
; Использование:
; hotkeys.exe click "1234,5678"
; hotkeys.exe follow "1234"
; hotkeys.exe key "space" "12345,67890,11111" "1"
; hotkeys.exe coords "411" "666" "394" "553"

if (A_Args.Length() > 0) {
    command := A_Args[1]
    
    if (command = "click") {
        excluded := A_Args.Length() > 1 ? A_Args[2] : ""
        ClickAtMouse(excluded)
    }
    else if (command = "follow") {
        target_pids := A_Args.Length() > 1 ? A_Args[2] : ""
        FollowLeader(target_pids)
    }
    else if (command = "attack_guard") {
        excluded := A_Args.Length() > 1 ? A_Args[2] : ""
        AttackGuard(excluded)
    }
    else if (command = "key") {
        key := A_Args.Length() > 1 ? A_Args[2] : ""
        window_ids := A_Args.Length() > 2 ? A_Args[3] : ""
        repeat := A_Args.Length() > 3 ? A_Args[4] : 1
        
        if (key != "" && window_ids != "") {
            SendKeyToWindows(key, window_ids, repeat)
        }
    }
    else if (command = "headhunter") {
        excluded := A_Args.Length() > 1 ? A_Args[2] : ""
        HeadhunterStart(excluded)
    }
    else if (command = "coords") {
        lx := A_Args.Length() > 1 ? A_Args[2] : 411
        ly := A_Args.Length() > 2 ? A_Args[3] : 666
        hx := A_Args.Length() > 3 ? A_Args[4] : 394
        hy := A_Args.Length() > 4 ? A_Args[5] : 553
        mx := A_Args.Length() > 5 ? A_Args[6] : 0
        my := A_Args.Length() > 6 ? A_Args[7] : 0
        
        UpdateCoordinates(lx, ly, hx, hy, mx, my)
    }
    
    ; Выход после выполнения команды
    ExitApp
}

; Если запущен без параметров - выход
ExitApp
