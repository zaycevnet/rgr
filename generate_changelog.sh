#!/bin/bash

# Проверяем аргумент версии
if [ $# -ne 1 ]; then
    echo "Использование: $0 <версия>"
    exit 1
fi

# Аргумент: версия
VERSION=$1
# Текущая дата в формате YYYY-MM-DD
DATE=$(date +%Y-%m-%d)
# Файл changelog
CHANGELOG_FILE="changelog.md"

# Получаем последний тег (если нет, используем начальный коммит)
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

# Собрать коммиты после последнего тега
COMMITS=$(git log --oneline $LAST_TAG..HEAD --pretty=format:"%s [%h]")

# Проверяем, есть ли новые коммиты
if [ -z "$COMMITS" ]; then
    echo "Нет новых коммитов с момента последнего тега ($LAST_TAG). Changelog не обновлён."
    exit 0
fi

# Формировать новую секцию
NEW_SECTION="## [$VERSION] - $DATE

$COMMITS

"

# Создаём или обновляем changelog.md
if [ ! -f "$CHANGELOG_FILE" ]; then
    echo "# Changelog" > "$CHANGELOG_FILE"
    echo "" >> "$CHANGELOG_FILE"
fi

# Вставляем новую секцию в начало (после заголовка)
TEMP_FILE=$(mktemp)
echo "# Changelog" > "$TEMP_FILE"
echo "" >> "$TEMP_FILE"
echo "$NEW_SECTION" >> "$TEMP_FILE"
# Добавляем остальной контент (если есть)
tail -n +3 "$CHANGELOG_FILE" >> "$TEMP_FILE"  # Пропускаем первые две строки (# Changelog и пустую)
mv "$TEMP_FILE" "$CHANGELOG_FILE"

echo "Changelog updated for $VERSION."
