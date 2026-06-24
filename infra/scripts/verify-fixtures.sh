#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
log_file="${repo_root}/infra/sample-logs/app.log"
seed_file="${repo_root}/infra/postgres/init/002-seed.sql"

for request_id in req-demo-4201 req-demo-4202 req-demo-4203; do
  if [[ "$(grep --fixed-strings --count "${request_id}" "${seed_file}")" != "1" ]]; then
    printf 'FAIL: fixture request ID %s must appear exactly once in the seed data\n' "${request_id}" >&2
    exit 1
  fi

  if [[ "$(grep --fixed-strings --count "${request_id}" "${log_file}")" != "1" ]]; then
    printf 'FAIL: fixture request ID %s must appear exactly once in the sample log\n' "${request_id}" >&2
    exit 1
  fi
done

sensitive_pattern='([[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,})|(bearer[[:space:]]+[[:alnum:]_.-]+)|(sk-[[:alnum:]_-]{16,})|(\+82[- ]?1[016789][- ]?[0-9]{3,4}[- ]?[0-9]{4})|(01[016789][- ][0-9]{3,4}[- ][0-9]{4})|(\+1[- ]?[2-9][0-9]{2}[- ][0-9]{3}[- ][0-9]{4})|(BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY)'

if grep --extended-regexp --line-number --ignore-case "${sensitive_pattern}" "${log_file}" "${seed_file}"; then
  printf 'FAIL: sample fixtures contain an email, token, phone number, or private key pattern\n' >&2
  exit 1
fi

printf 'Sample fixture correlation and sensitive-data scan passed.\n'
