CREATE TABLE users (
    id bigint PRIMARY KEY,
    username text NOT NULL UNIQUE,
    account_status text NOT NULL CHECK (account_status IN ('active', 'disabled', 'locked')),
    profile_img text,
    created_at timestamptz NOT NULL
);

CREATE TABLE orders (
    id bigint PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id),
    status text NOT NULL CHECK (status IN ('pending', 'paid', 'cancelled', 'refunded')),
    total_cents integer NOT NULL CHECK (total_cents >= 0),
    created_at timestamptz NOT NULL
);

CREATE TABLE login_events (
    id bigint PRIMARY KEY,
    user_id bigint NOT NULL REFERENCES users(id),
    outcome text NOT NULL CHECK (outcome IN ('success', 'failure')),
    source_ip inet NOT NULL,
    occurred_at timestamptz NOT NULL
);

CREATE TABLE error_events (
    id bigint PRIMARY KEY,
    request_id text NOT NULL UNIQUE,
    user_id bigint REFERENCES users(id),
    service_name text NOT NULL,
    error_type text NOT NULL,
    message text NOT NULL,
    occurred_at timestamptz NOT NULL
);

CREATE INDEX orders_user_id_idx ON orders (user_id);
CREATE INDEX login_events_user_id_occurred_at_idx ON login_events (user_id, occurred_at DESC);
CREATE INDEX error_events_user_id_occurred_at_idx ON error_events (user_id, occurred_at DESC);
