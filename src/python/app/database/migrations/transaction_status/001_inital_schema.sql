create table transaction_status (
    id int auto_increment primary key,
    type varchar(255) check (type in ('pending', 'succeeded', 'failed'))
);
