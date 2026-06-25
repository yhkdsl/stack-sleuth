from app.tool_schemas import TOOL_SCHEMAS


def test_tool_schemas_are_strict_and_match_router_contract() -> None:
    by_name = {tool["name"]: tool for tool in TOOL_SCHEMAS}

    assert set(by_name) == {
        "check_server_health",
        "search_error_logs",
        "run_read_only_query",
    }

    for tool in by_name.values():
        assert tool["type"] == "function"
        assert tool["strict"] is True
        assert tool["parameters"]["type"] == "object"
        assert tool["parameters"]["additionalProperties"] is False
        assert set(tool["parameters"]["required"]) == set(
            tool["parameters"]["properties"]
        )


def test_tool_schema_bounds_limit_model_control() -> None:
    by_name = {tool["name"]: tool for tool in TOOL_SCHEMAS}

    health = by_name["check_server_health"]["parameters"]["properties"]
    assert health == {
        "includeJvm": {"type": "boolean"},
        "includeDbPool": {"type": "boolean"},
    }

    logs = by_name["search_error_logs"]["parameters"]["properties"]
    assert logs["keyword"]["minLength"] == 1
    assert logs["keyword"]["maxLength"] == 100
    assert logs["sinceMinutes"]["minimum"] == 1
    assert logs["sinceMinutes"]["maximum"] == 1440
    assert logs["limit"]["minimum"] == 1
    assert logs["limit"]["maximum"] == 100

    sql = by_name["run_read_only_query"]["parameters"]["properties"]
    assert sql["sql"]["minLength"] == 1
    assert sql["sql"]["maxLength"] == 4000
