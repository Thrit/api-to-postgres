# api-to-postgres
Project to extract data from coinmarket's API and send it to a RDS PostgreSQL.

### Resources
* Open source API from https://coinmarketcap.com/api/documentation/v1/
* AWS RDS

### Pipeline.conf
It's necessary to create a file called pipeline.conf inside modules folder.
This way you can load necessary values to connect with the instances in this project.

    .
    ├── modules
        ├── pipeline.conf

The content should have something similar as below:
> **pipeleine.conf**
> 
> [aws_boto_credentials]\
access_key = <key_value>'\
secret_key = <key_value>
> 
> [aws_boto_rds_postgres_config]\
db_name = <key_value>'\
db_instance_identifier = <key_value>'\
master_username = <key_value>'\
master_password = <key_value>'\
db_instance_class = <key_value>'\
db_engine = <key_value>'\
storage = <key_value>'\
vpc_security_group_id = <key_value>'