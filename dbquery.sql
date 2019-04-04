USE python;

CREATE TABLE IF NOT EXISTS users(
	u_id INT NOT NULL PRIMARY KEY auto_increment,
    kuerzel VARCHAR(255) NOT NULL,
    vorname VARCHAR(255) NOT NULL,
    nachname VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS positions(
	p_id INT NOT NULL PRIMARY KEY auto_increment,
    p_uid INT NOT NULL,
    p_x FLOAT NOT NULL,
    p_y FLOAT NOT NULL,
    p_date date NOT NULL,
    p_time time NOT NULL,
    FOREIGN KEY(p_uid) REFERENCES users(u_id)
);

CREATE TABLE IF NOT EXISTS sites(
	s_id INT NOT NULL PRIMARY KEY auto_increment,
    s_name VARCHAR(255) NOT NULL,
    s_address VARCHAR(255) NOT NULL,
    s_x FLOAT NOT NULL,
    s_y FLOAT NOT NULL,
    s_description VARCHAR(2000) DEFAULT "No description"
);

#INSERT INTO positions (user_id, x, y, p_date, p_time) VALUES (1,  