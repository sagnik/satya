import os
import json
from typing import List, Tuple
import tkinter as tk
from tkinter import Text
from tkinter.ttk import Frame, Button, Label, Scrollbar
from tkinter.constants import *
from annotate.consts import *
from tkinter.filedialog import Open as tkfileopen
from tkinter.font import Font
from collections import deque
from annotate.utils import towkf, get_file_type
from annotate.autocomplete import AutocompleteEntry
from annotate.data import Tag, Span, Content


class SpanEntry(tk.Entry):
    def __init__(self, span: Span, tag: Tag, current_cursor: str, master=None, cnf={}, **kwargs):
        super().__init__(master, cnf, **kwargs)
        self.span = span
        self.tag = tag
        self.current_cursor = current_cursor


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
        self.labels = config[ENTITIES_KEY]  # config must provide the labels
        self.label_colors = config[ENTITY_COLORS_KEY]
        self.entity_shortcuts = config.get(SHORTCUT_ENTITIES_KEY, {})  # assign some keys to some common labels
        self.special_key_map = {
            HIGHLIGHT_KEY: HIGHLIGHT_COMMAND,
            UNDO_KEY: UNDO_COMMAND,
            UN_LABEL_KEY: UN_LABEL_COMMAND,
            SHOW_SPAN_INFO_KEY: SHOW_SPAN_INFO_COMMAND,
        }
        self.file_name = kwargs.get("input_file")

        # define the ui components here. the values will be set later
        self.text_row = None
        self.text_column = None
        self.select_color = None
        self.text_font_style = None
        self.text = None
        self.content = Content()
        self.cursor_index_lbl = None
        self.span_info_row_start = None
        self.span_info_entries = []
        self.min_text_row = MIN_TEXT_ROW
        self.min_text_column = MIN_TEXT_COL
        self.type_ahead_entry = None
        self.fnt = None
        self.msg_lbl = None
        self.span_relations_def_area = None
        self.type_ahead_string_replace = TYPE_AHEAD
        self.all_input_keys = ALL_INPUT_KEYS
        self.init_ui()

    def init_ui(self):
        """initialize the UI and bind the appropriate keys.
        :return:
        """
        if len(self.entity_shortcuts) > self.min_text_row:
            self.text_row = len(self.entity_shortcuts)
        else:
            self.text_row = self.min_text_row
        self.text_column = self.min_text_column

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

        self.fnt = Font(family=self.text_font_style, size=self.text_row, weight="bold", underline=0)
        self.text = Text(self, font=self.fnt, selectbackground=self.select_color)
        self.text.grid(
            row=1, column=0, columnspan=self.text_column, rowspan=self.text_row, padx=12, sticky=E + W + S + N
        )
        sb = Scrollbar(self)
        sb.grid(row=1, column=self.text_column, rowspan=self.text_row, padx=0, sticky=E + W + S + N)
        self.text["yscrollcommand"] = sb.set
        sb["command"] = self.text.yview

        open_button = Button(self, text="Open", command=self.open_file_dialog_read_file)
        open_button.grid(row=1, column=self.text_column + 1)

        export_button = Button(self, text="Export", command=self.export)
        export_button.grid(row=6, column=self.text_column + 1, pady=4)

        quit_button = Button(self, text="Quit", command=self.quit)
        quit_button.grid(row=7, column=self.text_column + 1, pady=4)

        cursor_name_row = 9
        cursor_name = Label(self, text="Cursor: ", foreground="Blue", font=(self.text_font_style, 14, "bold"))
        cursor_name.grid(row=cursor_name_row, column=self.text_column + 1, pady=4)
        self.cursor_index_lbl = Label(
            self, text="row: 0\ncol: 0", foreground="red", font=(self.text_font_style, 14, "bold")
        )

        self.cursor_index_lbl.grid(row=cursor_name_row + 1, column=self.text_column + 1, pady=4)

        self.span_info_row_start = (
            max((len(self.entity_shortcuts) + len(self.special_key_map), cursor_name_row + 1)) + 1
        )
        span_area_name = Label(self, text="Spans", foreground="Blue", font=(self.text_font_style, 14, "bold"))
        span_area_name.grid(row=self.span_info_row_start, column=self.text_column + 1, pady=4)

        self.msg_lbl = Label(self, text="[Message]:")
        self.msg_lbl.grid(row=self.text_row + 1, sticky=E + W + S + N, pady=4, padx=4)

        # all input keys are bound to type ahead
        for char_key in self.all_input_keys:
            self.text.bind(char_key, self.label_type_ahead)

        # bind shortcut keys
        for char_key in self.entity_shortcuts:
            self.text.bind(f'<Control-{char_key}>', self.label_shortcut_press)
        self.show_entity_shortcut_mapping()

        # bind special keys
        self.text.bind(UN_LABEL_KEY, self.un_label)
        self.text.bind(UNDO_KEY, self.undo)
        self.text.bind(HIGHLIGHT_KEY, self.highlight)
        self.text.bind(SHOW_SPAN_INFO_KEY, self.show_span_details)

        self.show_special_key_mapping()

        # bind arrow keys to show cursor positions
        for arrow_key in ['Left', 'Right', 'Up', 'Down']:
            self.text.bind(f'<{arrow_key}>', self.show_cursor_position)
            self.text.bind(f'<KeyRelease-{arrow_key}>', self.show_cursor_position)

        # if the input file is supplied, load that file in the text area
        if self.file_name is not None:
            self.load_file(self.file_name)

    def show_entity_shortcut_mapping(self):
        """set up the shortcut mapping region in the UI
        :return:
        """
        row = 0

        map_label = Label(self, text='Entity shortcut map', foreground='red', font=(self.text_font_style, 14, 'bold'))
        map_label.grid(row=0, column=self.text_column + 2, columnspan=2, rowspan=1, padx=10)

        for key in sorted(self.entity_shortcuts):
            row += 1
            symbol_label = Label(
                self, text=f'<ctrl-{key}>' + ': ', foreground='blue', font=(self.text_font_style, 14, 'bold')
            )
            symbol_label.grid(row=row, column=self.text_column + 2, columnspan=1, rowspan=1, padx=3)

            label_entry = tk.Entry(self, foreground='blue', font=(self.text_font_style, 14, 'bold'))
            label_entry.insert(0, self.entity_shortcuts[key])
            label_entry.grid(row=row, column=self.text_column + 3, columnspan=1, rowspan=1)
            label_entry.config(state='readonly')

    def show_special_key_mapping(self):
        """set up the special key mapping region in the UI
        :return:
        """
        row = len(self.entity_shortcuts) + 1

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
            label_entry.config(state='readonly')

    def open_file_dialog_read_file(self):
        """open the file dialog, read the file, and set the content of the file in the textarea
        :return:
        """
        file_types = [("text files", ".txt"), ("json files", ".json"), ("conll files", "*.conll")]
        dlg = tkfileopen(self, filetypes=file_types)
        fl = dlg.show()
        if fl:
            self.load_file(fl)

    def load_file(self, fl):
        file_type = get_file_type(fl)
        if file_type == FILE_TYPE_TXT:
            self.content.populate_from_text(txt_file=fl)
            self.file_name = f'{fl[:-4]}.json'
        elif file_type == FILE_TYPE_JSON:
            self.content.populate_from_json(json_file=fl)
        elif file_type == FILE_TYPE_CONLL:
            self.content.populate_from_json(json_file=fl)  # TODO: change this
            self.file_name = f'{fl[:-4]}.json'
        else:
            return BREAK
        self.msg_lbl.config(text=f'File: {os.path.abspath(self.file_name)}')
        self.write_output_and_text_area()

    def write_output_and_text_area(self, cursor_index=TEXTAREA_START):
        """convert the content into something that can be put into a text area, add highlight colors
        :return:
        """
        start_char_index = 0
        self.text.delete(TEXTAREA_START, TEXTAREA_END)
        span_tags = []
        content = ''
        current_sentence_num = 1
        for token in self.content.tokens:
            if token.sen_index != current_sentence_num:
                content += NEW_LINE_CHAR
                current_sentence_num = token.sen_index
            content += f'{token.content} '
            end_char_index = start_char_index + len(content)
            spans: List[Span] = [
                self.content.span_from_span_id(_id) for _id in self.content.span_ids_from_token_id(token.id)
            ]
            for span in spans:
                for tag in span.tags:
                    span_tags.append(
                        (
                            f'TOKEN_TAG_{token.id}.{tag.content}',
                            f'{span.sen_index}.{span.char_start_index}',
                            f'{span.sen_index}.{span.char_end_index}',
                            tag.color,
                        )
                    )
            start_char_index = end_char_index
        self.text.insert(TEXTAREA_END, content)
        for span_tag_id, start, end, color in span_tags:
            self.text.tag_add(span_tag_id, start, end)
            self.text.tag_config(span_tag_id, foreground=color)
        self.text.mark_set(INSERT, cursor_index)
        self.text.see(cursor_index)
        self.set_cursor_label(cursor_index)
        json.dump(self.content.serialize(), open(self.file_name, 'w'), indent=2)
        self.show_span_details(None)

    def show_cursor_position(self, event):
        """show the current cursor position in the cursor label + move the cursor in that index
        :param event: the event that caused this callback
        :return:
        """
        cursor_index = self.text.index(INSERT)
        self.text.mark_set(INSERT, cursor_index)
        self.text.see(cursor_index)
        self.set_cursor_label(cursor_index)

    def get_data_type_ahead(self, event, selection_start, selection_end):
        """the user has pressed enter on the type ahead. get the label from the type ahead widget, close the type ahead window, label the selected string
        :param event: the event that caused this callback
        :param selection_start: cursor index for the start of the selected text
        :param selection_end: cursor index for the end of the selected text
        :return:
        """
        label = self.type_ahead_entry.text_.get()
        self.type_ahead_entry.destroy()
        self.label_selected_text(label, selection_start, selection_end)

    def set_cursor_label(self, cursor_index):
        """set the cursor label region with the current cursor position
        :param cursor_index:
        :return:
        """
        cursor_row, cursor_column = cursor_index.split(CURSOR_SEP)
        cursor_text = f'row: {cursor_row}\ncol: {cursor_column}'
        self.cursor_index_lbl.config(text=cursor_text)

    def un_label(self, event):
        """If there is a labeled text around the cursor, select the span. else do nothing
        :param event: the event that caused this callback to fire
        :return:
        """
        current_cursor = self.text.index(INSERT)
        if self.text.tag_ranges(SEL):  # a text is selected
            allowed, selected_content, selection_start, selection_end = self.adjust_selection()
            if not allowed:
                return BREAK
            sel_row_start, sel_col_start = [int(x) for x in selection_start.split(CURSOR_SEP)]
            sel_row_end, sel_col_end = [int(x) for x in selection_end.split(CURSOR_SEP)]
            assert sel_row_start == sel_row_end
            span_id = self.content.span_id_from_start_end_index(sel_row_start, sel_col_start, sel_col_end)
        else:
            current_row, current_col = [int(x) for x in current_cursor.split(CURSOR_SEP)]
            span_ids = self.content.span_ids_from_char_index(current_row, current_col)
            if not span_ids:
                self.log('There is no span for the token you clicked on', ERROR)
                return BREAK
            if len(span_ids) > 1:
                self.log('There are multiple spans for the token you clicked on, select one', ERROR)
                return BREAK
            span_id = span_ids[0]
        span = self.content.span_from_span_id(span_id)
        if span is None:
            self.log('can not select span', ERROR)
            return BREAK
        tag = span.tags[-1]
        self.log(f'deleted tag [{tag.content}] for span [{span.content}]')
        self.content.delete_tag(span=span, tag=tag)

        self.write_output_and_text_area(cursor_index=current_cursor)
        self.text.tag_add("sel", f'{span.sen_index}.{span.char_start_index}', f'{span.sen_index}.{span.char_end_index}')
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
            "<Return>", lambda event_: self.get_data_type_ahead(event_, selection_start, selection_end)
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
        label = self.entity_shortcuts[press_key.lower()]
        allowed, selected_content, selection_start, selection_end = self.adjust_selection()
        if not allowed:
            return BREAK
        self.label_selected_text(label, selection_start, selection_end)
        return BREAK

    def adjust_selection(self) -> Tuple[bool, str, str, str]:
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
            self.log('Selected text must be in the same row', ERROR)
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
            content, cursor_index = self.history.pop()
            self.content.populate_from_dict(content)
            self.write_output_and_text_area(cursor_index=cursor_index)
        else:
            self.log("History is empty!", ERROR)

    def log(self, msg: str, msg_type: str = INFO):
        """append a msg to the logging area
        :param msg: message
        :param msg_type: error/info/
        :return:
        """
        self.msg_lbl.config(text=f'{msg_type.upper()}: {msg}')

    def label_selected_text(self, label: str, label_start_index: str, label_end_index: str):
        """we got a label from the labeling mechanism (type-ahead/shortcut), label the selected content with it
        :param label: label to apply
        :param label_start_index: cursor index of where the selected text begins
        :param label_end_index: cursor index of where the selected text ends
        :return:
        """
        row_index_start, col_index_start = [int(x) for x in label_start_index.split(CURSOR_SEP)]
        row_index_end, col_index_end = [int(x) for x in label_end_index.split(CURSOR_SEP)]
        label_color = self.label_colors[label]
        assert row_index_start == row_index_end
        self.content.add_tag(
            tag=Tag(label, color=label_color),
            sen_index=row_index_start,
            char_start_index=col_index_start,
            char_end_index=col_index_end,
        )
        self.write_output_and_text_area(cursor_index=f'{row_index_start}.{col_index_end}')

    def push_to_history(self):
        """push the current selected span and the cursor position to a queue
        :return:
        """
        cursor_position = self.text.index(INSERT)
        self.history.append((self.content.serialize(), cursor_position))

    def export(self):
        """export the text area content in a conll BIO format
        if there are multiple levels of labels like george/B-PER/B-PRES bush/I-PER/I-PRES there will be multiple columns
        in the conll file, with `words` as the first column.
        :return:
        """
        file_name = f'{self.file_name[:-5]}.bio.conll'
        self.log(f'Writing output to {file_name}')
        towkf(self.content, file_name)

    def highlight(self, event):
        """highlight a span or de-highlight the highlighted area.
        :param event: the event key that caused this callback to fire
        :return:
        """
        if self.text.tag_ranges(HIGHLIGHT_COMMAND):
            self.text.tag_delete(HIGHLIGHT_COMMAND)
            return BREAK
        if self.text.tag_ranges(SEL):
            sel_first = self.text.index(SEL_FIRST)
            sel_last = self.text.index(SEL_LAST)
        else:
            current_row, current_col = [int(x) for x in self.text.index(INSERT).split(CURSOR_SEP)]
            span_ids = self.content.span_ids_from_char_index(sen_index=current_row, char_index=current_col)
            if not span_ids:
                self.log('There is no span for the token you clicked on', ERROR)
                return BREAK
            if len(span_ids) > 1:
                self.log('There are multiple spans for the token you clicked on, select one', ERROR)
                return BREAK
            span = self.content.span_from_span_id(span_ids[0])
            sel_first = f'{current_row}.{span.char_start_index}'
            sel_last = f'{current_row}.{span.char_end_index}'
        self.text.tag_add(HIGHLIGHT_COMMAND, sel_first, sel_last)
        self.text.tag_config(HIGHLIGHT_COMMAND, background=DEFAULT_HIGHLIGHT_COLOR)
        return BREAK

    def show_span_details(self, event):
        """show span info for the token under cursor
        :param event:
        :return:
        """
        for entry in self.span_info_entries:
            entry.destroy()
            self.span_info_entries.remove(entry)
        current_cursor = self.text.index(INSERT)
        if self.text.tag_ranges(SEL):  # a text is selected
            allowed, selected_content, selection_start, selection_end = self.adjust_selection()
            if not allowed:
                return BREAK
            sel_row_start, sel_col_start = [int(x) for x in selection_start.split(CURSOR_SEP)]
            sel_row_end, sel_col_end = [int(x) for x in selection_end.split(CURSOR_SEP)]
            assert sel_row_start == sel_row_end
            span_ids = [self.content.span_id_from_start_end_index(sel_row_start, sel_col_start, sel_col_end)]
        else:
            current_row, current_col = [int(x) for x in current_cursor.split(CURSOR_SEP)]
            span_ids = self.content.span_ids_from_char_index(current_row, current_col)
            if not span_ids:
                self.log('There is no span for the token you clicked on', ERROR)
                return BREAK
        start_col = 1
        _fnt = Font(family=self.text_font_style, size=15, weight="bold", underline=0)
        for span_id in span_ids:
            span = self.content.span_from_span_id(span_id)
            span_content = span.content
            for tag in span.tags:
                entry = SpanEntry(
                    span=span,
                    tag=tag,
                    current_cursor=current_cursor,
                    master=self,
                    width=15,
                    background='white',
                    justify=tk.CENTER,
                    font=_fnt,
                )
                entry.grid(
                    padx=10,
                    pady=5,
                    row=self.span_info_row_start + start_col,
                    column=self.text_column + 1,
                    sticky=W + E + N + S,
                    columnspan=20,
                )
                entry.insert(0, f'{span_content}/{tag.content}')
                entry.config(fg=tag.color)
                entry.config(state='readonly')
                entry.bind("<Control-d>", lambda event_: self.un_label_span(event_))
                start_col += 1
                self.span_info_entries.append(entry)

    def un_label_span(self, event):
        """delete a span selected from the details area
        :param event:
        :return:
        """
        entry: SpanEntry = event.widget
        self.content.delete_tag(entry.span, entry.tag)
        self.write_output_and_text_area(cursor_index=entry.current_cursor)
        entry.destroy()
