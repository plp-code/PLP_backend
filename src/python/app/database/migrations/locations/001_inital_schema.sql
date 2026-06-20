create table locations (
    id int auto_increment primary key,
    name varchar(255) not null,
    map_id int not null,
    latitude int not null,
    longitude int not null,
    min_price int,
    max_price int,
    open_time time,
    close_time time,
    price_level int check (price_level in (1, 2, 3)),
    foreign key (price_level) references price_level(id) on delete cascade,
    foreign key (map_id) references maps(id) on delete cascade,
    index idx_map_id (map_id)
);
