# Offline short English words

`english_words.gd` bundles 870 one-, two- and three-letter words, the lengths
possible with the current three pedestals. It is a GDScript resource so Godot
exports it automatically. No dictionary download or network call happens in play.

Source: SCOWL 2020.12.07, from the project's official release:
https://downloads.sourceforge.net/wordlist/scowl-2020.12.07.tar.gz
Project and release information: https://wordlist.aspell.net/other/

Built from `english-words`, `british-words` and `american-words` categories,
through size 70, keeping lowercase ASCII entries of length 2–3 plus `a` and
`i`, with `qat` included from the size-80 tier. Proper-name, uppercase,
abbreviation and contraction categories are not included. Alphabet symbols
and their bare plurals are excluded. Several unit/math abbreviations appearing
in the ordinary-word categories are also excluded explicitly by the builder.
Ordinary dictionary senses (including informal words) remain accepted.
This is dictionary membership, not a pronunciation or CVC rule: e.g. `the`
is valid even though the blocks still play their individual phonemes.

This finite dictionary includes uncommon words but is not a promise to cover
every archaic, regional or specialist word. It can be extended in the bundled
resource when needed. No rules require every slot to be filled: empty slots
are skipped, so `a`, `i`, `at`, `it`, `cat` and `dog` all work.

Regenerate with Python's standard library:

```sh
python3 tools/build_short_word_list.py /path/to/scowl-2020.12.07.tar.gz
```

The complete upstream copyright/permission notices are in
`SCOWL-Copyright.txt` and must accompany the list.
