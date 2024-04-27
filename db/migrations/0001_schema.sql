CREATE TABLE IF NOT EXISTS language (
    code VARCHAR(2) PRIMARY KEY
);

INSERT INTO public.language (code)
VALUES ('ar'), ('az'), ('bg'), ('bn'), ('ca'), ('cs'), ('da'), ('de'), ('el'),
       ('en'), ('eo'), ('es'), ('et'), ('fa'), ('fi'), ('fr'), ('ga'), ('he'),
       ('hi'), ('hu'), ('id'), ('it'), ('ja'), ('ko'), ('lt'), ('lv'), ('ms'),
       ('nb'), ('nl'), ('pl'), ('pt'), ('ro'), ('ru'), ('sk'), ('sl'), ('sq'),
       ('sv'), ('th'), ('tl'), ('tr'), ('uk'), ('ur'), ('zh'), ('zt');

CREATE TABLE IF NOT EXISTS botuser (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    language VARCHAR(2),

    FOREIGN KEY (language) REFERENCES language(code)
);

CREATE TABLE IF NOT EXISTS external_user (
    platform TEXT,
    platform_user_id TEXT,
    user_id UUID DEFAULT NULL,
    additional_info json DEFAULT NULL,

    PRIMARY KEY (platform, platform_user_id),
    FOREIGN KEY (user_id) REFERENCES botuser(user_id)
);

CREATE TABLE IF NOT EXISTS words (
    word TEXT,
    language VARCHAR(2),
    category TEXT,

    PRIMARY KEY (word, language),
    FOREIGN KEY (language) REFERENCES language(code)
);

CREATE TABLE IF NOT EXISTS vocabulary (
    word TEXT,
    language VARCHAR(2),
    user_id UUID,
    learning_score INT,
    last_check TIMESTAMP DEFAULT (now() at time zone 'utc'),

    PRIMARY KEY (user_id, language, word),
    FOREIGN KEY (user_id) REFERENCES botuser(user_id),
    FOREIGN KEY (word, language) REFERENCES words(word, language)
);

CREATE INDEX vocabulary_learning_score_last_check ON vocabulary(learning_score, last_check);
