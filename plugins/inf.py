import os
import getpass
def key():
    return ord('i')  #срабатывание на клавишу "i"
def run(current_path): #основная часть плагина
    print("=== Информация о системе ===")
    print(f"Пользователь: {getpass.getuser()}")
    print(f"Текущий каталог: {current_path}")
    try:
        print(f"Файлов: {len(os.listdir(current_path))}")
    except Exception as e:
        print(f"Ошибка: {e}")

