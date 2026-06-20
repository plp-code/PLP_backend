create table price_level (
    id int auto_increment primary key,
    type varchar(255) check (type in ('inexpensive', 'moderate', 'expensive'))
)
