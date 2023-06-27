# Проект парсинга pep

***

Парсер обладает следующим функционалом:
- Сбор информации со статей о последних обновлениях Python
- Сбор информации о версиях Python с ссылками на документацию
- Скачивание документации последней актуальной версии Python в PDF
- Сбор информации о статусах PEP

### Запустить проект

Клонировать репозиторий 

```bash
git clone https://github.com/Ezereul/bs4_parser_pep
```
Создать и активировать виртуальное окружение
```bash
python -m venv venv
source venv/Scripts/activate
```
Установить зависимости
```bash
python -m pip install --upgrade pip
pip install -r requiremtns.txt
```
Перейти в директорию проекта и запустить скрипт
```bash
cd src
python main.py [mode]
```
Для получения всех параметров и доступных команд
```bash
python main.py --help
```