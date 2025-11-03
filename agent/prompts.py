"""Prompt templates for the AI agent.

These templates provide the system prompt and a user prompt pattern including schema and examples.
"""
from __future__ import annotations

SYSTEM_PROMPT = (
    "You are a SQL assistant. Given a table schema and a natural-language request, produce a single, valid SQL query. "
    "Respond with a JSON object: {{\"sql\": \"...\", \"notes\": \"optional notes\"}}."
)


USER_PROMPT_PATTERN = (
    "Schema columns: {schema}\n"
    "Request: {request}\n"
    "Examples:\n"
    "1) Schema: id INT, name VARCHAR, price FLOAT; Request: 'top 5 expensive items' -> {{\"sql\":\"SELECT id,name,price FROM table ORDER BY price DESC LIMIT 5;\"}}\n"
    "2) Schema: trackid INT, title VARCHAR, milliseconds INT; Request: 'longest tracks over 5 minutes' -> {{\"sql\":\"SELECT trackid,title,milliseconds FROM table WHERE milliseconds > 300000;\"}}\n"
    "Return: a JSON object with keys 'sql' and optional 'notes'."
)
