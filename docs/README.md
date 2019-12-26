### Usage

#### Starting the program

`satya <config.<yml|json>>`. [A sample config file](../data/sampleconfig.yml) can be found in the [data](../data) directory. It looks like this:

```
entities:
- name: PER
  shortcut: p
  color: MediumPurple1 # /etc/X11/rgb.txt
  level: 1
- name: LOC
  shortcut: l
  color: IndianRed1
  level: 1
- name: ORG
  shortcut: o
  color: NavyBlue
- name: MISC
  level: 1
- name: DATE
- name: STATE
  level: 2
relations:
- name: BORN_IN_PLACE
  entities:
    - start: PER
      end: LOC
- name: BORN_IN_DATE
  entities:
    - start: PER
      end: DATE
- name: BORN_IN
  entities:
    - start: PER
      end: LOC
    - start: PER
      end: DATE
```

There are six labels and three shortcuts defined. The label names are what a selected text span will be labeled with. The shortcuts are a mapping between an input key and a label: in other words, if you press `ctrl-l` on a selected text, you will label it as `LOC`. You can use any character key for shortcut except `q`, `z`, `s` (+ `e` and `d` if you are in the advanced mode).

**Important**: The content must be pre-tokenized and joined on a single white space character.

### Labeling

There are two ways of labeling entities: type-ahead and shortcut.

After you select a text span, start typing anything and a type-ahead window will pop up. Once you select a label name that label will be applied to the text and the color of the text in the span will be changed.

Another way to label is by using shortcuts. For eg, pressing `<ctrl-p>` labels a selected text with label `PER`.

You can add multiple labels to the same span. If you mistakenly select _part_ of a span, the whole span will be labeled (this is why the content needs to be pre-tokenized and joined on a single white space character).

If you select a span you can press `Ctrl-s` to get the entity labels for that span. If the cursor is inside a span you don't have to select a text, the software automatically finds out the span for you. Your cursor can be within multiple spans. Consider the sentence `Tom lives in Hawaii, USA` and you have annotated `Hawaii` as `STATE` and `Hawaii, USA` as `LOC`. If your cursor is on Hawaii, it is within multiple spans. In this case, you have to select the entire text of the span.

To label relations between spans, you have to press `<ctrl-e>` on two spans and a type-ahead window will open. The output of the type-ahead window will be used as the relation between the selected spans. The span selection works as described before. Once you press `<ctrl-e>` on a span, the span is highlighted meaning the relation annotation is in progress.  

### Un-labeling and Re-labeling

Often one needs to un-label/re-label a span.

`<ctrl-z>` is the command to undo the last change.

You can select a span (works as mentioned before) and use `<ctrl-q>` to remove the last entity label from it.

When a span is selected, the entity and relation labels are also shown in the UI. You can select a label and use `ctrl-d` to delete that label.
 
Once a label is deleted from a span, you can re-label it. 

### Exporting the content

If you click on the export button, a BIO format conll file will be created. The software is mostly [WYSIWYG](http://en.wikipedia.org/wiki/WYSIWYG).
