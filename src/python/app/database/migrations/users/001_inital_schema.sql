create table users (
    id int auto_increment primary key,
    email varchar(255) not null unique,
    first_name varchar(255) not null,
    last_name varchar(255) not null,
    hashed_password varchar(255) not null,
    is_active bool default true,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp on update current_timestamp,
    index idx_user_email (email)
);
