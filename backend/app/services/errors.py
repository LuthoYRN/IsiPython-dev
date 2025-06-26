def translate_error(error):
    if "NameError" in error:
        return "Impazamo: Igama elingachazwanga lifunyenwe"
    elif "SyntaxError" in error:
        return "Impazamo: Kukho into engalunganga kwindlela ebhalwe ngayo ikhowudi"
    else:
        return "Impazamo engachazwanga: " + error