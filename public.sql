BEGIN;

CREATE TYPE part_type AS ENUM ('am', 'pm');

CREATE TABLE person (
  login varchar PRIMARY KEY NOT NULL,
  name varchar NOT NULL
);

CREATE TABLE slot (
  slot_id serial PRIMARY KEY NOT NULL,
  person_login varchar NOT NULL REFERENCES person(login),
  name varchar NOT NULL,
  start date NOT NULL,
  parts int NOT NULL
);

CREATE TABLE vacation (
  vacation_id serial PRIMARY KEY NOT NULL,
  slot_id int NOT NULL REFERENCES slot(slot_id),
  day date NOT NULL,
  part part_type NOT NULL
);

COMMIT;
