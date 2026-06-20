create table transactions (
      id int auto_increment primary key,
      user_id int not null,
      map_id int not null,
      stripe_payment_intent_id varchar(255) not null unique,
      amount int not null,
      transaction_status int not null,
      created_at timestamp default current_timestamp,
      updated_at timestamp default current_timestamp on update current_timestamp,
      foreign key (user_id) references users(id) on delete cascade,
      foreign key (map_id) references maps(id) on delete cascade,
      foreign key (transaction_status) references transaction_status(id) on delete cascade,
      index idx_transaction_user_id (user_id),
      index idx_transaction_stripe_id (stripe_payment_intent_id)
  );
