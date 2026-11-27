# Camera Collection State Switcher

Аддон Blender сохраняет наборы параметров видимости коллекций и объектов для выбранной камеры. Наборы хранятся в данных камеры внутри файла `.blend`. Для коллекций сохраняются Exclude в текущем View Layer, Disable in Viewports и Disable in Renders. Для объектов сохраняются Disable in Viewports и Disable in Renders.

## Установка и запуск

1. Скачайте [Collection_Camera_Manager.py](Collection_Camera_Manager.py).
2. Откройте **Edit → Preferences → Add-ons**. Выберите **Install** или **Install from Disk** в зависимости от версии Blender, укажите Python-файл и включите аддон.
3. Выберите объект-камеру. Откройте **Properties → Camera Data → Collection Visibility States** или боковую панель 3D Viewport (**N → Camera → Camera Collection States**).
4. Сохраните текущую видимость, затем загрузите, обновите или удалите сохранённое состояние. Экспорт в текстовый блок Blender доступен в панели Camera Data.

Минимальная версия, указанная в метаданных аддона, — Blender 3.0.

Правила разработки и ревью описаны в [AGENTS.md](AGENTS.md), работа через Blender MCP — в [docs/MCP.md](docs/MCP.md).

## Лицензия

GNU General Public License v3.0 или более поздняя (GPL-3.0-or-later). Полный текст находится в файле [LICENSE](LICENSE).
