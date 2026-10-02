from pywinauto import Desktop

desktop = Desktop(backend="uia")

for window in desktop.windows():
    try:
        print(
            f"제목: {window.window_text()!r} "
            f"| PID: {window.process_id()}"
        )
    except:
        pass