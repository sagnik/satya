from typing import List, Union
import tkinter as tk
from tkinter import Text
from tkinter.ttk import Button, Label, Scrollbar
from tkinter.constants import *
from annotate.consts import *
from tkinter.font import Font
from annotate.autocomplete import AutocompleteEntry
from annotate.data import Span, Relation

from annotate.spanannotator import SpanEntry, SpanAnnotatorFrame


class RelationEntry(tk.Entry):
    def __init__(self, relation: Relation, current_cursor: str, master=None, cnf={}, **kwargs):
        super().__init__(master, cnf, **kwargs)
        self.relation = relation
        self.current_cursor = current_cursor


class SpanAnnotatorRelationFrame(SpanAnnotatorFrame):
    def __init__(self, parent, config, **kwargs):
        super().__init__(parent, config, **kwargs)
        self.special_key_map.update({RELATION_ENTITY_KEY: RELATION_ENTITY_COMMAND})
        self.relationship_spans: List[Span] = []
        self.relations = config.get(RELATIONS_KEY, [])
        self.type_ahead_relation = None

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
        span_area_name = Label(self, text=f"Spans", foreground="Blue", font=(self.text_font_style, 14, "bold"))
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
        self.text.bind(SHOW_SPAN_INFO_KEY, self.show_span_details)
        self.text.bind(RELATION_ENTITY_KEY, self.create_relations)

        self.show_special_key_mapping()

        # bind arrow keys to show cursor positions
        for arrow_key in ['Left', 'Right', 'Up', 'Down']:
            self.text.bind(f'<{arrow_key}>', self.show_cursor_position)
            self.text.bind(f'<KeyRelease-{arrow_key}>', self.show_cursor_position)

        # if the input file is supplied, load that file in the text area
        if self.file_name is not None:
            self.load_file(self.file_name)

    def create_relations(self, event):
        """create a relation between two spans
        :param event:
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
            self.log('No span can be selected', ERROR)
            return BREAK
        relation_highlight_tag = f'HIGHLIGHT_RELATION_{len(self.relationship_spans)}'
        self.text.tag_add(
            relation_highlight_tag,
            f'{span.sen_index}.{span.char_start_index}',
            f'{span.sen_index}.{span.char_end_index}',
        )
        self.text.tag_configure(relation_highlight_tag, background=DEFAULT_HIGHLIGHT_COLOR)
        self.relationship_spans.append(span)
        if len(self.relationship_spans) == 2:
            self.type_ahead_relation = AutocompleteEntry(self)
            self.type_ahead_relation.build(entries=self.relations, no_results_message=TYPE_AHEAD_NO_RESULTS_MESSAGE)
            self.type_ahead_relation.listbox.bind("<Return>", self.add_relation_type_ahead)
            return BREAK

    def add_relation_type_ahead(self, event):
        """the user has pressed enter on the type ahead. get the label from the type ahead widget, close the type ahead window, label the selected string
        :param event: the event that caused this callback
        :return:
        """
        self.push_to_history()
        relation_name = self.type_ahead_relation.text_.get()
        self.type_ahead_relation.destroy()
        self.content.add_relation(self.relationship_spans[0].id, self.relationship_spans[1].id, relation_name)
        self.relationship_spans = []
        self.text.tag_delete('HIGHLIGHT_RELATION_1')
        self.text.tag_delete('HIGHLIGHT_RELATION_2')
        self.write_output_and_text_area()

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
        start_col = self.span_info_row_start + 1
        _fnt = Font(family=self.text_font_style, size=15, weight="bold", underline=0)
        for span_id in span_ids:
            span = self.content.span_from_span_id(span_id)
            if span is None:
                continue
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
                    padx=10, pady=5, row=start_col, column=self.text_column + 1, sticky=W + E + N + S, columnspan=20
                )
                entry.insert(0, f'{span_content}/{tag.content}')
                entry.config(fg=tag.color)
                entry.config(state='readonly')
                entry.bind(UN_LABEL_FROM_SPAN_INFO_AREA_KEY, lambda event_: self.un_label_span(event_))
                start_col += 1
                self.span_info_entries.append(entry)
            relations = self.content.relations_by_span_id(span_id)
            for relation in relations:
                entry = RelationEntry(
                    relation=relation,
                    current_cursor=current_cursor,
                    master=self,
                    width=15,
                    background='white',
                    justify=tk.CENTER,
                    font=_fnt,
                )
                entry.grid(
                    padx=10, pady=5, row=start_col, column=self.text_column + 1, sticky=W + E + N + S, columnspan=20
                )
                entry.config(fg='DarkBlue')
                start_span = self.content.span_from_span_id(relation.start_id)
                if start_span is None:
                    continue
                end_span = self.content.span_from_span_id(relation.end_id)
                if end_span is None:
                    continue
                entry.insert(0, f'{start_span.content}-[{relation.name}]->{end_span.content}')
                entry.config(state='readonly')
                entry.bind(UN_LABEL_FROM_SPAN_INFO_AREA_KEY, lambda event_: self.un_label_span_relation(event_))
                start_col += 1
                self.span_info_entries.append(entry)

    def un_label_span_relation(self, event):
        """delete a span/relation selected from the details area
        :param event:
        :return:
        """
        self.push_to_history()
        entry: Union[SpanEntry, RelationEntry] = event.widget
        if hasattr(entry, 'relation'):
            self.content.delete_relation(entry.relation.start_id, entry.relation.end_id, entry.relation.name)
        else:
            self.content.delete_entity(entry.span, entry.tag)
        self.write_output_and_text_area(cursor_index=entry.current_cursor)
        entry.destroy()
