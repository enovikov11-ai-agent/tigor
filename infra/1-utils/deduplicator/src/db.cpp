#include <sqlite3.h>
#include <string>
#include <stdexcept>
#include <exception>

void init_db(std::string &db_path)
{
    sqlite3 *db;
    int rc = sqlite3_open(db_path.c_str(), &db);
    char *errorMessage = nullptr;
    std::string sqliteError;

    if (rc != SQLITE_OK)
        throw std::runtime_error("Can't open db");

    std::string init_db = "CREATE TABLE IF NOT EXISTS Files (hostname text, path text, sha256 text, size integer, last_modified integer)";

    rc = sqlite3_exec(db, init_db.c_str(), nullptr, 0, &errorMessage);
    if (rc != SQLITE_OK)
    {
        sqliteError = errorMessage;
        sqlite3_free(errorMessage);
        sqlite3_close(db);
        throw std::runtime_error(sqliteError);
    }
}