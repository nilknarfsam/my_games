#include "stopwatch_engine.hpp"

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <stdexcept>
#include <utility>

std::string format_time(double seconds) {
    const double clamped = std::max(0.0, seconds);
    const auto total_centiseconds = static_cast<long long>(clamped * 100.0 + 1e-9);
    const long long centiseconds = total_centiseconds % 100;
    const long long total_seconds = total_centiseconds / 100;
    const long long secs = total_seconds % 60;
    const long long total_minutes = total_seconds / 60;
    const long long minutes = total_minutes % 60;
    const long long hours = total_minutes / 60;

    char buffer[32];
    std::snprintf(buffer, sizeof(buffer), "%02lld:%02lld:%02lld.%02lld",
                  hours, minutes, secs, centiseconds);
    return std::string(buffer);
}

std::wstring format_time_w(double seconds) {
    const std::string narrow = format_time(seconds);
    return std::wstring(narrow.begin(), narrow.end());
}

StopwatchEngine::ClockFn StopwatchEngine::default_clock() {
    return []() -> double {
        using clock = std::chrono::steady_clock;
        const auto now = clock::now().time_since_epoch();
        return std::chrono::duration<double>(now).count();
    };
}

StopwatchEngine::StopwatchEngine() : clock_(default_clock()) {}

StopwatchEngine::StopwatchEngine(ClockFn clock) : clock_(std::move(clock)) {}

bool StopwatchEngine::is_running() const noexcept {
    return running_;
}

const std::vector<LapRecord>& StopwatchEngine::laps() const noexcept {
    return laps_;
}

double StopwatchEngine::elapsed_seconds() const {
    if (!running_) {
        return accumulated_;
    }
    return accumulated_ + std::max(0.0, clock_() - start_timestamp_);
}

void StopwatchEngine::start() {
    if (running_) {
        return;
    }
    start_timestamp_ = clock_();
    running_ = true;
}

void StopwatchEngine::pause() {
    if (!running_) {
        return;
    }
    accumulated_ = elapsed_seconds();
    running_ = false;
}

bool StopwatchEngine::toggle() {
    if (running_) {
        pause();
    } else {
        start();
    }
    return running_;
}

void StopwatchEngine::reset() {
    running_ = false;
    start_timestamp_ = 0.0;
    accumulated_ = 0.0;
    last_lap_total_ = 0.0;
    laps_.clear();
}

LapRecord StopwatchEngine::lap() {
    const double total = elapsed_seconds();
    if (!running_ && total == 0.0) {
        throw std::runtime_error(
            "Nao e possivel registrar volta com o cronometro zerado.");
    }
    const double split = std::max(0.0, total - last_lap_total_);
    last_lap_total_ = total;
    LapRecord record{
        static_cast<int>(laps_.size()) + 1,
        split,
        total,
    };
    laps_.push_back(record);
    return record;
}
