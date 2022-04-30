# clrp-regex
As with many repositories I have uploded recently, this one was also written couple years ago. It is a complete LR(1) Parser, and Regular Expression generator (inspiration was taken from [this][1] excellent article by Russ Cox). In fact the parser for the regex generator was the LR(1) parser!

`test_regex.py` contains an example of the regex generator at work:
```python
import clrp

regex = clrp.RegularExpression(r"[0-9]+")
print(regex.check("868993458990966743234"))
```

and `test_clrp.py` contains an example of the LR(1) parser generator at work.

[1]: https://swtch.com/~rsc/regexp/regexp1.html
