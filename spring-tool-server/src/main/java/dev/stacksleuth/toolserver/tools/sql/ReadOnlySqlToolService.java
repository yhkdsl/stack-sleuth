package dev.stacksleuth.toolserver.tools.sql;

import dev.stacksleuth.toolserver.api.ToolException;
import java.util.List;
import net.sf.jsqlparser.JSQLParserException;
import net.sf.jsqlparser.parser.CCJSqlParserUtil;
import net.sf.jsqlparser.statement.Statement;
import net.sf.jsqlparser.statement.Statements;
import net.sf.jsqlparser.statement.select.Select;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class ReadOnlySqlToolService {

    public ReadOnlySqlResponse run(ReadOnlySqlRequest request) {
        long startedAt = System.nanoTime();
        validateReadOnly(request.sql());
        long executionTimeMs = (System.nanoTime() - startedAt) / 1_000_000;
        return new ReadOnlySqlResponse("database_not_configured", List.of(), List.of(), 0, executionTimeMs);
    }

    private void validateReadOnly(String sql) {
        if (containsComment(sql)) {
            throw new ToolException("SQL_COMMENT_BLOCKED", "SQL comments are not allowed in tool queries.", HttpStatus.BAD_REQUEST);
        }

        Statements statements;
        try {
            statements = CCJSqlParserUtil.parseStatements(sql);
        } catch (JSQLParserException exception) {
            throw new ToolException("SQL_PARSE_FAILED", "SQL could not be parsed safely.", HttpStatus.BAD_REQUEST);
        }

        if (statements.size() != 1) {
            throw new ToolException("SQL_MULTI_STATEMENT_BLOCKED", "Only a single read-only SQL statement is allowed.", HttpStatus.BAD_REQUEST);
        }

        Statement statement = statements.get(0);
        if (!(statement instanceof Select)) {
            throw new ToolException("SQL_WRITE_BLOCKED", "Only SELECT statements are allowed.", HttpStatus.BAD_REQUEST);
        }
    }

    private static boolean containsComment(String sql) {
        return sql.contains("--") || sql.contains("/*") || sql.contains("*/") || sql.contains("#");
    }
}
