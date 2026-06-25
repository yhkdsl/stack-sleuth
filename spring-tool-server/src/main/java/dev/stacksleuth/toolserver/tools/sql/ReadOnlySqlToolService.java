package dev.stacksleuth.toolserver.tools.sql;

import dev.stacksleuth.toolserver.api.ToolException;
import java.sql.ResultSetMetaData;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class ReadOnlySqlToolService {

    private final ReadOnlySqlGuardrail guardrail;
    private final JdbcTemplate jdbcTemplate;

    @Autowired
    public ReadOnlySqlToolService(
        ReadOnlySqlGuardrail guardrail,
        ObjectProvider<JdbcTemplate> jdbcTemplateProvider
    ) {
        this.guardrail = guardrail;
        this.jdbcTemplate = jdbcTemplateProvider.getIfAvailable();
    }

    ReadOnlySqlToolService(ReadOnlySqlGuardrail guardrail, JdbcTemplate jdbcTemplate) {
        this.guardrail = guardrail;
        this.jdbcTemplate = jdbcTemplate;
    }

    public ReadOnlySqlResponse run(ReadOnlySqlRequest request) {
        long startedAt = System.nanoTime();
        PreparedReadOnlyQuery query = guardrail.prepare(request.sql());
        if (jdbcTemplate == null) {
            return response("database_not_configured", List.of(), List.of(), startedAt);
        }

        try {
            QueryResult result = jdbcTemplate.query(query.sql(), resultSet -> {
                ResultSetMetaData metadata = resultSet.getMetaData();
                int columnCount = metadata.getColumnCount();
                List<String> columns = new ArrayList<>(columnCount);
                for (int index = 1; index <= columnCount; index++) {
                    columns.add(metadata.getColumnLabel(index));
                }

                List<Map<String, Object>> rows = new ArrayList<>();
                while (resultSet.next()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    for (int index = 1; index <= columnCount; index++) {
                        row.put(columns.get(index - 1), resultSet.getObject(index));
                    }
                    rows.add(row);
                }
                return new QueryResult(List.copyOf(columns), List.copyOf(rows));
            });
            return response("ok", result.columns(), result.rows(), startedAt);
        } catch (DataAccessException exception) {
            throw new ToolException(
                "SQL_EXECUTION_FAILED",
                "The read-only query could not be executed.",
                HttpStatus.BAD_GATEWAY
            );
        }
    }

    private static ReadOnlySqlResponse response(
        String status,
        List<String> columns,
        List<Map<String, Object>> rows,
        long startedAt
    ) {
        long executionTimeMs = (System.nanoTime() - startedAt) / 1_000_000;
        return new ReadOnlySqlResponse(status, columns, rows, rows.size(), executionTimeMs);
    }

    private record QueryResult(List<String> columns, List<Map<String, Object>> rows) {
    }
}
