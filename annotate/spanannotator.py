import tkinter as tk
from tkinter import Text
from typing import List
from tkinter.ttk import Frame, Button, Label, Scrollbar
from tkinter.constants import *
from annotate.consts import *
from tkinter.filedialog import Open as tkfileopen
from tkinter.font import Font
from collections import deque
from annotate.utils import biofy, de_biofy, is_labeled, towkf
from annotate.autocomplete import AutocompleteEntry


class SpanAnnotatorFrame(Frame):
    def __init__(self, parent, config, **kwargs):
        """create a span annotator frame object: this will hold the text area and the shortcuts and stuff
        :param parent: parent frame
        :param config: configuration dictionary, typically stores the labels and shortcuts
        """
        super().__init__()
        self.parent = parent
        self.file_name = ""
        self.debug = False
        self.color_all_chunk = True
        self.recommend_flag = True
        self.history = deque(maxlen=20)
        self.current_content = deque(maxlen=1)
        self.labels: List = config[LABELS_KEY]  # config must provide the labels
        self.label_shortcuts = config.get(SHORTCUT_LABELS_KEY, {})  # assign some keys to some common labels
        self.special_key_map = {HIGHLIGHT_KEY: HIGHLIGHT_COMMAND, UNDO_KEY: UNDO_COMMAND,
                                UN_LABEL_KEY: UN_LABEL_COMMAND, RE_LABEL_KEY: RE_LABEL_COMMAND}
        self.file_name = kwargs.get('input_file')
        
        # define the ui components here. the values will be set later
        self.text_row = None
        self.text_column = None
        self.entity_color = None
        self.inside_nest_entity_color = None
        self.recommend_color = None
        self.select_color = None
        self.text_font_style = None
        self.filename_lbl = None
        self.text = None
        self.cursor_index_lbl = None
        self.min_text_row = MIN_TEXT_ROW
        self.min_text_column = MIN_TEXT_COL
        self.type_ahead_entry = None
        self.fnt = None
        self.msg_lbl = None
        self.type_ahead_string_replace = TYPE_AHEAD
        self.all_input_keys = ALL_INPUT_KEYS
        self.init_ui()

    def init_ui(self):
        """initialize the UI and bind the appropriate keys.
        :return:
        """
        if len(self.label_shortcuts) > self.min_text_row:
            self.text_row = len(self.label_shortcuts)
        else:
            self.text_row = self.min_text_row
        self.text_column = self.min_text_column

        self.entity_color = SKY_BLUE
        self.inside_nest_entity_color = LIGHT_BLUE
        self.recommend_color = LIGHT_GREEN
        self.select_color = LIGHT_SALMON
        self.text_font_style = FONT_TIMES

        self.parent.title(PARENT_TITLE)
        self.pack(fill=BOTH, expand=True)

        for idx in range(0, self.text_column):
            self.columnconfigure(idx, weight=2)
        self.columnconfigure(self.text_column + 2, weight=1)
        self.columnconfigure(self.text_column + 4, weight=1)
        for idx in range(0, self.text_row):
            self.rowconfigure(idx, weight=1)

        self.filename_lbl = Label(self, text='File: no file is opened')
        self.filename_lbl.grid(sticky=W, pady=4, padx=5)

        self.fnt = Font(family=self.text_font_style, size=self.text_row, weight='bold', underline=0)
        self.text = Text(self, font=self.fnt, selectbackground=self.select_color)
        self.text.grid(
            row=1, column=0, columnspan=self.text_column, rowspan=self.text_row, padx=12, sticky=E + W + S + N
        )
        sb = Scrollbar(self)
        sb.grid(row=1, column=self.text_column, rowspan=self.text_row, padx=0, sticky=E + W + S + N)
        self.text['yscrollcommand'] = sb.set
        sb['command'] = self.text.yview

        open_button = Button(self, text='Open', command=self.open_file_dialog_read_file)
        open_button.grid(row=1, column=self.text_column + 1)

        export_button = Button(self, text='Export', command=self.export)
        export_button.grid(row=6, column=self.text_column + 1, pady=4)

        quit_button = Button(self, text='Quit', command=self.quit)
        quit_button.grid(row=7, column=self.text_column + 1, pady=4)

        cursor_name = Label(self, text='Cursor: ', foreground='Blue', font=(self.text_font_style, 14, 'bold'))
        cursor_name.grid(row=9, column=self.text_column + 1, pady=4)
        self.cursor_index_lbl = Label(
            self, text='row: 0\ncol: 0', foreground='red', font=(self.text_font_style, 14, 'bold')
        )
        self.cursor_index_lbl.grid(row=10, column=self.text_column + 1, pady=4)
        self.cursor_index_lbl.grid(row=10, column=self.text_column + 1, pady=4)

        self.msg_lbl = Label(self, text='[Message]:')
        self.msg_lbl.grid(row=self.text_row + 1, sticky=E + W + S + N, pady=4, padx=4)

        # all input keys are bound to type ahead
        for char_key in self.all_input_keys:
            self.text.bind(char_key, self.label_type_ahead)

        # bind shortcut keys
        for char_key in self.label_shortcuts:
            self.text.bind(f'<Control-{char_key}>', self.label_shortcut_press)
        self.show_shortcut_mapping()

        # bind special keys
        self.text.bind(UN_LABEL_KEY, self.un_label)
        self.text.bind(UNDO_KEY, self.undo)
        self.text.bind(RE_LABEL_KEY, self.re_label)
        self.text.bind(HIGHLIGHT_KEY, self.highlight)
        self.show_special_key_mapping()
        
        # bind arrow keys to show cursor positions
        for arrow_key in ['Left', 'Right', 'Up', 'Down']:
            self.text.bind(f'<{arrow_key}>', self.show_cursor_position)
            self.text.bind(f'<KeyRelease-{arrow_key}>', self.show_cursor_position)

        # if the input file is supplied, load that file in the text area
        if self.file_name is not None:
            self.set_file_content_text_area(self.file_name)
        
    def show_shortcut_mapping(self):
        """set up the shortcut mapping region in the UI
        :return:
        """
        row = 0

        map_label = Label(self, text='Shortcuts map Labels', foreground='red', font=(self.text_font_style, 14, 'bold'))
        map_label.grid(row=0, column=self.text_column + 2, columnspan=2, rowspan=1, padx=10)

        for key in sorted(self.label_shortcuts):
            row += 1
            symbol_label = Label(
                self, text=f'<ctrl-{key}>' + ': ', foreground='blue', font=(self.text_font_style, 14, 'bold')
            )
            symbol_label.grid(row=row, column=self.text_column + 2, columnspan=1, rowspan=1, padx=3)

            label_entry = tk.Entry(self, foreground='blue', font=(self.text_font_style, 14, 'bold'))
            label_entry.insert(0, self.label_shortcuts[key])
            label_entry.grid(row=row, column=self.text_column + 3, columnspan=1, rowspan=1)

    def show_special_key_mapping(self):
        """set up the special key mapping region in the UI
        :return:
        """
        row = len(self.label_shortcuts)+1
    
        map_label = Label(self, text='Special keys', foreground='red', font=(self.text_font_style, 14, 'bold'))
        map_label.grid(row=row, column=self.text_column + 2, columnspan=2, rowspan=1, padx=10)
    
        for key in self.special_key_map:
            row += 1
            symbol_label = Label(
                self, text=f'{key.lower()}' + ': ', foreground='blue', font=(self.text_font_style, 14, 'bold')
            )
            symbol_label.grid(row=row, column=self.text_column + 2, columnspan=1, rowspan=1, padx=3)
        
            label_entry = tk.Entry(self, foreground='blue', font=(self.text_font_style, 14, 'bold'))
            label_entry.insert(0, self.special_key_map[key])
            label_entry.grid(row=row, column=self.text_column + 3, columnspan=1, rowspan=1)

    def open_file_dialog_read_file(self):
        """open the file dialog, read the file, and set the content of the file in the textarea
        :return:
        """
        file_types = [('text files', '.txt'), ('ann files', '.ann'), ('all files', '*')]
        dlg = tkfileopen(self, filetypes=file_types)
        fl = dlg.show()
        if fl:
            self.set_file_name_read_data(fl)
            
    def set_file_content_text_area(self, file_name):
        """set a file content in the text area
        :return:
        """
        self.text.delete(TEXTAREA_START, TEXTAREA_END)
        text = self.set_file_name_read_data(file_name)
        self.text.insert(TEXTAREA_END, text)
        self.filename_lbl.config(text=file_name)
        self.set_cursor_label(self.text.index(INSERT))

    def show_cursor_position(self, event):
        """show the current cursor position in the cursor label + move the cursor in that index
        :param event: the event that caused this callback
        :return:
        """
        cursor_index = self.text.index(INSERT)
        self.text.mark_set(INSERT, cursor_index)
        self.text.see(cursor_index)
        self.set_cursor_label(cursor_index)

    def get_data_type_ahead(self, event, selected_text, selection_start, selection_end):
        """the user has pressed enter on the type ahead. get the label from the type ahead widget, close the type ahead window, label the selected string
        :param event: the event that caused this callback
        :param selected_text: selected text
        :param selection_start: cursor index for the start of the selected text
        :param selection_end: cursor index for the end of the selected text
        :return:
        """
        label = self.type_ahead_entry.text_.get()
        self.type_ahead_entry.destroy()
        self.label_selected_text(label, selected_text, selection_start, selection_end)

    def set_file_name_read_data(self, filename):
        """set the filename variable for the class and read the content
        :param filename:
        :return:
        """
        try:
            with open(filename, 'r') as rf:
                text = rf.read()
            self.file_name = filename
            return text
        except TypeError:
            return ''

    def set_cursor_label(self, cursor_index):
        """set the cursor label region with the current cursor position
        :param cursor_index:
        :return:
        """
        cursor_row, cursor_column = cursor_index.split(CURSOR_SEP)
        cursor_text = f'row: {cursor_row}\ncol: {cursor_column}'
        self.cursor_index_lbl.config(text=cursor_text)

    def re_label(self, event):
        """If there is a labeled text around the cursor, select the span. else do nothing
        :param event: the event that caused this callback to fire
        :return:
        """
        current_cursor = self.text.index(INSERT)
        current_row, current_col = [int(x) for x in current_cursor.split('.')]
        line = self.row_content(current_row)
        if not line.strip():
            return BREAK
        selection_start_col, selection_end_col = self.get_closest_labeled_text(line, current_col)
        if selection_start_col is None or selection_end_col is None:
            return BREAK
        selection_start = f'{current_row}.{selection_start_col}'
        selection_end = f'{current_row}.{selection_end_col}'
        selected_content = self.text.get(selection_start, selection_end)
        prev_length = len(selected_content)
        text_before_cursor = self.text.get(TEXTAREA_START, selection_start)
        text_after_cursor = self.text.get(selection_end, TEXTAREA_END)
        selected_content = de_biofy(selected_content, depth=1)
        current_length = len(selected_content)
        cursor_move = current_length - prev_length
        selection_end = f'{current_row}.{selection_end_col+cursor_move}'
        self.write_output_and_text_area(text_before_cursor + selected_content + text_after_cursor, selection_start)
        self.text.tag_add("sel", selection_start, selection_end)
        return BREAK

    def label_type_ahead(self, event):
        """creates a type ahead widget which allows us to find a label. before the widget is created, we look at the selected text.
        1. if no text is selected, do not show the type-ahead widget
        2. check the correctness of the selected text
        :param event: the event that caused this callback to fire
        :return:
        """
        press_key = event.keysym
        self.push_to_history()
        self.log(f'type ahead: {press_key}')
        if not self.text.tag_ranges(SEL):
            return BREAK
        allowed, selected_content, selection_start, selection_end = self.adjust_selection()
        if not allowed:
            return BREAK
        self.type_ahead_entry = AutocompleteEntry(self)
        self.type_ahead_entry.build(entries=self.labels, no_results_message=TYPE_AHEAD_NO_RESULTS_MESSAGE)
        self.type_ahead_entry.text_.set(press_key)
        self.type_ahead_entry.listbox.bind(
            '<Return>',
            lambda event_: self.get_data_type_ahead(event_, selected_content, selection_start, selection_end),
        )

        return BREAK

    def label_shortcut_press(self, event):
        """handle the event when a shortcut key for an annotation label has been pressed.
        1. if no text is selected, do nothing
        2. check the correctness of the selected text
        3. label the text
        :param event: the event that caused this callback to fire
        :return:
        """
        press_key = event.keysym
        self.push_to_history()
        self.log(f'shortcut: {press_key}')
        if not self.text.tag_ranges(SEL):
            return BREAK
        label = self.label_shortcuts[press_key.lower()]
        allowed, selected_content, selection_start, selection_end = self.adjust_selection()
        if not allowed:
            return BREAK
        self.label_selected_text(label, selected_content, selection_start, selection_end)
        return BREAK

    def un_label(self, event):
        """handle the event when <ctrl-q> has been pressed.
        1. if no text is selected, do nothing
        2. check the correctness of the selected text
        3. un-label the text.
        This method is pretty similar to label_shortcut_press, only the label is *NOT* obtained from the shortcut map
        :param event: the event that caused this callback to fire
        :return:
        """
        self.push_to_history()
        self.log(f'un-label')
        if not self.text.tag_ranges(SEL):
            return BREAK
        label = UN_LABEL_COMMAND
        allowed, selected_content, selection_start, selection_end = self.adjust_selection()
        if not allowed:
            return BREAK
        self.label_selected_text(label, selected_content, selection_start, selection_end)
        return BREAK

    def adjust_selection(self):
        """verify the selected text
        1. you can not select text spanning multiple rows
        2. if you select 'part' of a word, the selected text and the index is adjusted to capture the whole word.
        :return:
        """
        selected_content = self.text.selection_get()
        selection_start = self.text.index(SEL_FIRST)
        selection_end = self.text.index(SEL_LAST)
        begin_row, begin_col = [int(x) for x in selection_start.split(CURSOR_SEP)]
        end_row, end_col = [int(x) for x in selection_end.split(CURSOR_SEP)]
        if begin_row != end_row:
            self.log('Selected text must be in the same row', 'ERROR')
            return False, '_', '_', '_'
        move_left, move_right = True, True
        while move_left:
            if begin_col == 0 or self.text.get(f'{begin_row}.{begin_col-1}') == WORD_SEP:
                move_left = False
            else:
                selected_content = self.text.get(f'{begin_row}.{begin_col-1}') + selected_content
                begin_col -= 1
        while move_right:
            if (
                self.text.get(f'{begin_row}.{end_col}') == WORD_SEP
                or self.text.get(f'{begin_row}.{end_col}') == NEW_LINE_CHAR
            ):
                move_right = False
            else:
                selected_content = selected_content + self.text.get(f'{begin_row}.{end_col}')
                end_col += 1
        selection_start = f'{begin_row}.{begin_col}'
        selection_end = f'{begin_row}.{end_col}'
        return True, selected_content, selection_start, selection_end

    def undo(self, event):
        """handle the ctrl z event by loading the last text and cursor index back in the text area
        :param event: the event that happened
        :return:
        """
        if len(self.history) > 0:
            history_content, cursor_index = self.history.pop()
            self.write_output_and_text_area(history_content, cursor_index)
        else:
            self.log('History is empty!', ERROR)

    def log(self, msg: str, msg_type: str = INFO):
        """append a msg to the logging area
        :param msg: message
        :param msg_type: error/info/
        :return:
        """
        self.msg_lbl.config(text=f'{msg_type.upper()}: {msg}')

    def re_construct_content(self, text_before_cursor, text_after_cursor, selected_string, label, cursor_index):
        """a selected text is labeled and the cursor_index is updated to go to the position after the selected text. The user might have selected a text already labeled. if the pressed key was <ctrl+q>, unlabel that span. Otherwise label the selected string.
        :param text_before_cursor: text before current cursor position
        :param text_after_cursor: text after current cursor position (this includes the selected string)
        :param selected_string: the text selected by the cursor
        :param label: the label to be applied. if label is 'undo', try to deselect the selected content
        :param cursor_index: current cursor index
        :return: the content to be put on the text area, changed cursor index, lenghth of the selected text (for highlighting)
        """
        text_after_cursor = text_after_cursor[len(selected_string) :]  # we need to remove the selected string
        # since it will be added later to the text after modifications
        cursor_row, cursor_col = [int(x) for x in cursor_index.split(CURSOR_SEP)]
        # if the label is UNDO, check if the selected string is fully labeled. if not, do nothing.
        # if yes, remove the last label. if the label is not UNDO, label the selected string
        if label == UN_LABEL_COMMAND:
            if not is_labeled(selected_string, self.labels, text_after_cursor):  # do nothing
                self.log('You need to select a fully labeled string to remove the labels', ERROR)
                return text_before_cursor + selected_string + text_after_cursor, cursor_index, len(selected_string)
            else:
                prev_length = len(selected_string)
                selected_string = de_biofy(selected_string, depth=1)
                current_length = len(selected_string)
                cursor_move = current_length - prev_length
        else:
            prev_length = len(selected_string)
            selected_string = biofy(selected_string, label)
            current_length = len(selected_string)
            cursor_move = current_length - prev_length
        new_cursor_index = f'{cursor_row}.{cursor_col+cursor_move}'
        return text_before_cursor + selected_string + text_after_cursor, new_cursor_index, len(selected_string)

    def label_selected_text(self, label, selected_content, label_start_index, label_end_index):
        """we got a label from the labeling mechanism (type-ahead/shortcut), label the selected content with it
        :param label: label to apply
        :param selected_content: text to label
        :param label_start_index: cursor index of where the selected text begins
        :param label_end_index: cursor index of where the selected text ends
        :return:
        """
        # if there was a highlight tag configured, remove it.
        self.text.tag_delete(HIGHLIGHT_COMMAND)
        text_before_cursor = self.text.get(TEXTAREA_START, label_start_index)
        text_after_cursor = self.text.get(label_start_index, TEXTAREA_END)
        # re-construct the content and get the modified cursor index back
        content, label_end_index, selected_content_length = self.re_construct_content(
            text_before_cursor, text_after_cursor, selected_content, label, label_end_index
        )
        label_end_row, label_end_col = [int(x) for x in label_end_index.split('.')]
        # highlight the selected span
        self.write_output_and_text_area(content, label_end_index)
        self.text.tag_add(
            HIGHLIGHT_COMMAND, f'{label_end_row}.{label_end_col-selected_content_length}', label_end_index
        )
        self.text.tag_config(HIGHLIGHT_COMMAND, background="yellow", foreground="black" )

    def write_output_and_text_area(self, content, new_cursor_index):
        """write the changes to an ann file and load the written file to a text area (WYSIWYG). put the cursor index at the position of last index.
        :param content: content to be written
        :param new_cursor_index: updated cursor index
        :return:
        """
        self.text.delete(TEXTAREA_START, TEXTAREA_END)
        self.text.insert(TEXTAREA_END, content)
        self.text.mark_set(INSERT, new_cursor_index)
        self.text.see(new_cursor_index)
        self.set_cursor_label(new_cursor_index)
        if '.ann' not in self.file_name:
            file_name = f'{self.file_name}.ann'
        else:
            file_name = self.file_name  # if you were editing an ann file anyway
        with open(file_name, 'w') as f:
            f.write(content)

    def push_to_history(self):
        """push the current selected span and the cursor position to a queue
        :return:
        """
        content = self.text.get(TEXTAREA_START, TEXTAREA_END)
        cursor_position = self.text.index(INSERT)
        self.history.append((content, cursor_position))

    def get_closest_labeled_text(self, content, char_index):
        """for a given char position in the text return the start and the end index of the smallest enclosing text that is fully labeled
        content = 'barack/B-PER obama/I-PER was born in Hawaii/B-LOC in 1961/B-DATE',
        char_index = 5 => 0,23
        char_index = 54 => 53,64
        char_index = 65 => None, None
        char_index = 27 => None, None
        Note: This will only work if you have one level of labels, IOW, if your string is `a/B-x b/I-x/B-y c/I-x/I-y/B-z`, it will not work, because if your cursor is on b, it is not clear whether the correct span is `a/B-x b/I-x/B-y` or `b/I-x/B-y c/I-x/I-y/B-z`.
        :param content: text
        :param char_index: col index for cursor click
        :return: start and end col indices for the closest labeled span
        """
        max_label_depth = max([(word.count(TAG_START_B) + word.count(TAG_START_I)) for word in content.split(WORD_SEP)])
        if max_label_depth > 1:
            self.log('Labels can not be renamed when there are multiple levels', 'ERROR')
            return None, None
        if char_index == len(content):
            self.log('Can not put cursor at the end of a line', ERROR)
            return None, None
        char = content[char_index]
        if char == ' ':  # clicked on a space, move index to the left
            char_index -= 1
        start = 0
        word_start_ends = []
        for word in content.split(WORD_SEP):
            end = start + len(word)
            word_start_ends.append((word, start, end))
            start = end + 1
        starting_word = None
        start_word_index = None
        for index, (word, start, end) in enumerate(word_start_ends):
            if start <= char_index <= end:
                starting_word = word
                start_word_index = index
        if starting_word is None:
            self.log('No word can be selected', 'ERROR')
            return None, None
        if not (TAG_START_B in starting_word or TAG_START_I in starting_word):
            self.log('No word can be selected', 'ERROR')
            return None, None
        if TAG_START_I in starting_word:  # look left until B
            word_index = start_word_index
            while True:
                word_index -= 1
                if word_index < 0:
                    self.log('no span to relabel', ERROR)
                    return None, None
                if TAG_START_B in word_start_ends[word_index][0]:
                    break
            start_word_index = word_index
        # look right until O/content ends
        word_index = start_word_index
        while True:
            word_index += 1
            if word_index == len(word_start_ends) or TAG_START_I not in word_start_ends[word_index][0]:
                break
        end_word_index = word_index - 1
        return word_start_ends[start_word_index][1], word_start_ends[end_word_index][2]

    def export(self):
        """export the text area content in a conll BIO format
        if there are multiple levels of labels like george/B-PER/B-PRES bush/I-PER/I-PRES there will be multiple columns
        in the conll file, with `words` as the first column.
        :return:
        """
        if self.file_name.endswith('.ann'):
            file_name = f'{self.file_name[:-3]}.bio.conll'
        else:
            file_name = f'{self.file_name}.bio.conll'
        content = self.text.get(TEXTAREA_START, TEXTAREA_END)
        self.log(f'Writing output to {file_name}')
        towkf(content, file_name)

    def highlight(self, event):
        """highlight a span or de-highlight the highlighted area.
        :param event: the event key that caused this callback to fire
        :return:
        """
        if self.text.tag_ranges( HIGHLIGHT_COMMAND ):
            self.text.tag_delete( HIGHLIGHT_COMMAND )
            return BREAK
        if self.text.tag_ranges(SEL):
            sel_first = self.text.index(SEL_FIRST)
            sel_last = self.text.index(SEL_LAST)
        else:
            current_row, current_col = [int(x) for x in self.text.index(INSERT).split('.')]
            line = self.row_content(current_row)
            if not line:
                return BREAK
            label_start_row, label_end_row = self.get_closest_labeled_text(line, current_col)
            if label_start_row is None or label_end_row is None:
                return BREAK
            else:
                sel_first = f'{current_row}.{label_start_row}'
                sel_last = f'{current_row}.{label_end_row}'
        self.text.tag_add( HIGHLIGHT_COMMAND, sel_first, sel_last )
        self.text.tag_config( HIGHLIGHT_COMMAND, background="yellow", foreground="black" )
        return BREAK

    def row_content(self, current_row):
        """content of the current row
        :return:
        """
        line = ''
        col = 0
        while True:
            current_char = self.text.get(self.text.index(f'{current_row}.{col}'))
            if current_char == NEW_LINE_CHAR:
                break
            line += current_char
            col += 1
        return line
