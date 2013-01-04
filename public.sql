BEGIN;

CREATE TYPE part_type AS ENUM ('am', 'pm');

CREATE TABLE slot (
  slot_id serial PRIMARY KEY NOT NULL,
  person varchar NOT NULL,
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
