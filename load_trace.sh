sqlite3 $2 << EOF
drop table trace;
create table trace(
    cycle int primary key not null,
    inst int not null,
    pc int not null,
    rs int,
    rd int
);
.separator ' '
.import $1 trace
