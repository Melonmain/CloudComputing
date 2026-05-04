#!/bin/bash

# PostgreSQL configuration
DB_NAME="${DB_NAME:-appdb}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

INSTALL_userdata=0
INSTALL_login=0

# Install PostgreSQL server and client
install_postgres() {
    if command -v psql &> /dev/null; then
        echo "PostgreSQL is already installed."
        # Try to start if not running
        service postgresql start 2>/dev/null || systemctl start postgresql 2>/dev/null || true
        return 0
    fi

    echo "Installing PostgreSQL server..."

    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y postgresql postgresql-client

    # Start PostgreSQL service
    service postgresql start || systemctl start postgresql || true

    # Wait for PostgreSQL to be ready
    for i in {1..30}; do
        if pg_isready -q 2>/dev/null; then
            break
        fi
        sleep 1
    done

    echo "PostgreSQL installed and started successfully."

    # Allow remote connections (PostgreSQL only listens on localhost by default)
    PG_CONF=$(find /etc/postgresql -name postgresql.conf | head -1)
    PG_HBA=$(find /etc/postgresql -name pg_hba.conf | head -1)

    sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$PG_CONF"
    echo "host all all 0.0.0.0/0 md5" >> "$PG_HBA"

    systemctl restart postgresql

    # Wait again after restart
    for i in {1..30}; do
        if pg_isready -q 2>/dev/null; then
            break
        fi
        sleep 1
    done
    echo "PostgreSQL configured for remote access."
}

while getopts i: FLAG; do
    case $FLAG in
        i)
            case $OPTARG in
                login)
                    INSTALL_login=1
                ;;
                user)
                    INSTALL_userdata=1
                ;;
            esac
        ;;
    esac
done

# Install PostgreSQL server if needed
install_postgres

# Create database and user if they don't exist
setup_postgres() {
    # Wait for PostgreSQL to be ready
    for i in {1..30}; do
        if pg_isready -q 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Create database using peer authentication (run as postgres user)
    su - postgres -c "psql -c \"CREATE DATABASE $DB_NAME;\"" 2>/dev/null || echo "Database $DB_NAME already exists."

    # Create user with password
    su - postgres -c "psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"" 2>/dev/null || echo "User $DB_USER already exists."

    # Grant privileges
    su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\""
    su - postgres -c "psql -d $DB_NAME -c \"GRANT ALL ON SCHEMA public TO $DB_USER;\""
}

setup_postgres

export PGPASSWORD="$DB_PASSWORD"

# Create users table
create_users_table() {
    su - postgres -c "psql -d $DB_NAME -c \"
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            username TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    \""
}

# Create todos table
create_todos_table() {
    su - postgres -c "psql -d $DB_NAME -c \"
        CREATE TABLE IF NOT EXISTS todos (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    \""
}

if [[ $INSTALL_login -eq 1 ]]; then
    echo "Creating users table..."
    create_users_table
    echo "login table created successfully."
fi

if [[ $INSTALL_userdata -eq 1 ]]; then
    echo "Creating todos table..."
    create_todos_table
    echo "userdata table created successfully."
fi

echo "Database initialization complete."