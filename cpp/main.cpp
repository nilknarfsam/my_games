#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif

#include "stopwatch_engine.hpp"

#include <windows.h>
#include <commctrl.h>

#include <algorithm>
#include <cstdio>
#include <string>
#include <vector>

namespace {

constexpr UINT_PTR kTimerId = 1;
constexpr UINT kRefreshIntervalMs = 20;

constexpr int kIdBtnStart = 101;
constexpr int kIdBtnLap = 102;
constexpr int kIdBtnReset = 103;
constexpr int kIdListLaps = 104;

// Modern dark slate palette matching the Python Tkinter version
constexpr COLORREF kBgMain = RGB(15, 23, 42);           // #0f172a
constexpr COLORREF kBgCard = RGB(30, 41, 59);           // #1e293b
constexpr COLORREF kBgRowAlt = RGB(38, 51, 72);         // #263348
constexpr COLORREF kBorderSlate = RGB(51, 65, 85);      // #334155
constexpr COLORREF kFgPrimary = RGB(248, 250, 252);     // #f8fafc
constexpr COLORREF kFgMuted = RGB(148, 163, 184);       // #94a3b8
constexpr COLORREF kAccentStart = RGB(16, 185, 129);    // #10b981
constexpr COLORREF kAccentPause = RGB(245, 158, 11);    // #f59e0b
constexpr COLORREF kAccentLap = RGB(56, 189, 248);      // #38bdf8
constexpr COLORREF kAccentReset = RGB(239, 68, 68);     // #ef4444
constexpr COLORREF kBtnDisabledBg = RGB(51, 65, 85);    // #334155
constexpr COLORREF kBtnDisabledFg = RGB(100, 116, 139); // #64748b
constexpr COLORREF kFastestColor = RGB(52, 211, 153);   // #34d399
constexpr COLORREF kSlowestColor = RGB(251, 113, 133);  // #fb7185

struct AppState {
    StopwatchEngine engine;
    int dpi = 96;

    HWND hwnd = nullptr;
    HWND btn_start = nullptr;
    HWND btn_lap = nullptr;
    HWND btn_reset = nullptr;
    HWND list_laps = nullptr;

    HBRUSH brush_bg = nullptr;
    HBRUSH brush_card = nullptr;

    HFONT font_header = nullptr;
    HFONT font_badge = nullptr;
    HFONT font_time = nullptr;
    HFONT font_centi = nullptr;
    HFONT font_subtime = nullptr;
    HFONT font_btn = nullptr;
    HFONT font_table_hdr = nullptr;
    HFONT font_table_row = nullptr;
    HFONT font_footer = nullptr;

    RECT rect_display_card{};
    RECT rect_status_badge{};
    RECT rect_laps_count{};
    RECT rect_table_frame{};
    RECT rect_table_header{};
    RECT rect_footer{};

    int fastest_lap_idx = -1;
    int slowest_lap_idx = -1;

