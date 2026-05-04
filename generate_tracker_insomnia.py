#!/usr/bin/env python3
"""
Generates an Insomnia v5 YAML collection for Yandex Tracker public API (v3).
All endpoints are sourced from: https://yandex.ru/support/tracker/ru/api-ref/about-api
"""

import sys
import json
import uuid
import time

sys.path.insert(0, ".pip")
import yaml

BASE_URL = "https://api.tracker.yandex.net"
DOCS_BASE = "https://yandex.ru/support/tracker/ru/api-ref"
NOW_MS = int(time.time() * 1000)


# ---------------------------------------------------------------------------
# Full endpoint list: (folder, name, method, path, query_params, body)
# ---------------------------------------------------------------------------
ENDPOINTS = [

    # ── ЗАДАЧИ ──────────────────────────────────────────────────────────────
    ("Задачи", "Создать задачу", "POST", "/v3/issues/",
     [],
     {"summary": "<название задачи>", "queue": {"id": "1", "key": "<ключ очереди>"},
      "parent": None, "description": None, "type": None, "priority": None,
      "assignee": None, "followers": None, "tags": None, "components": None,
      "sprint": None, "attachmentIds": None}),

    ("Задачи", "Получить задачу", "GET", "/v3/issues/{issueId}",
     [("expand", ""), ("fields", "")], None),

    ("Задачи", "Редактировать задачу", "PATCH", "/v3/issues/{issueId}",
     [("notify", "true")],
     {"summary": "<новое название>", "description": None, "type": None,
      "priority": None, "assignee": None, "followers": None}),

    ("Задачи", "Переместить задачу в другую очередь", "POST", "/v3/issues/{issueId}/_move",
     [("queue", "<ключ очереди>")], None),

    ("Задачи", "Удалить задачу", "DELETE", "/v3/issues/{issueId}", [], None),

    ("Задачи", "Найти задачи (фильтр)", "GET", "/v3/issues",
     [("queue", "<ключ очереди>"), ("filter", ""), ("perPage", "50"), ("page", "1")], None),

    ("Задачи", "Найти задачи (поиск)", "POST", "/v3/issues/_search",
     [("perPage", "50"), ("page", "1")],
     {"query": "<текст запроса на языке Яндекс.Трекера>",
      "filter": {"queue": "<ключ очереди>", "assignee": "<логин>"},
      "order": "+updatedAt", "expand": "transitions,attachments"}),

    ("Задачи", "Получить количество задач", "POST", "/v3/issues/_count",
     [],
     {"query": "<текст запроса>",
      "filter": {"queue": "<ключ очереди>"}}),

    ("Задачи", "Получить историю изменений задачи", "GET", "/v3/issues/{issueId}/changelog",
     [("perPage", "50"), ("page", "1"), ("field", ""), ("type", "")], None),

    ("Задачи", "Получить переходы задачи", "GET", "/v3/issues/{issueId}/transitions", [], None),

    ("Задачи", "Выполнить переход в статус", "POST", "/v3/issues/{issueId}/transitions/{transitionId}/_execute",
     [],
     {"comment": "<комментарий при переходе>",
      "resolution": {"key": "fixed"}}),

    # ── СВЯЗИ ЗАДАЧИ ─────────────────────────────────────────────────────────
    ("Задачи — связи", "Получить связи задачи", "GET", "/v3/issues/{issueId}/links", [], None),

    ("Задачи — связи", "Создать связь задачи", "POST", "/v3/issues/{issueId}/links",
     [],
     {"relationship": "relates", "issue": "<ключ связанной задачи>"}),

    ("Задачи — связи", "Удалить связь задачи", "DELETE", "/v3/issues/{issueId}/links/{linkId}",
     [], None),

    # ── ВНЕШНИЕ СВЯЗИ ────────────────────────────────────────────────────────
    ("Задачи — внешние связи", "Получить внешние связи задачи", "GET",
     "/v3/issues/{issueId}/remotelinks", [], None),

    ("Задачи — внешние связи", "Создать внешнюю связь", "POST",
     "/v3/issues/{issueId}/remotelinks",
     [],
     {"relationship": "relates", "url": "https://example.com/task/123",
      "title": "<название ссылки>"}),

    ("Задачи — внешние связи", "Получить внешнюю связь", "GET",
     "/v3/issues/{issueId}/remotelinks/{remoteLinkId}", [], None),

    ("Задачи — внешние связи", "Изменить внешнюю связь", "PATCH",
     "/v3/issues/{issueId}/remotelinks/{remoteLinkId}",
     [],
     {"relationship": "relates", "url": "https://example.com/task/123",
      "title": "<новое название>"}),

    ("Задачи — внешние связи", "Удалить внешнюю связь", "DELETE",
     "/v3/issues/{issueId}/remotelinks/{remoteLinkId}", [], None),

    # ── ФИЛЬТРЫ ──────────────────────────────────────────────────────────────
    ("Фильтры задач", "Получить все фильтры", "GET", "/v3/filters",
     [("owner", ""), ("perPage", "50"), ("page", "1")], None),

    ("Фильтры задач", "Создать фильтр", "POST", "/v3/filters",
     [],
     {"name": "<название фильтра>",
      "query": {"queue": "<ключ очереди>", "assignee": "<логин>"},
      "filter": "queue: <ключ>"}),

    ("Фильтры задач", "Получить фильтр", "GET", "/v3/filters/{filterId}", [], None),

    ("Фильтры задач", "Изменить фильтр", "PATCH", "/v3/filters/{filterId}",
     [],
     {"name": "<новое название>",
      "query": {"queue": "<ключ очереди>"}}),

    ("Фильтры задач", "Удалить фильтр", "DELETE", "/v3/filters/{filterId}", [], None),

    # ── ЧЕКЛИСТЫ ─────────────────────────────────────────────────────────────
    ("Чеклисты", "Получить чеклист задачи", "GET",
     "/v3/issues/{issueId}/checklistItems", [], None),

    ("Чеклисты", "Создать чеклист", "POST",
     "/v3/issues/{issueId}/checklistItems",
     [],
     [{"text": "<текст пункта>", "checked": False, "assignee": None, "deadline": None}]),

    ("Чеклисты", "Изменить порядок и содержимое чеклиста", "PATCH",
     "/v3/issues/{issueId}/checklistItems",
     [],
     [{"id": "<id пункта>", "text": "<текст>", "checked": False}]),

    ("Чеклисты", "Изменить пункт чеклиста", "PATCH",
     "/v3/issues/{issueId}/checklistItems/{checklistItemId}",
     [],
     {"text": "<новый текст>", "checked": True}),

    ("Чеклисты", "Удалить пункт чеклиста", "DELETE",
     "/v3/issues/{issueId}/checklistItems/{checklistItemId}", [], None),

    ("Чеклисты", "Удалить все пункты чеклиста", "DELETE",
     "/v3/issues/{issueId}/checklistItems", [], None),

    # ── КОММЕНТАРИИ ──────────────────────────────────────────────────────────
    ("Комментарии", "Получить все комментарии к задаче", "GET",
     "/v3/issues/{issueId}/comments",
     [("perPage", "50"), ("page", "1")], None),

    ("Комментарии", "Добавить комментарий к задаче", "POST",
     "/v3/issues/{issueId}/comments",
     [],
     {"text": "<текст комментария>",
      "summonees": ["<логин_1>"],
      "maillistSummonees": ["<почтовый список>"]}),

    ("Комментарии", "Изменить комментарий", "PATCH",
     "/v3/issues/{issueId}/comments/{commentId}",
     [],
     {"text": "<новый текст>"}),

    ("Комментарии", "Удалить комментарий", "DELETE",
     "/v3/issues/{issueId}/comments/{commentId}", [], None),

    # ── ПРИКРЕПЛЁННЫЕ ФАЙЛЫ ──────────────────────────────────────────────────
    ("Прикреплённые файлы", "Получить список файлов задачи", "GET",
     "/v3/issues/{issueId}/attachments", [], None),

    ("Прикреплённые файлы", "Прикрепить файл к задаче", "POST",
     "/v3/issues/{issueId}/attachments/{attachmentId}", [], None),

    ("Прикреплённые файлы", "Скачать файл задачи", "GET",
     "/v3/issues/{issueId}/attachments/{attachmentId}/{filename}", [], None),

    ("Прикреплённые файлы", "Удалить файл задачи", "DELETE",
     "/v3/issues/{issueId}/attachments/{attachmentId}", [], None),

    ("Прикреплённые файлы", "Создать временный файл", "POST",
     "/v3/attachments", [], None),

    # ── ПАКЕТНЫЕ ОПЕРАЦИИ ────────────────────────────────────────────────────
    ("Пакетные операции", "Массово изменить задачи", "POST",
     "/v3/bulkchange/_update",
     [],
     {"issues": ["<ключ задачи 1>", "<ключ задачи 2>"],
      "values": {"priority": {"id": "2", "key": "normal"},
                 "assignee": "<логин>"}}),

    ("Пакетные операции", "Массово выполнить переход в статус", "POST",
     "/v3/bulkchange/_transition",
     [],
     {"issues": ["<ключ задачи 1>", "<ключ задачи 2>"],
      "transition": {"id": "<id перехода>"}}),

    ("Пакетные операции", "Массово переместить задачи", "POST",
     "/v3/bulkchange/_move",
     [("queue", "<ключ очереди назначения>")],
     {"issues": ["<ключ задачи 1>", "<ключ задачи 2>"]}),

    ("Пакетные операции", "Получить статус пакетной операции", "GET",
     "/v3/bulkchange/{bulkchangeId}", [], None),

    # ── ПОЛЯ ЗАДАЧИ ──────────────────────────────────────────────────────────
    ("Поля задачи", "Получить доступные глобальные поля", "GET",
     "/v3/fields", [("category", ""), ("perPage", "50"), ("page", "1")], None),

    ("Поля задачи", "Создать глобальное поле задачи", "POST",
     "/v3/fields",
     [],
     {"name": {"ru": "<название поля на русском>", "en": "<field name>"},
      "id": "<ключ поля>",
      "category": {"id": "<id категории>"},
      "type": "string",
      "readonly": False, "options": False, "suggest": False, "optionsProvider": None}),

    # ── ПРОЕКТЫ, ПОРТФЕЛИ, ЦЕЛИ (новый API) ──────────────────────────────────
    ("Проекты, портфели, цели", "Создать сущность (проект/портфель/цель)", "POST",
     "/v3/entities/{entityType}",
     [],
     {"fields": {"summary": "<название>", "teamUsers": [{"id": "<id пользователя>"}],
                 "description": None, "deadline": None, "start": None}}),

    ("Проекты, портфели, цели", "Получить сущность", "GET",
     "/v3/entities/{entityType}/{entityId}",
     [("expand", ""), ("fields", "")], None),

    ("Проекты, портфели, цели", "Изменить сущность", "PATCH",
     "/v3/entities/{entityType}/{entityId}",
     [],
     {"fields": {"summary": "<новое название>", "description": None}}),

    ("Проекты, портфели, цели", "Удалить сущность", "DELETE",
     "/v3/entities/{entityType}/{entityId}", [], None),

    ("Проекты, портфели, цели", "Найти сущности", "POST",
     "/v3/entities/{entityType}/_search",
     [("perPage", "50"), ("page", "1")],
     {"filter": {"author": {"id": "<id автора>"}},
      "orderBy": "updatedAt", "orderAsc": False}),

    ("Проекты, портфели, цели", "Получить историю событий сущности", "GET",
     "/v3/entities/{entityType}/{entityId}/events",
     [("perPage", "50"), ("after", "")], None),

    # ── КОММЕНТАРИИ К СУЩНОСТИ ───────────────────────────────────────────────
    ("Сущности — комментарии", "Получить комментарии к сущности", "GET",
     "/v3/entities/{entityType}/{entityId}/comments",
     [("perPage", "50"), ("after", "")], None),

    ("Сущности — комментарии", "Добавить комментарий к сущности", "POST",
     "/v3/entities/{entityType}/{entityId}/comments",
     [],
     {"text": "<текст комментария>"}),

    ("Сущности — комментарии", "Изменить комментарий сущности", "PATCH",
     "/v3/entities/{entityType}/{entityId}/comments/{commentId}",
     [],
     {"text": "<новый текст>"}),

    ("Сущности — комментарии", "Удалить комментарий сущности", "DELETE",
     "/v3/entities/{entityType}/{entityId}/comments/{commentId}", [], None),

    # ── ФАЙЛЫ СУЩНОСТИ ───────────────────────────────────────────────────────
    ("Сущности — файлы", "Получить список файлов сущности", "GET",
     "/v3/entities/{entityType}/{entityId}/attachments", [], None),

    ("Сущности — файлы", "Прикрепить файл к сущности", "POST",
     "/v3/entities/{entityType}/{entityId}/attachments/{attachmentId}", [], None),

    ("Сущности — файлы", "Удалить файл сущности", "DELETE",
     "/v3/entities/{entityType}/{entityId}/attachments/{attachmentId}", [], None),

    # ── СВЯЗИ СУЩНОСТИ ────────────────────────────────────────────────────────
    ("Сущности — связи", "Получить связи сущности", "GET",
     "/v3/entities/{entityType}/{entityId}/links", [], None),

    ("Сущности — связи", "Создать связь сущности", "POST",
     "/v3/entities/{entityType}/{entityId}/links",
     [],
     {"entities": [{"id": "<id связанной сущности>"}],
      "relationship": "relates"}),

    ("Сущности — связи", "Удалить связь сущности", "DELETE",
     "/v3/entities/{entityType}/{entityId}/links/{linkId}", [], None),

    # ── ЧЕКЛИСТ СУЩНОСТИ ──────────────────────────────────────────────────────
    ("Сущности — чеклист", "Получить чеклист сущности", "GET",
     "/v3/entities/{entityType}/{entityId}/checklistItems", [], None),

    ("Сущности — чеклист", "Создать чеклист сущности", "POST",
     "/v3/entities/{entityType}/{entityId}/checklistItems",
     [],
     [{"text": "<текст пункта>", "checked": False}]),

    ("Сущности — чеклист", "Изменить чеклист сущности", "PATCH",
     "/v3/entities/{entityType}/{entityId}/checklistItems",
     [],
     [{"id": "<id пункта>", "text": "<текст>", "checked": False}]),

    ("Сущности — чеклист", "Изменить пункт чеклиста сущности", "PATCH",
     "/v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}",
     [],
     {"text": "<новый текст>", "checked": True}),

    ("Сущности — чеклист", "Удалить пункт чеклиста сущности", "DELETE",
     "/v3/entities/{entityType}/{entityId}/checklistItems/{checklistItemId}", [], None),

    ("Сущности — чеклист", "Удалить все пункты чеклиста сущности", "DELETE",
     "/v3/entities/{entityType}/{entityId}/checklistItems", [], None),

    # ── ПРОЕКТЫ (СТАРАЯ ВЕРСИЯ) ───────────────────────────────────────────────
    ("Проекты (старая версия)", "Получить все проекты", "GET", "/v3/projects",
     [("perPage", "50"), ("page", "1")], None),

    ("Проекты (старая версия)", "Создать проект", "POST", "/v3/projects",
     [],
     {"name": "<название проекта>", "queues": [{"id": "1", "key": "<ключ очереди>"}],
      "description": None, "lead": None, "members": None}),

    ("Проекты (старая версия)", "Получить проект", "GET",
     "/v3/projects/{projectId}", [], None),

    ("Проекты (старая версия)", "Изменить проект", "PATCH",
     "/v3/projects/{projectId}",
     [],
     {"name": "<новое название>", "description": None}),

    ("Проекты (старая версия)", "Удалить проект", "DELETE",
     "/v3/projects/{projectId}", [], None),

    ("Проекты (старая версия)", "Получить задачи проекта", "GET",
     "/v3/projects/{projectId}/issues",
     [("perPage", "50"), ("page", "1")], None),

    # ── ОЧЕРЕДИ ───────────────────────────────────────────────────────────────
    ("Очереди", "Получить все очереди", "GET", "/v3/queues",
     [("perPage", "50"), ("page", "1"), ("expand", "")], None),

    ("Очереди", "Получить очередь", "GET", "/v3/queues/{queueId}",
     [("expand", "")], None),

    ("Очереди", "Получить поля очереди", "GET", "/v3/queues/{queueId}/fields", [], None),

    ("Очереди", "Получить теги очереди", "GET", "/v3/queues/{queueId}/tags", [], None),

    ("Очереди", "Удалить очередь", "DELETE", "/v3/queues/{queueId}", [], None),

    ("Очереди", "Восстановить очередь из архива", "POST",
     "/v3/queues/{queueId}/_restore", [], None),

    # ── ОЧЕРЕДИ — ВЕРСИИ ──────────────────────────────────────────────────────
    ("Очереди — версии", "Получить версии очереди", "GET",
     "/v3/queues/{queueId}/versions", [], None),

    ("Очереди — версии", "Создать версию", "POST",
     "/v3/queues/{queueId}/versions",
     [],
     {"name": "<название версии>", "description": None,
      "startDate": None, "dueDate": None}),

    ("Очереди — версии", "Получить версию", "GET",
     "/v3/queues/{queueId}/versions/{versionId}", [], None),

    ("Очереди — версии", "Изменить версию", "PATCH",
     "/v3/queues/{queueId}/versions/{versionId}",
     [],
     {"name": "<новое название>", "description": None}),

    # ── ОЧЕРЕДИ — КОМПОНЕНТЫ ──────────────────────────────────────────────────
    ("Очереди — компоненты", "Получить компоненты очереди", "GET",
     "/v3/queues/{queueId}/components", [], None),

    ("Очереди — компоненты", "Создать компонент", "POST",
     "/v3/queues/{queueId}/components",
     [],
     {"name": "<название компонента>", "description": None, "lead": None,
      "assignAuto": False}),

    ("Очереди — компоненты", "Получить компонент", "GET",
     "/v3/queues/{queueId}/components/{componentId}", [], None),

    ("Очереди — компоненты", "Изменить компонент", "PATCH",
     "/v3/queues/{queueId}/components/{componentId}",
     [],
     {"name": "<новое название>", "description": None}),

    ("Очереди — компоненты", "Удалить компонент", "DELETE",
     "/v3/queues/{queueId}/components/{componentId}", [], None),

    # ── ОЧЕРЕДИ — ЛОКАЛЬНЫЕ ПОЛЯ ──────────────────────────────────────────────
    ("Очереди — локальные поля", "Получить локальные поля очереди", "GET",
     "/v3/queues/{queueId}/localFields", [], None),

    ("Очереди — локальные поля", "Создать локальное поле", "POST",
     "/v3/queues/{queueId}/localFields",
     [],
     {"id": "<ключ поля>",
      "name": {"ru": "<название>", "en": "<name>"},
      "type": "string",
      "category": {"id": "<id категории>"}}),

    ("Очереди — локальные поля", "Получить локальное поле", "GET",
     "/v3/queues/{queueId}/localFields/{fieldId}", [], None),

    ("Очереди — локальные поля", "Изменить локальное поле", "PATCH",
     "/v3/queues/{queueId}/localFields/{fieldId}",
     [],
     {"name": {"ru": "<новое название>"}}),

    ("Очереди — локальные поля", "Удалить локальное поле", "DELETE",
     "/v3/queues/{queueId}/localFields/{fieldId}", [], None),

    # ── АВТОДЕЙСТВИЯ ──────────────────────────────────────────────────────────
    ("Автодействия", "Получить все автодействия очереди", "GET",
     "/v3/queues/{queueId}/autoactions", [], None),

    ("Автодействия", "Создать автодействие", "POST",
     "/v3/queues/{queueId}/autoactions",
     [],
     {"name": "<название>",
      "filter": [{"type": "AssigneeFilter",
                  "user": {"id": "<id пользователя>"}}],
      "actions": [{"type": "Transition",
                   "status": {"key": "closed"}}]}),

    ("Автодействия", "Получить автодействие", "GET",
     "/v3/queues/{queueId}/autoactions/{autoactionId}", [], None),

    ("Автодействия", "Изменить автодействие", "PATCH",
     "/v3/queues/{queueId}/autoactions/{autoactionId}",
     [],
     {"name": "<новое название>"}),

    ("Автодействия", "Удалить автодействие", "DELETE",
     "/v3/queues/{queueId}/autoactions/{autoactionId}", [], None),

    # ── ТРИГГЕРЫ ──────────────────────────────────────────────────────────────
    ("Триггеры", "Получить все триггеры очереди", "GET",
     "/v3/queues/{queueId}/triggers",
     [("perPage", "50"), ("page", "1")], None),

    ("Триггеры", "Создать триггер", "POST",
     "/v3/queues/{queueId}/triggers",
     [],
     {"name": "<название триггера>",
      "conditions": [{"type": "FieldChangedCondition",
                      "field": {"id": "status"},
                      "from": None, "to": {"key": "closed"}}],
      "actions": [{"type": "CommentAction",
                   "body": "<текст комментария>"}]}),

    ("Триггеры", "Получить триггер", "GET",
     "/v3/queues/{queueId}/triggers/{triggerId}", [], None),

    ("Триггеры", "Изменить триггер", "PATCH",
     "/v3/queues/{queueId}/triggers/{triggerId}",
     [],
     {"name": "<новое название>", "active": True}),

    ("Триггеры", "Удалить триггер", "DELETE",
     "/v3/queues/{queueId}/triggers/{triggerId}", [], None),

    # ── МАКРОСЫ ───────────────────────────────────────────────────────────────
    ("Макросы", "Получить все макросы очереди", "GET",
     "/v3/queues/{queueId}/macros", [], None),

    ("Макросы", "Создать макрос", "POST",
     "/v3/queues/{queueId}/macros",
     [],
     {"name": "<название макроса>",
      "body": "<текст комментария, добавляемого при исполнении>",
      "actions": [{"type": "transition",
                   "status": {"key": "closed"}}]}),

    ("Макросы", "Получить макрос", "GET",
     "/v3/queues/{queueId}/macros/{macroId}", [], None),

    ("Макросы", "Изменить макрос", "PATCH",
     "/v3/queues/{queueId}/macros/{macroId}",
     [],
     {"name": "<новое название>", "body": None}),

    ("Макросы", "Удалить макрос", "DELETE",
     "/v3/queues/{queueId}/macros/{macroId}", [], None),

    # ── ДОСКИ ЗАДАЧ ───────────────────────────────────────────────────────────
    ("Доски задач", "Получить все доски", "GET", "/v3/boards",
     [("perPage", "50"), ("page", "1")], None),

    ("Доски задач", "Получить доску", "GET", "/v3/boards/{boardId}", [], None),

    ("Доски задач", "Создать доску", "POST", "/v3/boards",
     [],
     {"name": "<название доски>",
      "boardType": "scrum",
      "filter": {"queue": [{"key": "<ключ очереди>"}]}}),

    ("Доски задач", "Изменить доску", "PATCH", "/v3/boards/{boardId}",
     [],
     {"name": "<новое название>"}),

    ("Доски задач", "Удалить доску", "DELETE", "/v3/boards/{boardId}", [], None),

    # ── ДОСКИ — КОЛОНКИ ───────────────────────────────────────────────────────
    ("Доски — колонки", "Получить колонки доски", "GET",
     "/v3/boards/{boardId}/columns", [], None),

    ("Доски — колонки", "Создать колонку доски", "POST",
     "/v3/boards/{boardId}/columns",
     [],
     {"name": "<название колонки>",
      "statuses": [{"key": "open"}]}),

    ("Доски — колонки", "Получить колонку доски", "GET",
     "/v3/boards/{boardId}/columns/{columnId}", [], None),

    ("Доски — колонки", "Изменить колонку доски", "PATCH",
     "/v3/boards/{boardId}/columns/{columnId}",
     [],
     {"name": "<новое название>", "statuses": None}),

    ("Доски — колонки", "Удалить колонку доски", "DELETE",
     "/v3/boards/{boardId}/columns/{columnId}", [], None),

    # ── ДОСКИ — СПРИНТЫ ───────────────────────────────────────────────────────
    ("Доски — спринты", "Получить спринты доски", "GET",
     "/v3/boards/{boardId}/sprints",
     [("perPage", "50"), ("page", "1")], None),

    ("Доски — спринты", "Создать спринт", "POST",
     "/v3/boards/{boardId}/sprints",
     [],
     {"name": "<название спринта>",
      "startDate": "2024-01-01T00:00:00.000+0000",
      "endDate": "2024-01-14T00:00:00.000+0000"}),

    ("Доски — спринты", "Получить спринт", "GET",
     "/v3/boards/{boardId}/sprints/{sprintId}", [], None),

    ("Доски — спринты", "Изменить спринт", "PATCH",
     "/v3/boards/{boardId}/sprints/{sprintId}",
     [],
     {"name": "<новое название>",
      "startDate": None, "endDate": None}),

    ("Доски — спринты", "Удалить спринт", "DELETE",
     "/v3/boards/{boardId}/sprints/{sprintId}", [], None),

    # ── ДАШБОРДЫ ──────────────────────────────────────────────────────────────
    ("Дашборды", "Получить все дашборды", "GET", "/v3/dashboards",
     [("perPage", "50"), ("page", "1")], None),

    ("Дашборды", "Получить дашборд", "GET", "/v3/dashboards/{dashboardId}", [], None),

    ("Дашборды", "Создать дашборд", "POST", "/v3/dashboards",
     [],
     {"name": "<название дашборда>",
      "widgets": []}),

    ("Дашборды", "Изменить дашборд", "PATCH", "/v3/dashboards/{dashboardId}",
     [],
     {"name": "<новое название>"}),

    ("Дашборды", "Удалить дашборд", "DELETE", "/v3/dashboards/{dashboardId}", [], None),

    # ── КОМПОНЕНТЫ (глобальные) ───────────────────────────────────────────────
    ("Компоненты", "Получить все компоненты", "GET", "/v3/components",
     [("perPage", "50"), ("page", "1")], None),

    ("Компоненты", "Создать компонент", "POST", "/v3/components",
     [],
     {"name": "<название>",
      "queue": {"id": "1", "key": "<ключ очереди>"},
      "description": None, "lead": None, "assignAuto": False}),

    ("Компоненты", "Получить компонент", "GET",
     "/v3/components/{componentId}", [], None),

    ("Компоненты", "Изменить компонент", "PATCH",
     "/v3/components/{componentId}",
     [],
     {"name": "<новое название>", "description": None}),

    ("Компоненты", "Удалить компонент", "DELETE",
     "/v3/components/{componentId}", [], None),

    # ── ТИПЫ, СТАТУСЫ, РЕЗОЛЮЦИИ, ПРИОРИТЕТЫ ─────────────────────────────────
    ("Типы задач", "Получить все типы задач", "GET", "/v3/issuetypes",
     [("perPage", "50"), ("page", "1")], None),

    ("Типы задач", "Получить тип задачи", "GET",
     "/v3/issuetypes/{typeId}", [], None),

    ("Статусы", "Получить все статусы", "GET", "/v3/statuses",
     [("perPage", "50"), ("page", "1")], None),

    ("Статусы", "Получить статус", "GET",
     "/v3/statuses/{statusId}", [], None),

    ("Резолюции", "Получить все резолюции", "GET", "/v3/resolutions",
     [("perPage", "50"), ("page", "1")], None),

    ("Резолюции", "Получить резолюцию", "GET",
     "/v3/resolutions/{resolutionId}", [], None),

    ("Приоритеты", "Получить все приоритеты", "GET", "/v3/priorities",
     [("perPage", "50"), ("page", "1")], None),

    ("Приоритеты", "Получить приоритет", "GET",
     "/v3/priorities/{priorityId}", [], None),

    # ── УЧЁТ ВРЕМЕНИ ─────────────────────────────────────────────────────────
    ("Учёт времени", "Получить записи о времени задачи", "GET",
     "/v3/issues/{issueId}/worklogs", [], None),

    ("Учёт времени", "Добавить запись о затраченном времени", "POST",
     "/v3/issues/{issueId}/worklogs",
     [],
     {"start": "2024-01-15T10:00:00.000+0000",
      "duration": "PT3H", "comment": "<комментарий>"}),

    ("Учёт времени", "Изменить запись о затраченном времени", "PATCH",
     "/v3/issues/{issueId}/worklogs/{worklogId}",
     [],
     {"start": "2024-01-15T10:00:00.000+0000",
      "duration": "PT3H", "comment": "<новый комментарий>"}),

    ("Учёт времени", "Удалить запись о затраченном времени", "DELETE",
     "/v3/issues/{issueId}/worklogs/{worklogId}", [], None),

    # ── ИМПОРТ ────────────────────────────────────────────────────────────────
    ("Импорт", "Импортировать задачи", "POST", "/v3/issues/_import",
     [],
     {"queue": {"key": "<ключ очереди>"},
      "summary": "<название задачи>",
      "createdBy": {"id": "<id автора>"},
      "createdAt": "2024-01-01T00:00:00.000+0000",
      "comments": [], "attachments": [], "links": []}),

    ("Импорт", "Импортировать файлы к задаче", "POST",
     "/v3/issues/{issueId}/attachments/_import",
     [],
     {"createdBy": {"id": "<id пользователя>"},
      "createdAt": "2024-01-01T00:00:00.000+0000"}),

    ("Импорт", "Импортировать комментарии к задаче", "POST",
     "/v3/issues/{issueId}/comments/_import",
     [],
     {"text": "<текст комментария>",
      "createdBy": {"id": "<id автора>"},
      "createdAt": "2024-01-01T00:00:00.000+0000"}),

    ("Импорт", "Импортировать записи о времени", "POST",
     "/v3/issues/{issueId}/worklogs/_import",
     [],
     {"start": "2024-01-15T10:00:00.000+0000",
      "duration": "PT3H",
      "createdBy": {"id": "<id автора>"},
      "createdAt": "2024-01-01T00:00:00.000+0000"}),

    # ── ПОЛЬЗОВАТЕЛИ ──────────────────────────────────────────────────────────
    ("Пользователи", "Получить текущего пользователя", "GET", "/v3/myself", [], None),

    ("Пользователи", "Получить список пользователей организации", "GET", "/v3/users",
     [("perPage", "50"), ("page", "1")], None),

    ("Пользователи", "Получить пользователя по ID", "GET",
     "/v3/users/{userId}", [], None),
]


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def make_id(prefix="req"):
    return f"{prefix}_{uuid.uuid4().hex}"


