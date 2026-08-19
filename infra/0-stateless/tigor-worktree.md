---
name: tigor-worktree
description: Tigor monorepo workflow — worktrees in ~/.hermes/tigor.worktrees, bare repo in ~/.hermes/tigor. Linear history, rebase-only, github/main is source of truth.
category: infrastructure
tags:
  - git
  - tigor
  - worktree
  - forgejo
  - github
---

# Tigor Worktree Workflow

## Architecture

| | Путь | Роль |
|---|---|---|
| **Bare repo** | `~/.hermes/tigor/` | Git-хранилище (в `.gitignore`) |
| **Worktrees** | `~/.hermes/tigor.worktrees/<task>/` | По одному на задачу, короткие |
| **github/main** | `git@github.com:enovikov11/tigor.git` | **Source of truth** — здесь коммиты, из него деплой/билды |
| **forgejo** | `http://10.67.69.1:3000/hermes/tigor.git` | **Readonly mirror** — пушится вручную из github/main, напрямую не трогается |

## Golden rules

1. **Линейная история** — merge никогда, только rebase
2. **Удаление через revert** — `git revert`, не через удаление коммитов
3. **github/main — source of truth**, пушим туда напрямую после аппрува
4. **Один аппрув** — пользователь говорит «ок» один раз, агент доводит до конца
5. **Новая ветка вместо force-push** — операции rebase/squash пушатся в новую ветку, старая удаляется
6. **Один worktree на чат** — изоляция, ветки не смешиваются

## Workflow

### 1. Старт задачи

Отвести ветку от актуального github/main:

```bash
cd ~/.hermes/tigor
git fetch github main
git worktree add ~/.hermes/tigor.worktrees/<task> -b <task> github/main
```

### 2. Итерации

Работать внутри worktree, коммитить, пушить на forgejo:

```bash
cd ~/.hermes/tigor.worktrees/<task>
git add .
git commit -m "feat: ..."
git push forgejo <task>
```

**После каждой итерации** прилагать ссылку на compare:

```
http://10.67.69.1:3000/hermes/tigor/compare/main...<task>
```

### 3. Аппрув

Пользователь говорит «готово» / «ок» — один раз.

#### 3a. Squash: все коммиты после первого → в первый

```bash
cd ~/.hermes/tigor.worktrees/<task>

# Сохранить message первого коммита
FIRST_MSG=$(git log github/main..HEAD --format=%s --reverse | head -1)

# Squash всё в один коммит с message первого
git reset --soft github/main
git commit -m "$FIRST_MSG"
```

#### 3b. Rebase относительно github/main

```bash
# Обновить базу
git fetch github main

# Ребейзить
git rebase github/main
```

**Если конфликты** — agent останавливается, просит пользователя посмотреть, как разрешилось:

```bash
# После ручного разрешения
git add <resolved-files>
git rebase --continue
```

Потом пушить на forgejo для просмотра:

```bash
NEW_BRANCH="<task>-squashed"

# Если forgejo/main отстал — подтянуть (инвариант: только коммиты из GitHub)
git -C ~/.hermes/tigor fetch github main
git -C ~/.hermes/tigor push forgejo github/main:main

git push forgejo HEAD:$NEW_BRANCH
```

И приложить compare-ссылку на `<task>-squashed`. **Ждать подтверждения.**

**Если конфликтов нет** — пушить сразу:

```bash
NEW_BRANCH="<task>-squashed"

# Подтянуть forgejo/main если отстал — дифф на ревью будет к актуальному main
git -C ~/.hermes/tigor fetch github main
git -C ~/.hermes/tigor push forgejo github/main:main

git push forgejo HEAD:$NEW_BRANCH
```

### 4. Пуш в github/main

После явного подтверждения аппрува:

```bash
git push github HEAD:main
```

**Не создавать ветки на GitHub** — пуш напрямую в main.

### 5. Синхронизация forgejo/main

Ручной пуш из github/main в forgejo/main (когда нужно):

```bash
git -C ~/.hermes/tigor fetch github main
git -C ~/.hermes/tigor push forgejo github/main:main
```

### 6. Очистка

```bash
# Удалить worktree и ветки на forgejo
git -C ~/.hermes/tigor worktree remove ~/.hermes/tigor.worktrees/<task>
git -C ~/.hermes/tigor branch -D <task>
git -C ~/.hermes/tigor branch -D <task>-squashed

# Зачистить ветки на сервере
git push forgejo --delete <task>
git push forgejo --delete <task>-squashed
```

## Utility

### Список worktrees

```bash
git -C ~/.hermes/tigor worktree list
```

### Recovery: запутанные ветки (старый стиль без worktree)

1. Найти активную ветку: `git branch -vv`
2. Посмотреть не закоммиченное: `git status --short`
3. Разделить коммиты: `git rebase -i github/main` — split через `edit` → `git reset HEAD~1` → selective add/commit → `git rebase --continue`
4. Пушить на forgejo для ревью
5. После аппрува — squash и push в github/main по основному воркфлоу