    int s(int px) const { return MulDiv(px, dpi, 96); }
};

HFONT create_font(int pt_size, int weight, const wchar_t* face, int dpi) {
    const int height = -MulDiv(pt_size, dpi, 72);
    return CreateFontW(height, 0, 0, 0, weight, FALSE, FALSE, FALSE,
                       DEFAULT_CHARSET, OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS,
                       CLEARTYPE_QUALITY, DEFAULT_PITCH | FF_DONTCARE, face);
}

void update_extremes(AppState& state) {
    state.fastest_lap_idx = -1;
    state.slowest_lap_idx = -1;
    const auto& laps = state.engine.laps();
    if (laps.size() < 2) {
        return;
    }
    const auto [min_it, max_it] = std::minmax_element(
        laps.begin(), laps.end(),
        [](const LapRecord& a, const LapRecord& b) {
            return a.lap_seconds < b.lap_seconds;
        });
    if (min_it->lap_seconds == max_it->lap_seconds) {
        return;
    }
    state.fastest_lap_idx = min_it->index;
    state.slowest_lap_idx = max_it->index;
}

void rebuild_laps_list(AppState& state) {
    SendMessageW(state.list_laps, WM_SETREDRAW, FALSE, 0);
    ListView_DeleteAllItems(state.list_laps);
    update_extremes(state);

    const auto& laps = state.engine.laps();
    int row = 0;
    for (auto it = laps.rbegin(); it != laps.rend(); ++it) {
        wchar_t idx_buf[16];
        std::swprintf(idx_buf, 16, L"%02d", it->index);
        std::wstring split_str = format_time_w(it->lap_seconds);
        std::wstring total_str = format_time_w(it->total_seconds);

        LVITEMW item{};
        item.mask = LVIF_TEXT | LVIF_PARAM;
        item.iItem = row;
        item.pszText = idx_buf;
        item.lParam = static_cast<LPARAM>(it->index);
        ListView_InsertItem(state.list_laps, &item);

        ListView_SetItemText(state.list_laps, row, 1, split_str.data());
        ListView_SetItemText(state.list_laps, row, 2, total_str.data());
        ++row;
    }

    SendMessageW(state.list_laps, WM_SETREDRAW, TRUE, 0);
    InvalidateRect(state.list_laps, nullptr, TRUE);
}

void refresh_controls(AppState& state) {
    const bool running = state.engine.is_running();
    const double elapsed = state.engine.elapsed_seconds();

    if (running) {
        SetWindowTextW(state.btn_start, L"Pausar");
    } else if (elapsed > 0.0) {
        SetWindowTextW(state.btn_start, L"Retomar");
    } else {
        SetWindowTextW(state.btn_start, L"Iniciar");
    }

    const bool can_lap = running || elapsed > 0.0;
    EnableWindow(state.btn_lap, can_lap ? TRUE : FALSE);

    const bool can_reset =
        running || elapsed > 0.0 || !state.engine.laps().empty();
    EnableWindow(state.btn_reset, can_reset ? TRUE : FALSE);

    InvalidateRect(state.btn_start, nullptr, FALSE);
    InvalidateRect(state.btn_lap, nullptr, FALSE);
    InvalidateRect(state.btn_reset, nullptr, FALSE);
    InvalidateRect(state.hwnd, &state.rect_display_card, FALSE);
    InvalidateRect(state.hwnd, &state.rect_status_badge, FALSE);
    InvalidateRect(state.hwnd, &state.rect_laps_count, FALSE);
}

void handle_toggle(AppState& state) {
    if (state.engine.toggle()) {
        SetTimer(state.hwnd, kTimerId, kRefreshIntervalMs, nullptr);
    } else {
        KillTimer(state.hwnd, kTimerId);
    }
    refresh_controls(state);
}

void handle_lap(AppState& state) {
    if (!state.engine.is_running() && state.engine.elapsed_seconds() == 0.0) {
        return;
    }
    state.engine.lap();
    rebuild_laps_list(state);
    refresh_controls(state);
}

void handle_reset(AppState& state) {
    KillTimer(state.hwnd, kTimerId);
    state.engine.reset();
    rebuild_laps_list(state);
    refresh_controls(state);
}

void layout_children(AppState& state, int width, int height) {
    const int pad_x = state.s(24);
    const int pad_y = state.s(20);
    const int content_w = std::max(100, width - pad_x * 2);

    const int header_h = state.s(26);
    state.rect_status_badge = {width - pad_x - state.s(110), pad_y,
                               width - pad_x, pad_y + header_h};

    const int card_top = pad_y + header_h + state.s(12);
    const int card_h = state.s(136);
    state.rect_display_card = {pad_x, card_top, pad_x + content_w,
                               card_top + card_h};

    const int btn_top = card_top + card_h + state.s(16);
    const int btn_h = state.s(42);
    const int gap = state.s(12);
    const int btn_w = (content_w - gap * 2) / 3;
    const int btn_reset_w = content_w - btn_w * 2 - gap * 2;

    MoveWindow(state.btn_start, pad_x, btn_top, btn_w, btn_h, TRUE);
    MoveWindow(state.btn_lap, pad_x + btn_w + gap, btn_top, btn_w, btn_h, TRUE);
    MoveWindow(state.btn_reset, pad_x + (btn_w + gap) * 2, btn_top, btn_reset_w,
               btn_h, TRUE);

    const int laps_hdr_top = btn_top + btn_h + state.s(18);
    const int laps_hdr_h = state.s(22);
    state.rect_laps_count = {width - pad_x - state.s(110), laps_hdr_top,
                             width - pad_x, laps_hdr_top + laps_hdr_h};

    const int footer_h = state.s(20);
    const int footer_top = height - pad_y - footer_h;
    state.rect_footer = {pad_x, footer_top, pad_x + content_w,
                         footer_top + footer_h};

    const int table_top = laps_hdr_top + laps_hdr_h + state.s(6);
    const int table_bottom = std::max(table_top + state.s(80),
                                      footer_top - state.s(10));
    state.rect_table_frame = {pad_x, table_top, pad_x + content_w, table_bottom};

    const int col_hdr_h = state.s(28);
    state.rect_table_header = {pad_x + 1, table_top + 1, pad_x + content_w - 1,
                               table_top + 1 + col_hdr_h};

    const int list_x = pad_x + 1;
    const int list_y = table_top + 1 + col_hdr_h;
    const int list_w = std::max(50, content_w - 2);
    const int list_h = std::max(40, table_bottom - 1 - list_y);
    MoveWindow(state.list_laps, list_x, list_y, list_w, list_h, TRUE);

    const int col0 = state.s(56);
    const int remaining = std::max(80, list_w - col0 - GetSystemMetrics(SM_CXVSCROLL) - 4);
    const int col1 = remaining / 2;
    const int col2 = remaining - col1;
    ListView_SetColumnWidth(state.list_laps, 0, col0);
    ListView_SetColumnWidth(state.list_laps, 1, col1);
    ListView_SetColumnWidth(state.list_laps, 2, col2);
}

void draw_button(const AppState& state, const DRAWITEMSTRUCT* dis) {
    HDC hdc = dis->hDC;
    RECT rc = dis->rcItem;
    const bool disabled = (dis->itemState & ODS_DISABLED) != 0;
    const bool pressed = (dis->itemState & ODS_SELECTED) != 0;

    COLORREF bg = kBtnDisabledBg;
    COLORREF fg = kBtnDisabledFg;

    if (!disabled) {
        if (dis->CtlID == kIdBtnStart) {
            bg = state.engine.is_running() ? kAccentPause : kAccentStart;
            fg = kBgMain;
        } else if (dis->CtlID == kIdBtnLap) {
            bg = kAccentLap;
            fg = kBgMain;
        } else if (dis->CtlID == kIdBtnReset) {
            bg = kAccentReset;
            fg = kFgPrimary;
        }
        if (pressed) {
            bg = RGB(
                static_cast<BYTE>(GetRValue(bg) * 85 / 100),
                static_cast<BYTE>(GetGValue(bg) * 85 / 100),
                static_cast<BYTE>(GetBValue(bg) * 85 / 100));
        }
    }

    HBRUSH fill = CreateSolidBrush(bg);
    FillRect(hdc, &rc, fill);
    DeleteObject(fill);

    wchar_t text[64]{};
    GetWindowTextW(dis->hwndItem, text, 64);

    SetBkMode(hdc, TRANSPARENT);
    SetTextColor(hdc, fg);
    HFONT old_font = static_cast<HFONT>(SelectObject(hdc, state.font_btn));
    DrawTextW(hdc, text, -1, &rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    SelectObject(hdc, old_font);
}

void paint_window(AppState& state, HDC target_dc, const RECT& client) {
    const int w = client.right - client.left;
    const int h = client.bottom - client.top;
    if (w <= 0 || h <= 0) {
        return;
    }

    HDC mem_dc = CreateCompatibleDC(target_dc);
    HBITMAP bmp = CreateCompatibleBitmap(target_dc, w, h);
    HBITMAP old_bmp = static_cast<HBITMAP>(SelectObject(mem_dc, bmp));

    FillRect(mem_dc, &client, state.brush_bg);
    SetBkMode(mem_dc, TRANSPARENT);

    const int pad_x = state.s(24);
    const int pad_y = state.s(20);

    // Header title
    RECT hdr_rc{pad_x, pad_y, state.rect_status_badge.left - state.s(8),
                state.rect_status_badge.bottom};
    SelectObject(mem_dc, state.font_header);
    SetTextColor(mem_dc, kFgMuted);
    DrawTextW(mem_dc, L"CRONÔMETRO", -1, &hdr_rc,
              DT_LEFT | DT_VCENTER | DT_SINGLELINE);

    // Status badge
    const bool running = state.engine.is_running();
    const double elapsed = state.engine.elapsed_seconds();
    const wchar_t* status_text = L"Pronto";
    COLORREF status_color = kFgMuted;
    if (running) {
        status_text = L"Em execução";
        status_color = kAccentStart;
    } else if (elapsed > 0.0) {
        status_text = L"Pausado";
        status_color = kAccentPause;
    }

    FillRect(mem_dc, &state.rect_status_badge, state.brush_card);
    SelectObject(mem_dc, state.font_badge);
    SetTextColor(mem_dc, status_color);
    RECT badge_rc = state.rect_status_badge;
    DrawTextW(mem_dc, status_text, -1, &badge_rc,
              DT_CENTER | DT_VCENTER | DT_SINGLELINE);

    // Display card background + 1px border
    FillRect(mem_dc, &state.rect_display_card, state.brush_card);
    HPEN border_pen = CreatePen(PS_SOLID, 1, kBorderSlate);
    HPEN old_pen = static_cast<HPEN>(SelectObject(mem_dc, border_pen));
    HBRUSH old_brush = static_cast<HBRUSH>(
        SelectObject(mem_dc, GetStockObject(NULL_BRUSH)));
    Rectangle(mem_dc, state.rect_display_card.left,
              state.rect_display_card.top, state.rect_display_card.right,
              state.rect_display_card.bottom);

    // Main time + centiseconds centered inside display card
    const std::wstring formatted = format_time_w(elapsed);
    const std::wstring hms = formatted.substr(0, 8);
    const std::wstring centi = formatted.substr(8);

    SelectObject(mem_dc, state.font_time);
    SIZE hms_size{};
    GetTextExtentPoint32W(mem_dc, hms.c_str(), static_cast<int>(hms.size()),
                          &hms_size);

    SelectObject(mem_dc, state.font_centi);
    SIZE centi_size{};
    GetTextExtentPoint32W(mem_dc, centi.c_str(), static_cast<int>(centi.size()),
                          &centi_size);

    const int total_time_w = hms_size.cx + centi_size.cx;
    const int card_center_x =
        (state.rect_display_card.left + state.rect_display_card.right) / 2;
    const int time_x = card_center_x - total_time_w / 2;
    const int time_y = state.rect_display_card.top + state.s(26);

    SelectObject(mem_dc, state.font_time);
    SetTextColor(mem_dc, kFgPrimary);
    RECT hms_rc{time_x, time_y, time_x + hms_size.cx, time_y + hms_size.cy};
    DrawTextW(mem_dc, hms.c_str(), -1, &hms_rc, DT_LEFT | DT_SINGLELINE);

    SelectObject(mem_dc, state.font_centi);
    SetTextColor(mem_dc, kAccentLap);
    const int centi_y = time_y + hms_size.cy - centi_size.cy - state.s(6);
    RECT centi_rc{time_x + hms_size.cx, centi_y,
                  time_x + total_time_w, centi_y + centi_size.cy};
    DrawTextW(mem_dc, centi.c_str(), -1, &centi_rc, DT_LEFT | DT_SINGLELINE);

    // Current lap label
    const auto& laps = state.engine.laps();
    const double last_total = laps.empty() ? 0.0 : laps.back().total_seconds;
    const double current_lap = std::max(0.0, elapsed - last_total);
    const std::wstring current_lap_text =
        L"Volta atual: " + format_time_w(current_lap);
    SelectObject(mem_dc, state.font_subtime);
    SetTextColor(mem_dc, kFgMuted);
    RECT sub_rc{state.rect_display_card.left, time_y + hms_size.cy + state.s(10),
                state.rect_display_card.right, state.rect_display_card.bottom};
    DrawTextW(mem_dc, current_lap_text.c_str(), -1, &sub_rc,
              DT_CENTER | DT_TOP | DT_SINGLELINE);

    // Laps section header
    SelectObject(mem_dc, state.font_table_hdr);
    SetTextColor(mem_dc, kFgMuted);
    RECT laps_lbl_rc{pad_x, state.rect_laps_count.top,
                     state.rect_laps_count.left - state.s(8),
                     state.rect_laps_count.bottom};
    DrawTextW(mem_dc, L"VOLTAS REGISTRADAS", -1, &laps_lbl_rc,
              DT_LEFT | DT_VCENTER | DT_SINGLELINE);

    wchar_t count_buf[32];
    const size_t count = laps.size();
    std::swprintf(count_buf, 32, L"%zu %ls", count,
                  count == 1 ? L"volta" : L"voltas");
    SelectObject(mem_dc, state.font_footer);
    RECT cnt_rc = state.rect_laps_count;
    DrawTextW(mem_dc, count_buf, -1, &cnt_rc,
              DT_RIGHT | DT_VCENTER | DT_SINGLELINE);

    // Table frame border & dark column header
    Rectangle(mem_dc, state.rect_table_frame.left, state.rect_table_frame.top,
              state.rect_table_frame.right, state.rect_table_frame.bottom);
    FillRect(mem_dc, &state.rect_table_header, state.brush_bg);

    const int col0 = state.s(56);
    const int hdr_w = state.rect_table_header.right - state.rect_table_header.left;
    const int rem = std::max(80, hdr_w - col0 - GetSystemMetrics(SM_CXVSCROLL) - 4);
    const int col1 = rem / 2;
    const int col2 = rem - col1;

    SelectObject(mem_dc, state.font_table_hdr);
    SetTextColor(mem_dc, kFgMuted);
    RECT c0{state.rect_table_header.left, state.rect_table_header.top,
            state.rect_table_header.left + col0, state.rect_table_header.bottom};
    RECT c1{c0.right, state.rect_table_header.top, c0.right + col1,
            state.rect_table_header.bottom};
    RECT c2{c1.right, state.rect_table_header.top, c1.right + col2,
            state.rect_table_header.bottom};
    DrawTextW(mem_dc, L"#", -1, &c0, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    DrawTextW(mem_dc, L"Tempo da Volta", -1, &c1,
              DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    DrawTextW(mem_dc, L"Tempo Total", -1, &c2,
              DT_CENTER | DT_VCENTER | DT_SINGLELINE);

    // Footer shortcuts hint
    SelectObject(mem_dc, state.font_footer);
    SetTextColor(mem_dc, kFgMuted);
    RECT ftr_rc = state.rect_footer;
    DrawTextW(mem_dc,
              L"Atalhos: Espaço (Iniciar/Pausar)  •  V (Volta)  •  R (Zerar)",
              -1, &ftr_rc, DT_CENTER | DT_VCENTER | DT_SINGLELINE);

    SelectObject(mem_dc, old_brush);
    SelectObject(mem_dc, old_pen);
    DeleteObject(border_pen);

    BitBlt(target_dc, 0, 0, w, h, mem_dc, 0, 0, SRCCOPY);
    SelectObject(mem_dc, old_bmp);
    DeleteObject(bmp);
    DeleteDC(mem_dc);
}

LRESULT handle_listview_custom_draw(const AppState& state,
                                    NMLVCUSTOMDRAW* lvcd) {
    switch (lvcd->nmcd.dwDrawStage) {
        case CDDS_PREPAINT:
            return CDRF_NOTIFYITEMDRAW;
        case CDDS_ITEMPREPAINT: {
            const int row = static_cast<int>(lvcd->nmcd.dwItemSpec);
            const int lap_idx = static_cast<int>(lvcd->nmcd.lItemlParam);

            lvcd->clrTextBk = (row % 2 == 1) ? kBgRowAlt : kBgCard;
            if (lap_idx == state.fastest_lap_idx) {
                lvcd->clrText = kFastestColor;
            } else if (lap_idx == state.slowest_lap_idx) {
                lvcd->clrText = kSlowestColor;
            } else {
                lvcd->clrText = kFgPrimary;
            }
            return CDRF_NEWFONT;
        }
        default:
            return CDRF_DODEFAULT;
    }
}

LRESULT CALLBACK wnd_proc(HWND hwnd, UINT msg, WPARAM wparam, LPARAM lparam) {
    auto* state = reinterpret_cast<AppState*>(
        GetWindowLongPtrW(hwnd, GWLP_USERDATA));

    switch (msg) {
        case WM_CREATE: {
            auto* cs = reinterpret_cast<CREATESTRUCTW*>(lparam);
            state = static_cast<AppState*>(cs->lpCreateParams);
            state->hwnd = hwnd;
            SetWindowLongPtrW(hwnd, GWLP_USERDATA,
                              reinterpret_cast<LONG_PTR>(state));

            HDC hdc = GetDC(hwnd);
            state->dpi = GetDeviceCaps(hdc, LOGPIXELSX);
            ReleaseDC(hwnd, hdc);

            state->brush_bg = CreateSolidBrush(kBgMain);
            state->brush_card = CreateSolidBrush(kBgCard);

            state->font_header = create_font(10, FW_BOLD, L"Segoe UI", state->dpi);
            state->font_badge = create_font(9, FW_BOLD, L"Segoe UI", state->dpi);
            state->font_time = create_font(36, FW_BOLD, L"Consolas", state->dpi);
            state->font_centi = create_font(22, FW_BOLD, L"Consolas", state->dpi);
            state->font_subtime = create_font(10, FW_NORMAL, L"Consolas", state->dpi);
            state->font_btn = create_font(11, FW_BOLD, L"Segoe UI", state->dpi);
            state->font_table_hdr = create_font(9, FW_BOLD, L"Segoe UI", state->dpi);
            state->font_table_row = create_font(10, FW_NORMAL, L"Consolas", state->dpi);
            state->font_footer = create_font(9, FW_NORMAL, L"Segoe UI", state->dpi);

            state->btn_start = CreateWindowExW(
                0, L"BUTTON", L"Iniciar",
                WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_OWNERDRAW, 0, 0, 0, 0,
                hwnd, reinterpret_cast<HMENU>(static_cast<INT_PTR>(kIdBtnStart)),
                cs->hInstance, nullptr);

            state->btn_lap = CreateWindowExW(
                0, L"BUTTON", L"Volta",
                WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_OWNERDRAW, 0, 0, 0, 0,
                hwnd, reinterpret_cast<HMENU>(static_cast<INT_PTR>(kIdBtnLap)),
                cs->hInstance, nullptr);

            state->btn_reset = CreateWindowExW(
                0, L"BUTTON", L"Zerar",
                WS_CHILD | WS_VISIBLE | WS_TABSTOP | BS_OWNERDRAW, 0, 0, 0, 0,
                hwnd, reinterpret_cast<HMENU>(static_cast<INT_PTR>(kIdBtnReset)),
                cs->hInstance, nullptr);

            state->list_laps = CreateWindowExW(
                0, WC_LISTVIEWW, L"",
                WS_CHILD | WS_VISIBLE | LVS_REPORT | LVS_SINGLESEL |
                    LVS_NOCOLUMNHEADER,
                0, 0, 0, 0, hwnd,
                reinterpret_cast<HMENU>(static_cast<INT_PTR>(kIdListLaps)),
                cs->hInstance, nullptr);

            ListView_SetExtendedListViewStyle(
                state->list_laps, LVS_EX_FULLROWSELECT | LVS_EX_DOUBLEBUFFER);
            ListView_SetBkColor(state->list_laps, kBgCard);
            ListView_SetTextBkColor(state->list_laps, kBgCard);
            ListView_SetTextColor(state->list_laps, kFgPrimary);
            SendMessageW(state->list_laps, WM_SETFONT,
                         reinterpret_cast<WPARAM>(state->font_table_row), TRUE);

            LVCOLUMNW col{};
            col.mask = LVCF_FMT | LVCF_WIDTH | LVCF_TEXT;
            col.fmt = LVCFMT_CENTER;
            col.cx = 60;
            col.pszText = const_cast<wchar_t*>(L"#");
            ListView_InsertColumn(state->list_laps, 0, &col);
            col.cx = 160;
            col.pszText = const_cast<wchar_t*>(L"Tempo da Volta");
            ListView_InsertColumn(state->list_laps, 1, &col);
            col.cx = 160;
            col.pszText = const_cast<wchar_t*>(L"Tempo Total");
            ListView_InsertColumn(state->list_laps, 2, &col);

            refresh_controls(*state);
            return 0;
        }

        case WM_SIZE: {
            if (state) {
                layout_children(*state, LOWORD(lparam), HIWORD(lparam));
                InvalidateRect(hwnd, nullptr, FALSE);
            }
            return 0;
        }

        case WM_GETMINMAXINFO: {
            if (state) {
                auto* mmi = reinterpret_cast<MINMAXINFO*>(lparam);
                mmi->ptMinTrackSize.x = state->s(400);
                mmi->ptMinTrackSize.y = state->s(480);
            }
            return 0;
        }

        case WM_TIMER: {
            if (state && wparam == kTimerId) {
                InvalidateRect(hwnd, &state->rect_display_card, FALSE);
            }
            return 0;
        }

        case WM_COMMAND: {
            if (!state) {
                break;
            }
            const int id = LOWORD(wparam);
            if (id == kIdBtnStart) {
                handle_toggle(*state);
            } else if (id == kIdBtnLap) {
                handle_lap(*state);
            } else if (id == kIdBtnReset) {
                handle_reset(*state);
            }
            return 0;
        }

        case WM_DRAWITEM: {
            if (state) {
                auto* dis = reinterpret_cast<const DRAWITEMSTRUCT*>(lparam);
                draw_button(*state, dis);
                return TRUE;
            }
            break;
        }

        case WM_NOTIFY: {
            if (state) {
                auto* hdr = reinterpret_cast<NMHDR*>(lparam);
                if (hdr->idFrom == kIdListLaps && hdr->code == NM_CUSTOMDRAW) {
                    return handle_listview_custom_draw(
                        *state, reinterpret_cast<NMLVCUSTOMDRAW*>(lparam));
                }
            }
            break;
        }

        case WM_ERASEBKGND:
            return 1;

        case WM_PAINT: {
            PAINTSTRUCT ps{};
            HDC hdc = BeginPaint(hwnd, &ps);
            if (state) {
                RECT client{};
                GetClientRect(hwnd, &client);
                paint_window(*state, hdc, client);
            }
            EndPaint(hwnd, &ps);
            return 0;
        }

        case WM_DESTROY: {
            if (state) {
                KillTimer(hwnd, kTimerId);
                DeleteObject(state->brush_bg);
                DeleteObject(state->brush_card);
                DeleteObject(state->font_header);
                DeleteObject(state->font_badge);
                DeleteObject(state->font_time);
                DeleteObject(state->font_centi);
                DeleteObject(state->font_subtime);
                DeleteObject(state->font_btn);
                DeleteObject(state->font_table_hdr);
                DeleteObject(state->font_table_row);
                DeleteObject(state->font_footer);
            }
            PostQuitMessage(0);
            return 0;
        }
    }

    return DefWindowProcW(hwnd, msg, wparam, lparam);
}

}  // namespace

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE, PWSTR, int show_cmd) {
    SetProcessDPIAware();

    INITCOMMONCONTROLSEX icc{sizeof(icc), ICC_LISTVIEW_CLASSES};
    InitCommonControlsEx(&icc);

    AppState state{};

    WNDCLASSEXW wc{};
    wc.cbSize = sizeof(wc);
    wc.lpfnWndProc = wnd_proc;
    wc.hInstance = instance;
    wc.hCursor = LoadCursorW(nullptr, IDC_ARROW);
    wc.lpszClassName = L"CronometroWin32Class";
    RegisterClassExW(&wc);

    HDC screen = GetDC(nullptr);
    const int dpi = GetDeviceCaps(screen, LOGPIXELSX);
    ReleaseDC(nullptr, screen);

    const int init_w = MulDiv(480, dpi, 96);
    const int init_h = MulDiv(600, dpi, 96);

    HWND hwnd = CreateWindowExW(
        0, wc.lpszClassName, L"Cronômetro",
        WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN, CW_USEDEFAULT, CW_USEDEFAULT,
        init_w, init_h, nullptr, nullptr, instance, &state);
    if (!hwnd) {
        return 1;
    }

    ShowWindow(hwnd, show_cmd);
    UpdateWindow(hwnd);

    MSG msg{};
    while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
        if (msg.message == WM_KEYDOWN) {
            if (msg.wParam == VK_SPACE) {
                handle_toggle(state);
                continue;
            }
            if (msg.wParam == 'V') {
                handle_lap(state);
                continue;
            }
            if (msg.wParam == 'R') {
                handle_reset(state);
                continue;
            }
        }
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    return static_cast<int>(msg.wParam);
}
