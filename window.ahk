element_windows := []
WinGet, id, list, ahk_class ElementClient Window
Loop, %id%
    {
        this_id := id%A_Index%
        element_windows.Push(this_id)
    }

#IfWinActive ahk_class ElementClient Window
SetControlDelay -1

XButton1::
MouseGetPos, xpos, ypos
WinGet, active_id, ID, A
for index, window_id in element_windows {
    if (window_id != active_id) && WinExist("ahk_id " . window_id) {
        CoordMode, Mouse, Screen
        ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
    }
}
return

+XButton1::
WinGet, active_id, ID, A
for index, window_id in element_windows {
    if (window_id != active_id) && WinExist("ahk_id " . window_id) {
        CoordMode, Mouse, Screen
        ControlClick, x482 y666, ahk_id %window_id%, , R, NA
        ControlClick, x530 y727, ahk_id %window_id%, , L, NA
        Sleep, 500
        ControlClick, x832 y814, ahk_id %window_id%, , L, NA
    }
}
return

XButton2::
MouseGetPos, xpos, ypos
WinGet, active_id, ID, A
Click, x%xpos% y%ypos%
for index, window_id in element_windows {
    if (window_id != active_id) && WinExist("ahk_id " . window_id) {
        CoordMode, Mouse, Screen
        ControlClick, x%xpos% y%ypos%, ahk_id %window_id%, , L, NA
    }
}
return

+XButton2::
WinGet, active_id, ID, A
for index, window_id in element_windows {
    if (window_id != active_id) && WinExist("ahk_id " . window_id) {
        CoordMode, Mouse, Screen
        ControlClick, x482 y666, ahk_id %window_id%, , R, NA
        ControlClick, x530 y710, ahk_id %window_id%, , L, NA
        ControlClick, x482 y666, ahk_id %window_id%, , R, NA
        ControlClick, x530 y727, ahk_id %window_id%, , L, NA
    }
}
return