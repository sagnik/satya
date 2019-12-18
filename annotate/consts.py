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
SHORTCUT_ENTITIES_KEY = "entity_shortcuts"
ENTITY_COLORS_KEY = "entity_colors"
RELATIONS_KEY = "relations"
SHORTCUT_RELATIONS_KEY = "relation_shortcuts"
PARENT_TITLE = "Span Annotator"
TAG_START_B = "/B-"
TAG_START_I = "/I-"

# special keys
UNDO_KEY = "<Control-z>"
UNDO_COMMAND = "undo"
UN_LABEL_KEY = "<Control-q>"
UN_LABEL_COMMAND = "un-label"
RE_LABEL_KEY = "<Control-r>"
RE_LABEL_COMMAND = "re-label"
HIGHLIGHT_KEY = "<Control-h>"
HIGHLIGHT_COMMAND = "highlight"
RELATION_ENTITY_KEY = "<Control-e>"
RELATION_ENTITY_COMMAND = "select-relation-entity"
SPECIAL_KEYS = [UNDO_KEY, UN_LABEL_KEY, RE_LABEL_KEY, HIGHLIGHT_KEY]
RESERVED_CHARS = [x.split("-")[1][0] for x in SPECIAL_KEYS]

# consts for typeahead
TYPE_AHEAD_LISTBOX_HEIGHT = 5
TYPE_AHEAD_LISTBOX_WIDTH = 25
TYPE_AHEAD_ENTRY_WIDTH = 25
TYPE_AHEAD_NO_RESULTS_MESSAGE = "No results found for '{0:}'"

TKINTER_COLORS = ['peach_puff', 'gold', 'cyan2']
DEFAULT_HIGHLIGHT_COLOR = 'yellow'
FILE_TYPE_JSON = '.json'
FILE_TYPE_TXT = '.txt'
FILE_TYPE_CONLL = '.conll'
ALLOWED_FILE_TYPE = [FILE_TYPE_JSON, FILE_TYPE_TXT, FILE_TYPE_CONLL]
