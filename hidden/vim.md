
```bash
.               # repeat last executed command
~               # toggle character case (uppercase/lowercase)
dd              # delete (cut) the current line
y               # yank (copy)
p               # paste after the cursor
u               # undo
CTRL+r          # redo
o               # open a new line below and enter Insert mode
cW              # replace the current word and enter Insert mode
$               # move to the end of the line
0               # move to the beginning of the line
50 » CTRL+a     # increment 50 in a number value (useful for requests/limits)
40 » CTRL+x     # decrement 40 in a number value (useful for requests/limits)
:%s/foo/bar/g   # replace all occurrences of "foo" with "bar"
:10,15>         # indent lines 10–15 by one shiftwidth
:10,15<         # unindent lines 10–15 by one shiftwidth
:30,50d         # delete (cut) lines 30–50
:30,50t70       # copy lines 30–50 and paste them below line 70
:30,50m70       # move lines 30–50 below line 70
i » CTRL+y      # copy line above character by character
V               # enter Visual Line mode
CTRL+v          # enter Visual Block mode
gv              # reselect the last Visual selection
* » cW » type new word » n » . » n » .              # replace word by word
CTRL+v » select column » SHIFT+i » type text » ESC  # multi-line column insertion (comments)
```
