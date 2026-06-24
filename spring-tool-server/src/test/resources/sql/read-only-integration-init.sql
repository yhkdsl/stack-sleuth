CREATE TABLE users (
    id bigint PRIMARY KEY,
    account_status text NOT NULL,
    profile_img text
);

INSERT INTO users (id, account_status, profile_img)
VALUES (42, 'active', NULL);

CREATE ROLE stacksleuth_test_reader
    LOGIN
    PASSWORD 'test-reader-password'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS;

ALTER ROLE stacksleuth_test_reader SET default_transaction_read_only = on;
GRANT CONNECT ON DATABASE test TO stacksleuth_test_reader;
GRANT USAGE ON SCHEMA public TO stacksleuth_test_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO stacksleuth_test_reader;
