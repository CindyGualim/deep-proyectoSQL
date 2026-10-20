#!/usr/bin/env bash
# Levanta MySQL 8.4.10 con la configuracion por defecto (incluye ONLY_FULL_GROUP_BY)
# y crea el usuario de solo lectura que usan los scripts de validacion.
#
#   bash scripts/mysql_setup.sh docker   # local, imagen mysql:8.4.10
#   bash scripts/mysql_setup.sh colab    # Colab o Kaggle, binario oficial
#
# Variables exportadas por los scripts de Python: MYSQL_HOST, MYSQL_PORT,
# MYSQL_USER, MYSQL_PASSWORD.
set -euo pipefail

MODO="${1:-docker}"
PASS="${MYSQL_PASSWORD:-proyecto3}"
PUERTO="${MYSQL_PORT:-3306}"

# En ambos modos se crea el usuario 'lector', sin permisos de escritura, para
# replicar la condicion con la que el evaluador ejecuta las consultas.
case "$MODO" in
  docker)
    docker rm -f mysql8410 >/dev/null 2>&1 || true
    docker run -d --name mysql8410 \
      -e MYSQL_ROOT_PASSWORD="$PASS" \
      -p "$PUERTO":3306 \
      mysql:8.4.10

    echo "Esperando a que MySQL acepte conexiones..."
    for _ in $(seq 1 60); do
      if docker exec mysql8410 mysqladmin ping -u root -p"$PASS" --silent >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done

    docker exec -i mysql8410 mysql -u root -p"$PASS" <<'SQL'
CREATE USER IF NOT EXISTS 'lector'@'%' IDENTIFIED BY 'lector';
GRANT SELECT, SHOW VIEW ON *.* TO 'lector'@'%';
FLUSH PRIVILEGES;
SQL
    echo "MySQL 8.4.10 listo en 127.0.0.1:$PUERTO (root / $PASS)"
    ;;

  colab)
    URL=https://downloads.mysql.com/archives/get/p/23/file/mysql-8.4.10-linux-glibc2.17-x86_64-minimal.tar.xz
    DEST=/opt/mysql
    if [ ! -d "$DEST" ]; then
      mkdir -p "$DEST"
      wget -q -O /tmp/mysql.tar.xz "$URL"
      tar -xf /tmp/mysql.tar.xz -C "$DEST" --strip-components=1
    fi
    export PATH="$DEST/bin:$PATH"

    rm -rf /var/lib/mysql-p3 && mkdir -p /var/lib/mysql-p3
    mysqld --initialize-insecure --user=root --datadir=/var/lib/mysql-p3
    mysqld --user=root --datadir=/var/lib/mysql-p3 \
           --socket=/tmp/mysql.sock --port="$PUERTO" \
           --mysqlx=0 --daemonize

    for _ in $(seq 1 60); do
      if mysqladmin ping -h 127.0.0.1 -P "$PUERTO" -u root --silent >/dev/null 2>&1; then
        break
      fi
      sleep 2
    done

    mysql -h 127.0.0.1 -P "$PUERTO" -u root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED BY '$PASS';
CREATE USER IF NOT EXISTS 'lector'@'%' IDENTIFIED BY 'lector';
GRANT SELECT, SHOW VIEW ON *.* TO 'lector'@'%';
FLUSH PRIVILEGES;
SQL
    echo "MySQL 8.4.10 listo en 127.0.0.1:$PUERTO (root / $PASS)"
    ;;

  *)
    echo "Modo no reconocido: $MODO (use docker o colab)" >&2
    exit 1
    ;;
esac

cat <<EOF

Exporte estas variables antes de correr los scripts de Python:

  export MYSQL_HOST=127.0.0.1
  export MYSQL_PORT=$PUERTO
  export MYSQL_USER=root
  export MYSQL_PASSWORD=$PASS

Luego:

  python scripts/cargar_esquemas.py --dir datos/esquemas --poblar
EOF
