from typing import Any

ToolSchema = dict[str, Any]

TOOL_SCHEMAS: list[ToolSchema] = [
    {
        "type": "function",
        "name": "check_server_health",
        "description": "Check normalized JVM and read-only database availability.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "includeJvm": {"type": "boolean"},
                "includeDbPool": {"type": "boolean"},
            },
            "required": ["includeJvm", "includeDbPool"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_error_logs",
        "description": "Search bounded sample application logs for recent matching records.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100,
                },
                "sinceMinutes": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 1440,
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["keyword", "sinceMinutes", "limit"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "run_read_only_query",
        "description": "Execute one bounded read-only SQL SELECT through the Spring guardrail.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 4000,
                }
            },
            "required": ["sql"],
            "additionalProperties": False,
        },
    },
]
