package dev.stacksleuth.toolserver.tools.sql;

import dev.stacksleuth.toolserver.api.ToolException;
import dev.stacksleuth.toolserver.config.ToolServerProperties;
import java.util.List;
import net.sf.jsqlparser.JSQLParserException;
import net.sf.jsqlparser.parser.CCJSqlParserUtil;
import net.sf.jsqlparser.statement.ParenthesedStatement;
import net.sf.jsqlparser.statement.Statement;
import net.sf.jsqlparser.statement.Statements;
import net.sf.jsqlparser.statement.select.ParenthesedSelect;
import net.sf.jsqlparser.statement.select.ParenthesedFromItem;
import net.sf.jsqlparser.statement.select.PlainSelect;
import net.sf.jsqlparser.statement.select.Select;
import net.sf.jsqlparser.statement.select.SetOperationList;
import net.sf.jsqlparser.statement.select.WithItem;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
public class ReadOnlySqlGuardrail {

    private final ToolServerProperties properties;

    public ReadOnlySqlGuardrail(ToolServerProperties properties) {
        this.properties = properties;
    }

    public PreparedReadOnlyQuery prepare(String sql) {
        if (containsComment(sql)) {
            throw rejected("SQL_COMMENT_BLOCKED", "SQL comments are not allowed in tool queries.");
        }

        Statements statements;
        try {
            statements = CCJSqlParserUtil.parseStatements(sql);
        } catch (JSQLParserException exception) {
            throw rejected("SQL_PARSE_FAILED", "SQL could not be parsed safely.");
        }

        if (statements.size() != 1) {
            throw rejected("SQL_MULTI_STATEMENT_BLOCKED", "Only a single read-only SQL statement is allowed.");
        }

        Statement statement = statements.get(0);
        if (!(statement instanceof Select select)) {
            throw rejected("SQL_WRITE_BLOCKED", "Only SELECT statements are allowed.");
        }

        validateSelect(select);
        int maxRows = properties.sqlMaxRows();
        String boundedSql = "SELECT * FROM (" + select + ") stacksleuth_query LIMIT " + maxRows;
        return new PreparedReadOnlyQuery(boundedSql, maxRows);
    }

    private void validateSelect(Select select) {
        rejectLockingSelect(select);
        validateWithItems(select.getWithItemsList());

        if (select instanceof PlainSelect plainSelect) {
            if ((plainSelect.getIntoTables() != null && !plainSelect.getIntoTables().isEmpty())
                || plainSelect.getIntoTempTable() != null) {
                throw rejected("SQL_WRITE_BLOCKED", "SELECT INTO is not allowed.");
            }
            validateFromItem(plainSelect.getFromItem());
            if (plainSelect.getJoins() != null) {
                plainSelect.getJoins().forEach(join -> validateFromItem(join.getRightItem()));
            }
            return;
        }

        if (select instanceof ParenthesedSelect parenthesedSelect) {
            validateSelect(parenthesedSelect.getSelect());
            return;
        }

        if (select instanceof SetOperationList setOperationList) {
            setOperationList.getSelects().forEach(this::validateSelect);
        }
    }

    private void validateFromItem(net.sf.jsqlparser.statement.select.FromItem fromItem) {
        if (fromItem instanceof Select nestedSelect) {
            validateSelect(nestedSelect);
        } else if (fromItem instanceof ParenthesedFromItem parenthesedFromItem) {
            validateFromItem(parenthesedFromItem.getFromItem());
            if (parenthesedFromItem.getJoins() != null) {
                parenthesedFromItem.getJoins().forEach(join -> validateFromItem(join.getRightItem()));
            }
        }
    }

    private void validateWithItems(List<WithItem<?>> withItems) {
        if (withItems == null) {
            return;
        }

        for (WithItem<?> withItem : withItems) {
            ParenthesedStatement statement = withItem.getParenthesedStatement();
            if (statement instanceof ParenthesedSelect parenthesedSelect) {
                validateSelect(parenthesedSelect);
            } else {
                throw rejected("SQL_WRITE_BLOCKED", "Data-modifying common table expressions are not allowed.");
            }
        }
    }

    private void rejectLockingSelect(Select select) {
        if (select.getForClause() != null || select.getForMode() != null || select.getForUpdateTable() != null) {
            throw rejected("SQL_LOCK_BLOCKED", "Locking SELECT statements are not allowed.");
        }
    }

    private static ToolException rejected(String code, String message) {
        return new ToolException(code, message, HttpStatus.BAD_REQUEST);
    }

    private static boolean containsComment(String sql) {
        return sql.contains("--") || sql.contains("/*") || sql.contains("*/") || sql.contains("#");
    }
}
