create table maps (
    id int auto_increment primary key,
    name varchar(255) not null unique,
    slug varchar(255) not null unique,
    region varchar(255),
    price int not null,
    is_active bool default true,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp on update current_timestamp
);
