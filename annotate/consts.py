SKY_BLUE = "SkyBlue1"
LIGHT_BLUE = "light slate blue"
LIGHT_GREEN = "lightgreen"
LIGHT_SALMON = "light salmon"
FONT_TIMES = "Times"
MIN_TEXT_ROW = 20
MIN_TEXT_COL = 5
TYPE_AHEAD = "TYPE_AHEAD"
BREAK = "break"
WORD_SEP = " "
CURSOR_SEP = "."
ERROR = "ERROR"
INFO = "INFO"
TEXTAREA_START = "1.0"  # in tkinter, the text actually starts from row 1, col 0
TEXTAREA_END = "end-1c"  # tkinter inserts a new line after the text. we dont need to remove it.
NEW_LINE_CHAR = "\n"
ALL_INPUT_KEYS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
ENTITIES_KEY = "entities"
RELATIONS_KEY = "relations"
PARENT_TITLE = "Span Annotator"
TAG_START_B = "/B-"
TAG_START_I = "/I-"

# special keys
UNDO_KEY = "<Control-z>"
UNDO_COMMAND = "undo"
UN_LABEL_KEY = "<Control-q>"
UN_LABEL_COMMAND = "un label entities"
SHOW_SPAN_INFO_KEY = "<Control-s>"
SHOW_SPAN_INFO_COMMAND = "show span info"
UN_LABEL_FROM_SPAN_INFO_AREA_KEY = "<Control-d>"
UN_LABEL_FROM_SPAN_INFO_AREA_COMMAND = "un label relations"
RELATION_ENTITY_KEY = "<Control-e>"
RELATION_ENTITY_COMMAND = "select-relation-entity"
SPECIAL_KEYS = [UNDO_KEY, UN_LABEL_KEY, SHOW_SPAN_INFO_KEY, UN_LABEL_FROM_SPAN_INFO_AREA_KEY, RELATION_ENTITY_KEY]
RESERVED_CHARS = [x.split("-")[1][0] for x in SPECIAL_KEYS]

# consts for typeahead
TYPE_AHEAD_LISTBOX_HEIGHT = 5
TYPE_AHEAD_LISTBOX_WIDTH = 25
TYPE_AHEAD_ENTRY_WIDTH = 25
TYPE_AHEAD_NO_RESULTS_MESSAGE = "No results found for '{0:}'"

DEFAULT_HIGHLIGHT_COLOR = 'yellow'
FILE_TYPE_JSON = '.json'
FILE_TYPE_TXT = '.txt'
FILE_TYPE_CONLL = '.conll'
ALLOWED_FILE_TYPE = [FILE_TYPE_JSON, FILE_TYPE_TXT, FILE_TYPE_CONLL]

TKINTER_COLORS = [
    'LightGreen',
    'DarkRed',
    'DarkMagenta',
    'DarkCyan',
    'DarkBlue',
    'DebianRed',
    'MediumPurple',
    'BlueViolet',
    'DarkViolet',
    'DarkOrchid',
    'MediumOrchid',
    'VioletRed',
    'MediumVioletRed',
    'PaleVioletRed',
    'LightPink',
    'DeepPink',
    'HotPink',
    'OrangeRed',
    'LightCoral',
    'DarkOrange',
    'LightSalmon',
    'DarkSalmon',
    'SandyBrown',
    'SaddleBrown',
    'IndianRed',
    'RosyBrown',
    'DarkGoldenrod',
    'LightGoldenrod',
    'LightYellow',
    'LightGoldenrodYellow',
    'PaleGoldenrod',
    'DarkKhaki',
    'OliveDrab',
    'ForestGreen',
    'YellowGreen',
    'LimeGreen',
    'GreenYellow',
    'MediumSpringGreen',
    'LawnGreen',
    'SpringGreen',
    'PaleGreen',
    'LightSeaGreen',
    'MediumSeaGreen',
    'SeaGreen',
    'DarkSeaGreen',
    'DarkOliveGreen',
    'DarkGreen',
    'MediumAquamarine',
    'CadetBlue',
    'LightCyan',
    'MediumTurquoise',
    'DarkTurquoise',
    'PaleTurquoise',
    'PowderBlue',
    'LightBlue',
    'LightSteelBlue',
    'SteelBlue',
    'LightSkyBlue',
    'SkyBlue',
    'DeepSkyBlue',
    'DodgerBlue',
    'RoyalBlue',
    'MediumBlue',
    'LightSlateBlue',
    'MediumSlateBlue',
    'SlateBlue',
    'DarkSlateBlue',
    'CornflowerBlue',
    'NavyBlue',
    'MidnightBlue',
    'MistyRose',
    'LavenderBlush',
    'AliceBlue',
    'MintCream',
    'LemonChiffon',
    'PeachPuff',
    'BlanchedAlmond',
    'PapayaWhip',
    'OldLace',
]