def make_request(folder, name, method, path, query_params, body, sort_key):
    url = BASE_URL + path
    headers = [
        {"name": "Authorization", "value": "OAuth {{token}}"},
        {"name": "X-Org-ID", "value": "{{org_id}}"},
    ]

    request = {
        "url": url,
        "name": name,
        "meta": {
            "id": make_id("req"),
            "created": NOW_MS,
            "modified": NOW_MS,
            "isPrivate": False,
            "description": (
                f"Документация: {DOCS_BASE}/\n"
                f"Метод: {method} {url}"
            ),
            "sortKey": sort_key,
        },
        "method": method,
        "headers": headers,
        "settings": {
            "renderRequestBody": True,
            "encodeUrl": True,
            "followRedirects": "global",
            "cookies": {"send": True, "store": True},
            "rebuildPath": True,
        },
    }

    if body is not None:
        request["headers"].append({"name": "Content-Type", "value": "application/json"})
        # Filter out None values for cleaner bodies
        if isinstance(body, dict):
            clean_body = {k: v for k, v in body.items() if v is not None}
        else:
            clean_body = body
        request["body"] = {
            "mimeType": "application/json",
            "text": json.dumps(clean_body, ensure_ascii=False, indent=2),
        }

    if query_params:
        request["parameters"] = [
            {"name": k, "value": v, "disabled": v == ""} for k, v in query_params
        ]

    return request


