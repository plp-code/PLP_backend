create table purchases (
    id int auto_increment primary key,
    user_id int not null,
    map_id int not null,
    transaction_id int not null,
    purchased_at timestamp default current_timestamp,
    unique (user_id, map_id),
    foreign key (user_id) references users(id) on delete cascade,
    foreign key (map_id) references maps(id) on delete cascade,
    foreign key (transaction_id) references transactions(id),
    index idx_purchase_user_id (user_id)
);
