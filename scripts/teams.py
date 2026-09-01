# NPB 公式サイトのチームコード → CSVの1文字略称
TEAM_CODE_TO_ABBR = {
    "s": "ヤ",
    "c": "広",
    "d": "中",
    "g": "巨",
    "t": "神",
    "db": "デ",
    "f": "日",
    "m": "ロ",
    "e": "楽",
    "h": "ソ",
    "l": "西",
    "b": "オ",
}

TEAMNAMES: tuple[str, ...] = (
    "神",
    "広",
    "デ",
    "巨",
    "ヤ",
    "中",
    "オ",
    "ロ",
    "ソ",
    "楽",
    "西",
    "日",
)
CENTRAL = TEAMNAMES[:6]
PACIFIC = TEAMNAMES[6:]
