# Подготовка к GitHub и автоматическим релизам

## 1. Иконки приложения

Положите три файла в папку **`icon/`** в корне репозитория. Если у вас другие имена (например, после экспорта из редактора) — **переименуйте** копии именно так, иначе скрипты их не найдут:

| Файл | Назначение |
|------|------------|
| `icon/guitarassistant.png` | Linux (AppImage, .desktop), иконка окна в собранном приложении |
| `icon/guitarassistant.ico` | Windows: иконка `.exe` в проводнике и на панели задач |
| `icon/guitarassistant.icns` | macOS: иконка `GuitarAssistant.app` и в DMG |

Исходник 512×512 для PNG — нормально. Для `.ico` удобно иметь несколько размеров внутри файла (16–256), но один крупный слой часто тоже подходит. Ваш `.icns` с уровнями 128 / 256 / 512 подходит для релизов: в `GuitarAssistant.spec` он передаётся в `BUNDLE` как есть.

Если файла с нужным именем нет, сборка не падает: для этой платформы просто не подставляется иконка (кроме PNG для окна — тогда окно без кастомной иконки).

---

## 2. Локальная проверка сборки

```powershell
cd путь\к\GuitarHelper
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt -r requirements-build.txt
pyinstaller --noconfirm GuitarAssistant.spec
```

- Windows: `dist\GuitarAssistant.exe`
- macOS: `dist/GuitarAssistant.app`
- Linux: `dist/GuitarAssistant/` (из этого делается AppImage в CI)

---

## 3. Первый выгруз на GitHub

### Один раз на компьютере: имя и email в коммитах

Подставьте свои данные (как на GitHub или публичное имя). Email можно взять в GitHub → **Settings → Emails** — там есть вариант вида `id+username@users.noreply.github.com`, чтобы не светить личную почту.

```powershell
git config --global user.name "Ваше Имя"
git config --global user.email "ваш@email или noreply от GitHub"
```

Проверка: `git config --global --list`

### Репозиторий на GitHub

1. Зайдите на [github.com/new](https://github.com/new), укажите имя репозитория (например `GuitarHelper`), **не** ставьте галочки README / .gitignore / license (у вас они уже есть локально).
2. После создания GitHub покажет URL — скопируйте **HTTPS**, например `https://github.com/ВАШ_ЛОГИН/GuitarHelper.git`.

### В папке проекта (репозиторий уже создан командой `git init -b main`)

```powershell
cd O:\repos\GuitarHelper
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ВАШ_ЛОГИН/ИМЯ_РЕПО.git
git push -u origin main
```

При первом `git push` Windows может открыть окно входа в GitHub (браузер или менеджер учётных данных).

### После пуша

В `README.md` замените `yourusername/GuitarAssistant` на ваш реальный путь репозитория и закоммитьте правку.

---

## 4. Публикация релиза (запуск CI)

Workflow **Release builds** срабатывает только когда вы **публикуете** GitHub Release (не черновик).

1. Закоммитьте и запушьте все изменения (включая папку `icon/` с файлами).
2. На GitHub: **Releases** → **Draft a new release**.
3. Создайте новый тег, например `v1.0.0` (кнопка «Choose a tag» → ввести имя → создать).
4. Заголовок релиза — любой (часто тот же `v1.0.0`).
5. Нажмите **Publish release**.

После этого в Actions пойдут три сборки (Windows, macOS, Linux), затем к релизу прикрепятся:

- `GuitarAssistant-Windows-x86_64.zip`
- `GuitarAssistant-macOS.dmg`
- `GuitarAssistant-x86_64.AppImage`

Отдельные секреты не нужны: используется `GITHUB_TOKEN`.

**Замечание:** `macos-latest` даёт сборку под **Apple Silicon** (arm64). Отдельный Intel-сборщик не настроен.

---

## 5. Если что-то упало в Actions

Откройте красный workflow → шаг **PyInstaller** или **AppImage** → лог. Частые темы: не те имена файлов в `icon/`, не закоммичена папка `icon/`, на Linux не хватает системной библиотеки (тогда по логу добавляют пакет в шаг `apt-get` в `.github/workflows/release.yml`).
