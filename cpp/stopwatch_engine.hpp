#pragma once

#include <functional>
#include <string>
#include <vector>

struct LapRecord {
    int index;
    double lap_seconds;
    double total_seconds;
};

std::string format_time(double seconds);
std::wstring format_time_w(double seconds);

class StopwatchEngine {
public:
    using ClockFn = std::function<double()>;

    StopwatchEngine();
    explicit StopwatchEngine(ClockFn clock);

    bool is_running() const noexcept;
    const std::vector<LapRecord>& laps() const noexcept;
    double elapsed_seconds() const;

    void start();
    void pause();
    bool toggle();
    void reset();
    LapRecord lap();

    static ClockFn default_clock();

private:
    ClockFn clock_;
    bool running_ = false;
    double start_timestamp_ = 0.0;
    double accumulated_ = 0.0;
    double last_lap_total_ = 0.0;
    std::vector<LapRecord> laps_;
};
