CREATE KEYSPACE IF NOT EXISTS kodawari WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};
CREATE TABLE kodawari.user (id bigint PRIMARY KEY, display_name text, description text);
CREATE TABLE kodawari.recipe (id bigint PRIMARY KEY, author_id bigint, name text, description text, views int, subscribers int, vote_diff int);
CREATE TABLE kodawari.variation (id bigint PRIMARY KEY, author_id bigint, recipe_id bigint, name text, ingredients list<text>, process text, notes text, views int, vote_diff int);
