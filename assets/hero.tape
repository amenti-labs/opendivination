Output assets/hero.gif

Set FontSize 22
Set Width 1400
Set Height 900
Set Theme "Builtin Solarized Dark"
Set TypingSpeed 80ms
Set Padding 24
Set Shell "zsh"

Type "alias opendivination='.venv/bin/python -m opendivination.cli.main'"
Enter
Sleep 800ms

Type "opendivination setup --source-profile computer"
Enter
Sleep 2s

Type "opendivination draw tarot"
Enter
Sleep 2s

Type "opendivination draw iching --method yarrow"
Enter
Sleep 2s

Type "opendivination sources"
Enter
Sleep 2s
