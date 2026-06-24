# Spring Boot를 AI Agent의 안전한 Tool Server로 만들기

**Publication status:** Draft  
**Related implementation:** Spring Boot tool server, Issue #1  
**External URL:** Not published

## English Summary

This article explains how StackSleuth turns a Spring Boot application into a bounded tool server for an AI agent. Instead of exposing arbitrary backend access, the service offers authenticated, validated, deterministic endpoints for health inspection, log search, and read-only SQL. It also records trace and request identifiers without exposing raw Actuator data or secrets.

## 이 글에서 다루는 것

AI 에이전트에게 백엔드 기능을 연결할 때 중요한 질문은 “모델이 무엇을 할 수 있는가”보다 “애플리케이션이 어디까지 허용하는가”다. StackSleuth의 Spring Boot 서버는 모델 전용 만능 관리 API가 아니라, 입력과 출력이 제한된 세 개의 조사 도구를 제공한다.

```http
POST /internal/tools/health
POST /internal/tools/logs/search
POST /internal/tools/sql/read-only
```

독자는 다음 내용을 배울 수 있다.

- 모델이 호출하기 쉬운 작은 도구 API를 설계하는 방법
- 내부 도구 인증과 요청 검증을 분리하는 이유
- raw Actuator 응답 대신 안전한 DTO를 반환하는 이유
- 도구 성공, 정책 거부, 실행 실패를 감사 로그에서 구분하는 방법

## 왜 Spring Boot를 Tool Server로 사용했나

기존 Java 백엔드에는 이미 데이터 접근 계층, 인증 규칙, 운영 지표, 로그 정책이 있다. 이 기능을 Python 에이전트 서비스에 다시 구현하면 보안 규칙이 중복되고 시스템의 실제 권한 경계가 흐려진다.

따라서 역할을 다음처럼 나눴다.

- Spring Boot: 실제 백엔드 도구와 권한을 소유한다.
- Python agent service: 모델 호출과 도구 선택 루프를 소유한다.
- React dashboard: Python이 저장한 trace를 읽고 설명한다.

Spring은 “모델이 판단하는 곳”이 아니라 “판단 결과를 안전하게 실행하거나 거부하는 곳”이다.

## 가장 작은 호출 예제

```bash
curl -X POST http://localhost:8080/internal/tools/health \
  -H 'Content-Type: application/json' \
  -H "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  -H 'X-Trace-Id: trace-demo-001' \
  -H 'X-Request-Id: request-demo-001' \
  -d '{"includeJvm":true,"includeDbPool":true}'
```

응답은 모델이 해석하기 쉬운 제한된 JSON이어야 한다. 환경 변수 전체나 raw Actuator 구조를 그대로 노출하지 않는다.

## 인증과 감사 로그

`/internal/tools/**` 요청은 공유 토큰을 요구한다. 이것은 완전한 서비스 간 인증의 최종 형태가 아니라 로컬 MVP의 최소 경계다. 중요한 점은 모델이 토큰을 생성하거나 선택하지 않는다는 것이다. Python 서비스가 서버 설정에서 토큰을 읽어 내부 헤더로 전달한다.

각 실행은 `traceId`, `requestId`, 도구 이름, 상태, 지연 시간, 거부 또는 실패 코드를 기록한다. 여기서 상태 구분은 중요하다.

- `success`: 도구가 정상 실행됨
- `rejected`: 인증, 입력 검증, SQL 정책 등 의도적인 정책 거부
- `failed`: DB 장애와 같은 실행 실패

초기 구현에서는 모든 `ToolException`을 `rejected`로 기록했다. 존재하지 않는 테이블을 조회해 `502`가 발생해도 정책 거부처럼 보였다. 회귀 테스트로 이 문제를 재현한 뒤 `4xx`는 `rejected`, 서버 오류는 `failed`로 분리했다.

## 실패 사례

내부 토큰 없이 요청하면 다음과 같은 구조화된 오류를 반환해야 한다.

```json
{
  "code": "UNAUTHORIZED_TOOL_REQUEST",
  "message": "Missing or invalid internal tool token."
}
```

오류 응답에도 trace 식별자를 제공하면 CLI와 dashboard가 실패를 같은 실행 흐름으로 연결할 수 있다.

## 현재 한계

- 공유 토큰은 로컬 MVP 경계이며 운영 환경에서는 서비스 identity 또는 mTLS 같은 강한 인증이 필요하다.
- health 도구의 DB 상태는 설정 여부와 실제 연결 가능성을 구분해야 한다.
- trace 전체는 Spring이 아니라 Python agent service가 소유해야 한다.

## 검증

```bash
./gradlew :spring-tool-server:test
```

관련 코드는 `spring-tool-server/src/main/java/dev/stacksleuth/toolserver`에서 확인할 수 있다.

## 관련 자료

- [Issue #1: Scaffold Spring Boot tool server](https://github.com/yhkdsl/stack-sleuth/issues/1)
- [PR #8: feat: scaffold Spring Boot tool server](https://github.com/yhkdsl/stack-sleuth/pull/8)
- [PR #9: execution failure audit classification follow-up](https://github.com/yhkdsl/stack-sleuth/pull/9)
- [Architecture document](../ARCHITECTURE.md)
- [Beginner tutorial](../TUTORIAL.md)
