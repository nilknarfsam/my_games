#include "stopwatch_engine.hpp"

#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>

namespace {

class FakeClock {
public:
    explicit FakeClock(double initial = 0.0) : now_(initial) {}

    double operator()() const { return now_; }
    void advance(double seconds) { now_ += seconds; }

private:
    double now_;
};

bool approx_equal(double a, double b, double eps = 1e-9) {
    return std::fabs(a - b) <= eps;
}

void test_format_time() {
    assert(format_time(0.0) == "00:00:00.00");
    assert(format_time(-5.25) == "00:00:00.00");
    assert(format_time(3723.45) == "01:02:03.45");
    assert(format_time(1.14) == "00:00:01.14");
}

void test_initial_state() {
    FakeClock clock(100.0);
    StopwatchEngine engine([&clock]() { return clock(); });
    assert(!engine.is_running());
    assert(approx_equal(engine.elapsed_seconds(), 0.0));
    assert(engine.laps().empty());
}

void test_start_pause_resume_reset() {
    FakeClock clock(10.0);
    StopwatchEngine engine([&clock]() { return clock(); });

    engine.start();
    assert(engine.is_running());
    clock.advance(2.5);
    assert(approx_equal(engine.elapsed_seconds(), 2.5));

    engine.pause();
    assert(!engine.is_running());
    clock.advance(5.0);
    assert(approx_equal(engine.elapsed_seconds(), 2.5));

    engine.start();
    clock.advance(1.25);
    assert(approx_equal(engine.elapsed_seconds(), 3.75));

    engine.reset();
    assert(!engine.is_running());
    assert(approx_equal(engine.elapsed_seconds(), 0.0));
    assert(engine.laps().empty());
}

void test_laps_compute_splits_and_totals() {
    FakeClock clock(0.0);
    StopwatchEngine engine([&clock]() { return clock(); });

    bool threw = false;
    try {
        engine.lap();
    } catch (const std::runtime_error&) {
        threw = true;
    }
    assert(threw);

    engine.start();
    clock.advance(1.5);
    const LapRecord lap1 = engine.lap();
    assert(lap1.index == 1);
    assert(approx_equal(lap1.lap_seconds, 1.5));
    assert(approx_equal(lap1.total_seconds, 1.5));

    clock.advance(2.25);
    const LapRecord lap2 = engine.lap();
    assert(lap2.index == 2);
    assert(approx_equal(lap2.lap_seconds, 2.25));
    assert(approx_equal(lap2.total_seconds, 3.75));
    assert(engine.laps().size() == 2);
}

}  // namespace

int main() {
    test_format_time();
    test_initial_state();
    test_start_pause_resume_reset();
    test_laps_compute_splits_and_totals();
    std::cout << "All 4 C++ unit test suites passed.\n";
    return 0;
}
