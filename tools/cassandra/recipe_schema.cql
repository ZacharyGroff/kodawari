CREATE TABLE kodawari.recipe (id bigint PRIMARY KEY, author_id bigint, name text, description text);
CREATE TABLE kodawari.variation (id bigint PRIMARY KEY, author_id bigint, recipe_id bigint, name text, ingredients list<text>, process text, notes text);
