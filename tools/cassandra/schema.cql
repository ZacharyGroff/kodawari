CREATE KEYSPACE IF NOT EXISTS kodawari WITH replication = {'class':'SimpleStrategy', 'replication_factor' : 1};
CREATE TABLE kodawari.user (id INT PRIMARY KEY, display_name text, description text, joined bigint);
