CREATE TABLE IF NOT EXISTS tb_player(
    user_id       SERIAL PRIMARY KEY,
    email         VARCHAR(128) UNIQUE NOT NULL,
    password      VARCHAR(128) NOT NULL,
    display_name  VARCHAR(128),
    profile_photo bytea,
    likes         INT DEFAULT 0,
    bio           VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS tb_game(
    game_id        SERIAL PRIMARY KEY,
    title          VARCHAR(128) UNIQUE NOT NULL,
    ign_descriptor VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_game_role(
    game_role_id SERIAL PRIMARY KEY,
    game_id      INTEGER NOT NULL REFERENCES tb_game(game_id) NOT NULL,
    role         VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS tb_player_game(
    player_game_id  SERIAL PRIMARY KEY,
    game_id       INTEGER NOT NULL REFERENCES tb_game(game_id) NOT NULL,
    user_id       INTEGER NOT NULL REFERENCES tb_player(user_id) NOT NULL,
    display_name  VARCHAR(128) NOT NULL,
    role          VARCHAR(128) NOT NULL,
    partner_role  VARCHAR(128) NOT NULL
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

CREATE TABLE IF NOT EXISTS tb_player_skill (
    skill_id       SERIAL PRIMARY KEY,
    player_game_id INTEGER NOT NULL REFERENCES tb_player_game(player_game_id) NOT NULL,
    user_id        INTEGER NOT NULL REFERENCES tb_player(user_id) NOT NULL,
    role           VARCHAR(128) NOT NULL,
    role_wins      INTEGER NOT NULL,
    role_losses    INTEGER NOT NULL,
    wins           INTEGER NOT NULL,
    losses         INTEGER NOT NULL,
    role_pick      VARCHAR(128) NOT NULL,
    tier           VARCHAR(128) NOT NULL,
    rank           VARCHAR(128) NOT NULL
);

/* Uncomment if the database is being created from scratch.

INSERT INTO tb_game (title, ign_descriptor) VALUES('League of Legends', 'Summoner Name');

INSERT INTO tb_game_role (game_id, role) VALUES('1', 'Bottom');
INSERT INTO tb_game_role (game_id, role) VALUES('1', 'Middle');
INSERT INTO tb_game_role (game_id, role) VALUES('1', 'Top');
INSERT INTO tb_game_role (game_id, role) VALUES('1', 'Jungle');
INSERT INTO tb_game_role (game_id, role) VALUES('1', 'Support');

INSERT INTO tb_game (title, ign_descriptor) VALUES('Overwatch', 'Battle.NET ID');
*/
INSERT INTO tb_game_role (game_id, role) VALUES('2', 'DPS');
INSERT INTO tb_game_role (game_id, role) VALUES('2', 'Support');
INSERT INTO tb_game_role (game_id, role) VALUES('2', 'Tank');

INSERT INTO tb_game (title, ign_descriptor) VALUES('World of Warcraft', 'Battle.NET ID');

INSERT INTO tb_game_role (game_id, role) VALUES('3', 'Tank');
INSERT INTO tb_game_role (game_id, role) VALUES('3', 'Healer');
INSERT INTO tb_game_role (game_id, role) VALUES('3', 'DPS');

