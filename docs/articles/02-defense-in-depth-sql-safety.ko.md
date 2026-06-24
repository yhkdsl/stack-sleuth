# LLM이 실행하는 SQL을 이중으로 보호하는 방법

**Publication status:** Draft  
**Related implementation:** SQL guardrail and PostgreSQL demo data, Issues #1 and #2  
**External URL:** Not published

## English Summary

StackSleuth protects model-generated SQL with two independent boundaries. JSqlParser limits requests to one bounded read-only query and returns explainable policy errors. PostgreSQL then executes the query through a restricted reader role with read-only transactions, narrow grants, and timeouts. This defense-in-depth design prevents parser validation from becoming the sole authorization mechanism.

## 파서만으로는 충분하지 않다

LLM이 생성한 SQL 앞에 `SELECT`가 있는지만 검사하는 방식은 안전하지 않다. 다중 문장, locking select, `SELECT INTO`, 데이터 변경 CTE처럼 겉보기와 실제 효과가 다른 입력이 존재한다.

반대로 SQL parser가 모든 위험을 완벽하게 막을 것이라고 가정하는 것도 위험하다. parser 버전과 지원 문법이 바뀌고 애플리케이션 코드에 회귀가 생길 수 있기 때문이다.

StackSleuth는 두 개의 독립적인 경계를 둔다.

1. 애플리케이션 경계: SQL을 파싱하고 허용 정책을 설명한다.
2. 데이터베이스 경계: reader 계정의 실제 권한으로 쓰기를 거부한다.

## 1차 경계: 애플리케이션 정책

허용 규칙은 단순하다.

- 문장은 하나만 허용한다.
- 최상위 문장은 `SELECT`여야 한다.
- 주석, locking select, `SELECT INTO`, 데이터 변경 CTE를 차단한다.
- 서버가 결과 행 제한을 강제한다.

위험한 요청 예제:

```bash
curl -X POST http://localhost:8080/internal/tools/sql/read-only \
  -H 'Content-Type: application/json' \
  -H "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  -d '{"sql":"SELECT * FROM users; DELETE FROM users"}'
```

이 요청은 DB로 전달되기 전에 `SQL_MULTI_STATEMENT_BLOCKED`로 거부되어야 한다.

## 2차 경계: PostgreSQL reader 계정

도구 전용 계정은 다음 속성을 가진다.

```sql
ALTER ROLE stacksleuth_reader SET default_transaction_read_only = on;
ALTER ROLE stacksleuth_reader SET statement_timeout = '5s';
ALTER ROLE stacksleuth_reader SET lock_timeout = '1s';

GRANT CONNECT ON DATABASE stacksleuth TO stacksleuth_reader;
GRANT USAGE ON SCHEMA public TO stacksleuth_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO stacksleuth_reader;
```

이 계정은 owner나 애플리케이션 migration 계정과 분리한다. 모델이 parser 우회를 시도하더라도 데이터베이스가 `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` 권한을 제공하지 않는다.

## 자동 검증

권한 설정은 문서만으로 신뢰하지 않는다. 검증 스크립트가 reader 계정으로 실제 쓰기 명령을 실행하고 모두 실패하는지 확인한다.

```bash
infra/scripts/verify-postgres.sh
```

검증 대상:

- reader가 incident 데이터를 `SELECT`할 수 있음
- `default_transaction_read_only=on`
- `statement_timeout=5s`
- `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`가 모두 거부됨
- 거부된 작업 뒤에도 seed row count가 유지됨

## 실패 사례와 관측 가능성

정책 위반은 `rejected`다. 반면 문법상 허용된 query가 존재하지 않는 테이블을 조회해 DB에서 실패하면 `failed`다. 두 경우를 같은 상태로 표시하면 dashboard 사용자는 “보안 정책이 작동한 것인지”와 “인프라가 고장 난 것인지”를 구분할 수 없다.

## 현재 한계

- SQL 함수별 allowlist는 아직 적용하지 않았다.
- 매우 복잡한 읽기 query의 비용은 row limit만으로 제한되지 않는다.
- 운영 환경에서는 DB-level query monitoring과 별도 resource quota가 추가로 필요하다.

이 프로젝트의 목표는 SQL 실행을 무조건 허용하는 것이 아니라, 조사에 필요한 최소 권한을 설명 가능하고 검증 가능한 방식으로 제공하는 것이다.

## 관련 자료

- [Issue #2: Add PostgreSQL demo schema and seed data](https://github.com/yhkdsl/stack-sleuth/issues/2)
- [PR #9: feat: add deterministic PostgreSQL demo data](https://github.com/yhkdsl/stack-sleuth/pull/9)
- [Build log](../BUILD_LOG.md)
- [Beginner tutorial](../TUTORIAL.md)
