# Django Starter

## Deployment

### Server Setup

https://djangocentral.com/using-postgresql-with-django/

`sudo apt install postgresql postgresql-contrib`

`sudo apt install libpq-dev python3-dev`

`sudo apt install postgresql-server-dev-13` (for psycopg2)`

### Database (PostgreSQL)

`sudo -iu postgres`

`psql`

`ALTER USER postgres WITH ENCRYPTED PASSWORD '<password>';`

`CREATE DATABASE <database>;`

`CREATE USER <user> WITH ENCRYPTED PASSWORD '<password>';`

`ALTER USER <user> SET client_encoding TO 'utf8';`
`ALTER USER <user> SET default_transaction_isolation TO 'read committed';`
`ALTER USER <user> SET timezone TO 'Europe/Berlin';`

`GRANT ALL PRIVILEGES ON DATABASE <database> TO <user>;`

### mod_wsgi

https://tecadmin.net/install-apache-mod-wsgi-on-ubuntu-18-04-bionic/

`sudo apt install apache2 apache2-utils ssl-cert`

`sudo apt install libapache2-mod-wsgi-py3`

`sudo systemctl restart apache2`


### Checklist

https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/
