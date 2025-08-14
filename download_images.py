import os
from pathlib import Path
import urllib.request

BASE = Path(__file__).parent
IMG = BASE / "content" / "images"
IMG.mkdir(parents=True, exist_ok=True)

# Публичные источники (Wikimedia Commons / учебные примеры / схемы)
urls = {
    "day01_bybit_interface.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Candlestick_chart_scheme_01-en.svg/640px-Candlestick_chart_scheme_01-en.svg.png",
    "day01_candles.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Candlestick_chart_illustration.png/640px-Candlestick_chart_illustration.png",
    "day02_timeframes.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Time_series.png/640px-Time_series.png",
    "day03_order_form.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5a/Order_book_example_depth_chart.png/640px-Order_book_example_depth_chart.png",
    "day04_size.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Bitcoin_sign.svg/640px-Bitcoin_sign.svg.png",
    "day05_sltp.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Support_and_resistance.svg/640px-Support_and_resistance.svg.png",
    "day06_orderbook.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Order_book.png/640px-Order_book.png",
    "day07_quiz.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Check_green_circle.svg/512px-Check_green_circle.svg.png",
    "day08_candle.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/67/Candlestick-chart.svg/640px-Candlestick-chart.svg.png",
    "day09_levels.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Support_and_resistance.svg/640px-Support_and_resistance.svg.png",
    "day10_trendline.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Trend_line.svg/640px-Trend_line.svg.png",
    "day11_patterns.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Candlestick_pattern_bearish_engulfing.svg/640px-Candlestick_pattern_bearish_engulfing.svg.png",
    "day12_sma.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Moving_Average_Example.svg/640px-Moving_Average_Example.svg.png",
    "day13_rsi.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Relative_Strength_Index.svg/640px-Relative_Strength_Index.svg.png",
    "day14_quiz.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Check_green_circle.svg/512px-Check_green_circle.svg.png",
    "day15_risk.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Risk_management_cycle.svg/640px-Risk_management_cycle.svg.png",
    "day16_rr.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Reward_system_concept.svg/640px-Reward_system_concept.svg.png",
    "day17_checklist.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/72/Checklist_icon.svg/512px-Checklist_icon.svg.png",
    "day18_journal.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Notebook_icon.svg/512px-Notebook_icon.svg.png",
    "day19_psych.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Psychology_icon.svg/512px-Psychology_icon.svg.png",
    "day20_discipline.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Stop_hand_nuvola.svg/512px-Stop_hand_nuvola.svg.png",
    "day21_quiz.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Check_green_circle.svg/512px-Check_green_circle.svg.png",
    "day22_strategy.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Support_and_resistance.svg/640px-Support_and_resistance.svg.png",
    "day23_filter.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Moving_Average_Example.svg/640px-Moving_Average_Example.svg.png",
    "day24_breakout.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6a/Breakout_chart.svg/640px-Breakout_chart.svg.png",
    "day25_be.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/No-Sign.svg/512px-No-Sign.svg.png",
    "day26_partial.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Pie_chart_simple.svg/512px-Pie_chart_simple.svg.png",
    "day27_history.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Stock_Price_Chart.png/640px-Stock_Price_Chart.png",
    "day28_demo.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Computer_n_screen.svg/512px-Computer_n_screen.svg.png",
    "day29_quiz.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Check_green_circle.svg/512px-Check_green_circle.svg.png",
    "day30_final.png": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Check_green_circle.svg/512px-Check_green_circle.svg.png"
}

for fname, url in urls.items():
    path = IMG / fname
    if not path.exists():
        try:
            print(f"Downloading {fname} ...")
            urllib.request.urlretrieve(url, path)
        except Exception as e:
            print(f"Failed {fname}: {e}")
    else:
        print(f"Exists {fname}")

print("Done.")
