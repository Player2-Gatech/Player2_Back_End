CREATE TABLE IF NOT EXISTS tb_player(
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR(128) UNIQUE NOT NULL,
    password      VARCHAR(128) NOT NULL,
    display_name  VARCHAR(128),
    likes         INT DEFAULT 0,
    bio           VARCHAR(255),
    is_searching  boolean DEFAULT 't'
);

CREATE TABLE IF NOT EXISTS tb_game(
    game_id       SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES tb_player(user_id) NOT NULL,
    title         VARCHAR(128) NOT NULL,
    console       VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_comment(
    comment_id    SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES tb_player(user_id) NOT NULL,
    commenter     VARCHAR(128) NOT NULL,
    message       VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_clip(
    clip_id       SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES tb_player(user_id) NOT NULL,
    url           VARCHAR(128) NOT NULL,
    game          VARCHAR(128) NOT NULL
);
