import tkinter as tk
from annotate.consts import *
from tkinter.constants import *


class AutocompleteEntry(tk.Toplevel, object):
    """A container for `tk.Entry` and `tk.Listbox` widgets.

    An instance of AutocompleteEntry is actually a `tk.Frame`, containing the `tk.Entry` and `tk.Listbox` widgets needed to display autocompletion entries. Thus, you can initialize it with the usual arguments to `tk.Frame`.
    Constants:
    LISTBOX_HEIGHT -- Default height for the `tk.Listbox` widget
    LISTBOX_WIDTH -- Default width for the `tk.Listbox` widget
    ENTRY_WIDTH -- Default width for the `tk.Entry` widget

    Methods:
    __init__ -- Set up the `tk.Listbox` and `tk.Entry` widgets
    build -- Build a list of autocompletion entries
    _update_autocomplete -- Internal method
    _select_entry -- Internal method
    _cycle_up -- Internal method
    _cycle_down -- Internal method

    Other attributes:
    text -- StringVar object associated with the `tk.Entry` widget
    entry -- The `tk.Entry` widget (access this directly if you
             need to change styling)
    listbox -- The `tk.Listbox` widget (access this directly if
             you need to change AutocompleteEntry)
    """

    def __init__(self, _, *args, **kwargs):
        """Constructor.

        Create the `self.entry` and `self.listbox` widgets.
        Note that these widgets are not yet displayed and will only be visible when you call `self.build`.

        Arguments:
        master -- The master tkinter widget

        Returns:
        None
        """
        super(AutocompleteEntry, self).__init__(*args, **kwargs)
        self.text_ = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.text_, width=TYPE_AHEAD_ENTRY_WIDTH)
        self.listbox = tk.Listbox(
            self, selectmode='browse', height=TYPE_AHEAD_LISTBOX_HEIGHT, width=TYPE_AHEAD_LISTBOX_WIDTH
        )
        self._case_sensitive = None
        self._entries = None
        self._no_results_message = None
        self._listbox_height = None

    def build(self, entries, max_entries=5, no_results_message=TYPE_AHEAD_NO_RESULTS_MESSAGE):
        """Set up the autocompletion settings.

        Binds <KeyRelease>, <<ListboxSelect>>, <Down> and <Up> for
        smooth cycling between autocompletion entries.

        Arguments:
        entries -- An iterable containing autocompletion entries (strings)
        max_entries -- [int] The maximum number of entries to display
        no_results_message -- [str] Message to display when no entries
                              match the current entry; you can use a
                              formatting identifier '{}' which will be
                              replaced with the entry at runtime

        Returns:
        None
        """
        self._entries = entries
        self._no_results_message = no_results_message
        self._listbox_height = max_entries

        self.entry.bind("<KeyRelease>", self._update_autocomplete)
        self.entry.focus()
        self.entry.grid(column=0, row=0)

        self.listbox.bind("<<ListboxSelect>>", self._select_entry)
        self.listbox.grid(column=0, row=1)
        self.listbox.grid_forget()
        # Initially, the listbox widget doesn't show up.

    def _update_autocomplete(self, event):
        """Internal method.
        Update `self.listbox` to display new matches.
        """
        self.listbox.delete(0, END)
        self.listbox["height"] = self._listbox_height

        text = self.text_.get()
        if not text:
            self.listbox.grid_forget()
        else:
            for entry in self._entries:
                if text.lower() in entry.strip().lower():
                    self.listbox.insert(END, entry)

        listbox_size = self.listbox.size()
        if not listbox_size:
            if self._no_results_message is None or text is None:
                self.listbox.grid_forget()
            else:
                try:
                    self.listbox.insert(END, self._no_results_message.format(text))
                except UnicodeEncodeError:
                    self.listbox.insert(END, self._no_results_message.format(text.encode("utf-8")))
                if listbox_size <= self.listbox["height"]:
                    # In case there's less entries than the maximum
                    # amount of entries allowed, resize the listbox.
                    self.listbox["height"] = listbox_size
                self.listbox.grid()
        else:
            if listbox_size <= self.listbox["height"]:
                self.listbox["height"] = listbox_size
            self.listbox.grid()

    def _select_entry(self, event):
        """Internal method.
        Set the text variable corresponding to `self.entry`
        to the value currently selected.
        """
        widget = event.widget
        try:
            value = widget.get(int(widget.curselection()[0]))
            self.text_.set(value)
        except IndexError:
            self.text_.set('')
