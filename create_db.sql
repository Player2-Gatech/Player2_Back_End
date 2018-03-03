CREATE TABLE IF NOT EXISTS tb_user(
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR(128) UNIQUE NOT NULL,
    password      VARCHAR(MAX) NOT NULL,
    display_name  VARCHAR(128),
    likes         INT NOT NULL DEFAULT 0,
    bio           VARCHAR(MAX),
    is_searching  boolean NOT NULL DEFAULT 't'
);

CREATE TABLE IF NOT EXISTS tb_game(
    game_id       SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES tb_user(user_id) NOT NULL,
    title         VARCHAR(128) NOT NULL,
    console       VARCHAR(129) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_comment(
    comment_id    SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES tb_user(user_id) NOT NULL,
    commenter     VARCHAR(128) NOT NULL,
    message       VARCHAR(MAX) NOT NULL,
);

CREATE TABLE IF NOT EXISTS tb_clip(
    clip_id       SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES tb_user(user_id) NOT NULL,
    url           VARCHAR(128) NOT NULL,
    game          VARCHAR(128) NOT NULL,
);
