#pragma once

// Default OFF: the user's actual buzzer type/rating and hardware condition are unverified.
// Enable only after an electrically compatible 3.3 V passive piezo circuit has been verified.
// This setting does not make an unknown magnetic buzzer safe.
constexpr bool PASSIVE_BUZZER_ENABLED = false;
constexpr unsigned long BUZZER_TONE_HZ = 2000;
