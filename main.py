import curses
import os
import shutil
import importlib.util
def draw_menu(stdscr, current_row, files, path):#отрисовка
    stdscr.clear()
    max_y, max_x = stdscr.getmaxyx()
    stdscr.addstr(0, 0, f"Текущий путь: {path}"[:max_x - 1])
    for idx, file in enumerate(files):
        y = idx + 2
        x = 2
        if y >= max_y - 1:
            break
        if idx == current_row:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, file[:max_x - x - 1])
            stdscr.attroff(curses.color_pair(1))
        else:
            stdscr.addstr(y, x, file[:max_x - x - 1])
    stdscr.refresh()
    help_line = "[Enter] Открыть  [Backspace] Назад  [c] Копировать  [v] Вставить  [d] Удалить  [r] Переименовать  [n] Новый [l] Плагин  [Esc] Выйти"
    stdscr.addstr(max_y - 1, 0, help_line[:max_x - 1])
    stdscr.refresh()
def load_plugins(folder="plugins"):#расширение (загрузка плагинов)
    bindings = {}
    if not os.path.exists(folder):
        os.makedirs(folder)
    for filename in os.listdir(folder):
        if filename.endswith(".py"):
            filepath = os.path.join(folder, filename)
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "key") and hasattr(module, "run"):
                    bindings[module.key()] = module.run
    return bindings

def main(stdscr):#ядро программы
    plugin_bindings = load_plugins()
    curses.curs_set(0)
    curses.mousemask(curses.ALL_MOUSE_EVENTS)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    path = os.path.expanduser('~')
    files = os.listdir(path)
    current_row = 0
    clipboard = None

    while True:
        draw_menu(stdscr, current_row, files, path)
        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(files) - 1:
            current_row += 1
        elif key == 27:
            break
        elif key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, _ = curses.getmouse()
                clicked_index = my - 2
                if 0 <= clicked_index < len(files):
                    current_row = clicked_index
                    selected = files[current_row]
                    full_path = os.path.join(path, selected)
                    if os.path.isdir(full_path):
                        path = full_path
                        files = os.listdir(path)
                        current_row = 0
            except Exception:
                pass
        elif key in plugin_bindings: #срабатывание плагина на соответсвующую кнопку
            curses.endwin()
            try:
                plugin_bindings[key](path)
            except Exception as e:
                print(f"Ошибка при выполнении плагина: {e}")
            input("Нажмите Enter...")
            stdscr.clear()
            stdscr.refresh()

        elif key == ord('l') or key ==ord('д'):#перезагрузка плагинов
            plugin_bindings = load_plugins()
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            stdscr.addstr(1, 0, "Плагины перезагружены!")
            stdscr.refresh()
            curses.napms(1000)

        elif key == 10: #открытие файлов и папок
            selected = files[current_row]
            full_path = os.path.join(path, selected)
            if os.path.isdir(full_path):
                path = full_path
                files = os.listdir(path)
                current_row = 0
            elif os.path.isfile(full_path):
                with open(full_path, 'r', errors='ignore') as f:
                    content = f.read()
                stdscr.clear()
                stdscr.addstr(0, 0, content[:curses.LINES * curses.COLS - 1])
                stdscr.addstr(curses.LINES - 1, 0, "Нажмите любую клавишу для возврата")
                stdscr.getch()
        elif key in (8, 127, curses.KEY_BACKSPACE): #возвращение в родительскую директорию
            parent_path = os.path.dirname(path)
            if os.path.exists(parent_path) and parent_path != path:
                path = parent_path
                files = os.listdir(path)
                current_row = 0
        elif key == ord('c') or key == ord ('с'): #копирование
            selected = files[current_row]
            clipboard = {
                'type': 'copy',
                'source': os.path.join(path, selected),
                'name': selected
            }
            stdscr.move(1, 0)
            stdscr.clrtoeol()
            stdscr.addstr(1, 0, f"Скопировано: {selected}")
            stdscr.refresh()
            curses.napms(1000)
        elif key == ord('v') or key == ord ('м'): #вставка
            if clipboard is None:
                stdscr.move(1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(1, 0, "Буфер пуст! Скопируйте что-нибудь (c)")
                stdscr.refresh()
                curses.napms(1000)
            else:
                try:
                    base_name = clipboard['name']
                    dest_path = os.path.join(path, base_name)
                    i = 1
                    while os.path.exists(dest_path):
                        name, ext = os.path.splitext(base_name)
                        new_name = f"{name}_copy{i}{ext}"
                        dest_path = os.path.join(path, new_name)
                        i += 1
                    if os.path.isdir(clipboard['source']):
                        shutil.copytree(clipboard['source'], dest_path)
                    else:
                        shutil.copy2(clipboard['source'], dest_path)
                    files = os.listdir(path)
                    inserted_name = os.path.basename(dest_path)
                    if inserted_name in files:
                        current_row = files.index(inserted_name)
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                    stdscr.addstr(1, 0, f"Вставлено: {inserted_name}")
                    stdscr.refresh()
                    curses.napms(1000)
                except Exception as e:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                    stdscr.addstr(1, 0, f"Ошибка вставки: {str(e)[:curses.COLS - 1]}")
                    stdscr.refresh()
                    curses.napms(2000)
        elif key == curses.KEY_DC or key == ord('d') or key == ord('в'): #удаление
            selected = files[current_row]
            full_path = os.path.join(path, selected)
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    os.remove(full_path)
                files = os.listdir(path)
                current_row = min(current_row, len(files) - 1)
            except Exception as e:
                stdscr.move(1, 0)
                stdscr.clrtoeol()
                stdscr.addstr(1, 0, f"Ошибка удаления: {str(e)[:curses.COLS - 1]}")
        elif key == ord('r') or key == ord ('к'): #переименование
            selected = files[current_row]
            curses.endwin()
            new_name = input(f"Новое имя для '{selected}': ").strip()
            try:
                os.rename(os.path.join(path, selected), os.path.join(path, new_name))
                files = os.listdir(path)
            except Exception as e:
                print(f"Ошибка переименования: {e}")
                input("Нажмите Enter...")
            stdscr.clear()
            stdscr.refresh()
        elif key == ord('n') or key == ord ('т'): #создание папки или файла
            curses.endwin()
            choice = input("1 - Папка, 2 - Файл: ").strip()
            name = input("Имя: ").strip()
            try:
                if choice == '2' and not name.lower().endswith(".txt"):
                    name += ".txt"
                full_path = os.path.join(path, name)
                if choice == '1':
                    os.mkdir(full_path)
                elif choice == '2':
                    with open(full_path, 'w', encoding='utf-8') as f:
                        f.write("")
                files = os.listdir(path)
                print(f"Создано: {name}")
                input("Нажмите Enter...")
            except Exception as e:
                print(f"Ошибка создания: {e}")
                input("Нажмите Enter...")
            stdscr.clear()
            stdscr.refresh()

curses.wrapper(main)
