#include "memory_utils.h"
#include <windows.h>
#include <tlhelp32.h>
#include <fstream>
#include "json.hpp"
#include <string>

static HANDLE hProcess = nullptr;
static json offsets;
static uintptr_t base_address = 0;

DWORD get_process_id(const std::wstring& process_name) {
    DWORD pid = 0;
    PROCESSENTRY32 entry = { sizeof(PROCESSENTRY32) };
    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) return 0;

    if (Process32First(snapshot, &entry)) {
        do {
            if (wcscmp(entry.szExeFile, process_name.c_str()) == 0) {
                pid = entry.th32ProcessID;
                break;
            }
        } while (Process32Next(snapshot, &entry));
    }

    CloseHandle(snapshot);
    return pid;
}

uintptr_t read_pointer(uintptr_t address) {
    if (!hProcess) return 0;
    uintptr_t value = 0;
    ReadProcessMemory(hProcess, (LPCVOID)address, &value, sizeof(value), nullptr);
    return value;
}

void load_offsets() {
    std::ifstream f("offsets.json");
    f >> offsets;

    std::string proc_name = offsets["process_name"];
    DWORD pid = get_process_id(std::wstring(proc_name.begin(), proc_name.end()));
    if (pid == 0) return;

    hProcess = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);

    uintptr_t module_base = (uintptr_t)GetModuleHandleA(proc_name.c_str());
    base_address = module_base + std::stoul(offsets["offsets"]["char_origin"].get<std::string>(), nullptr, 16);
}

float read_float_from_pointer(const char* offset_key) {
    if (!hProcess) load_offsets();
    if (!hProcess) return -1.0f;

    uintptr_t ptr = 0;
    ReadProcessMemory(hProcess, (LPCVOID)base_address, &ptr, sizeof(ptr), nullptr);

    for (auto off : offsets["offsets"]["char_base_offsets"]) {
        ptr = read_pointer(ptr + off.get<size_t>());
    }

    uintptr_t final_address = ptr + std::stoul(offsets["offsets"][offset_key].get<std::string>(), nullptr, 16);
    float value = 0.0f;
    ReadProcessMemory(hProcess, (LPCVOID)final_address, &value, sizeof(value), nullptr);
    return value;
}