def main():
    from collections import OrderedDict
    folders = OrderedDict()
    sort_counter = 0

    for folder, name, method, path, query_params, body in ENDPOINTS:
        sort_counter -= 50
        req = make_request(folder, name, method, path, query_params, body, sort_counter)
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(req)

    collection = []
    folder_sort = 0
    for folder_name, requests in folders.items():
        folder_sort -= 100
        collection.append({
            "name": folder_name,
            "meta": {
                "id": make_id("fld"),
                "created": NOW_MS,
                "modified": NOW_MS,
                "sortKey": folder_sort,
            },
            "children": requests,
        })

    output = {
        "type": "collection.insomnia.rest/5.0",
        "schema_version": "5.1",
        "name": "Yandex Tracker API v3",
        "meta": {
            "id": make_id("wrk"),
            "created": NOW_MS,
            "modified": NOW_MS,
            "description": (
                "Коллекция по документации:\n"
                "https://yandex.ru/support/tracker/ru/api-ref/about-api\n\n"
                "Переменные окружения:\n"
                "  token       — OAuth-токен (Authorization: OAuth {{token}})\n"
                "  org_id      — ID организации Яндекс 360 (X-Org-ID)\n"
                "  cloud_org_id — ID организации Yandex Cloud (X-Cloud-Org-ID)"
            ),
        },
        "collection": collection,
    }

    out_path = "Tracker_API_Insomnia.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False,
                  default_flow_style=False, width=120)

    total = sum(len(v) for v in folders.values())
    print(f"Saved: {out_path}")
    print(f"Folders: {len(collection)} | Requests: {total}")
    for folder_name, reqs in folders.items():
        print(f"  {folder_name}: {len(reqs)}")


if __name__ == "__main__":
    main()
