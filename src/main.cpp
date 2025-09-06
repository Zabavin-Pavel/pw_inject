#include "memory_utils.h"

extern "C" __declspec(dllexport) float get_hp() {
    return read_float_from_pointer("health_offset");
}

extern "C" __declspec(dllexport) float get_mp() {
    return read_float_from_pointer("mana_offset");
}
