import os
import subprocess
import psycopg2


if __name__ == "__main__":
    db_name = os.environ.get('DB_NAME', None)
    db_user = os.environ.get('DB_USER', None)
    db_password = os.environ.get('DB_PASSWORD', None)
    db_host = os.environ.get('DB_HOST', None)

    assert (db_name is not None)
    assert (db_user is not None)
    assert (db_password is not None)
    assert (db_host is not None)

    connection = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        password=db_password,
        host=db_host
    )

    cur = connection.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS public.deployed_migrations ("
        "   migration_name TEXT PRIMARY KEY,"
        "   deployed TIMESTAMP DEFAULT (now() AT TIME ZONE 'utc')"
        ");"
    )
    connection.commit()

    deployed_migrations = set()
    cur = connection.cursor()
    cur.execute("SELECT migration_name FROM public.deployed_migrations;")
    for entry in cur:
        deployed_migrations.add(entry[0])

    migrations = os.listdir("./migrations/")
    migrations.sort()
    print(f"Migrations files: {migrations}")
    for migration_file_name in migrations:
        ext_sql = migration_file_name[-4:]
        ext_py = migration_file_name[-3:]
        if migration_file_name in deployed_migrations:
            print(f"Skipping migration {migration_file_name}")
            continue

        if ext_sql == ".sql":
            print(f"Deploying SQL migration {migration_file_name}...")
            result = subprocess.run(
                ["psql", "-h", db_host, db_name, db_user, "-a", "-f", os.path.join("./migrations", migration_file_name)]
            )
        elif ext_py == ".py":
            print(f"Deploying Python migration {migration_file_name}...")
            result = subprocess.run(
                ["python3", os.path.join("./migrations", migration_file_name)]
            )
        else:
            print(f"Wrong file in migrations directory: {migration_file_name}")
            exit(1)

        if result.returncode == 0:
            print("Deployed successfully.")
            try:
                cur = connection.cursor()
                cur.execute(
                    "INSERT INTO public.deployed_migrations(migration_name) VALUES(%s);",
                    (migration_file_name,)
                )
                connection.commit()
                deployed_migrations.add(migration_file_name)
            except Exception as e:
                print(f"Failed to add migration {migration_file_name}: {e}")
        else:
            print(f"Migration {migration_file_name} not deployed")
            exit(1)

