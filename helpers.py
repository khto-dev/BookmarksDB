from bs4 import BeautifulSoup
import requests, requests_cache
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed, wait
import sqlite3
import validators


session = requests_cache.CachedSession("preview_cache")

def get_connection():
    """Return the connection to the database."""
    try:
        connection = sqlite3.connect("bookmarks.db")
        connection.row_factory = sqlite3.Row
        return connection
    except sqlite3.Error as error:
        print("Failed to connect to database", error)
        exit()

def initialize_database(connection):
    """Create database tables if not previously initialized."""
    sql_create_bookmarks_table = """
        CREATE TABLE IF NOT EXISTS bookmarks (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            url       TEXT NOT NULL,
            notes     TEXT,
            timestamp DATETIME NOT NULL
        );
    """
    connection.execute(sql_create_bookmarks_table)

    sql_create_tags_table = """
        CREATE TABLE IF NOT EXISTS tags (
            bookmark_id INTEGER NOT NULL,
            tag         TEXT NOT NULL,
            FOREIGN KEY (bookmark_id) REFERENCES bookmarks (id)
        );
    """
    connection.execute(sql_create_tags_table)
    
    connection.close()

def get_tags(bookmarks):
    """Populates each bookmark with assigned tags."""
    connection = get_connection()
    for bookmark in bookmarks:
        tags_query = connection.execute(
            """
            SELECT DISTINCT tag
            FROM tags
            WHERE bookmark_id=?
            ORDER BY tag
            COLLATE NOCASE;
            """,
            [bookmark["id"]]
        ).fetchall()
        tags_list = [dict(tag)["tag"] for tag in tags_query]
        bookmark["tags"] = tags_list
    connection.close

# Metadata scraping code by Anshu Pal:
# https://anshu-dev.medium.com/generating-link-preview-using-beautifulsoup4-and-django-654957ac7ff6
def get_preview(bookmarks):
    """Populates each bookmark with metadata of respective URLs."""
    for bookmark in bookmarks:
        bookmark["meta"] = {
            "title": "", 
            "description": "", 
            "image": ""
        }

        try:
            request = session.get(bookmark["url"])
            if (request.status_code == 200):
                html = BeautifulSoup(request.text, "html.parser")
                bookmark["meta"]["title"] = get_preview_title(html)
                bookmark["meta"]["description"] = get_preview_description(html)
                bookmark["meta"]["image"] = get_preview_image(html)
            else:
                bookmark["meta"]["title"] = "Website Not Found"
        except requests.exceptions.ConnectionError as error:
            bookmark["meta"]["title"] = "Website Not Found"

def get_preview_title(html):
    title = ""
    if html.find("title"):
        title = html.find("title").string
    elif html.find("meta", attrs={"name": "title"}):
        title = html.find("meta", attrs={"name": "title"})["content"]
    elif html.find("meta", property="og:title").get("content"):
        title = html.find("meta", property="og:title").get("content")
    elif html.find("meta", property="twitter:title"):
        title = html.find("meta", property="twitter:title").get("content")
    return title

def get_preview_description(html):
    desc = ""
    if html.find("meta", property="description"):
        desc = html.find("meta", property="description").get("content")
    elif html.find("meta", attrs={"name": "description"}):
        desc = html.find("meta", attrs={"name": "description"})["content"]
    elif html.find("meta", property="og:description"):
        desc = html.find("meta", property="og:description").get("content")
    elif html.find("meta", property="twitter:description"):
        desc = html.find("meta", property="twitter:description").get("content")
    return desc
    
def get_preview_image(html):
    img = ""
    if html.find("meta", property="image"):
        img = html.find("meta", property="image").get("content")
    elif html.find("meta", attrs={"name": "image"}):
        img = html.find("meta", attrs={"name": "image"})["content"]
    elif html.find("meta", property="og:image"):
        img = html.find("meta", property="og:image").get("content")
    elif html.find("meta", property="twitter:image"):
        img = html.find("meta", property="twitter:image").get("content")
    
    if (validators.url(img)):
        return img
    else:
        return ""

def check_duplicate(url):
    connection = get_connection()
    query = connection.execute(
        """
            SELECT *
            FROM bookmarks
            WHERE url=?;
        """,
        [url]
    ).fetchall()
    connection.close()

    return bool(query)

def add_bookmark(url, notes, tags):
    connection = get_connection()
    connection.execute(
        """
            INSERT INTO bookmarks (url, notes, timestamp)
            VALUES (?, ?, (
                SELECT datetime("now")
            ));
        """,
        [url, notes]
    )
    connection.commit()

    id = connection.execute(
        """
            SELECT id 
            FROM bookmarks 
            WHERE url=?;
        """, 
        [url]
    ).fetchone()["id"]

    add_tags(id, tags)

    connection.close()

def add_tags(id, tags):
    connection = get_connection()

    for tag in tags:
        connection.execute(
            """
                INSERT INTO tags (bookmark_id, tag)
                VALUES (?, ?);
            """,
            [id, tag]
        )
    connection.commit()

    connection.close()

def remove_tags(id, tags):
    connection = get_connection()

    for tag in tags:
        connection.execute(
            """
                DELETE FROM tags
                WHERE bookmark_id=?
                  AND tag=?;
            """,
            [id, tag]
        )
    connection.commit()

    connection.close()

def update_bookmark(bookmark):
    connection = get_connection()

    duplicate_bookmarks = connection.execute(
        """
            SELECT *
            FROM bookmarks
            WHERE url=?
              AND NOT id=?;
        """,
        [bookmark["url"], bookmark["id"]]
    ).fetchall()

    if len(duplicate_bookmarks) > 0:
        return False

    connection.execute(
        """
            UPDATE bookmarks
            SET url=?,
                notes=?
            WHERE id=?;
        """,
        [bookmark["url"], bookmark["notes"], bookmark["id"]]
    )
    connection.commit()

    db_tags = [list(tag)[0] for tag in connection.execute(
        """
        SELECT tag
        FROM tags
        WHERE bookmark_id=?;
        """,
        [bookmark["id"]]
    ).fetchall()]
    print(db_tags)

    connection.close()
    
    tags_to_add = list(set(bookmark["tags"]) - set(db_tags))
    tags_to_remove = list(set(db_tags) - set(bookmark["tags"]))

    add_tags(bookmark["id"], tags_to_add)
    remove_tags(bookmark["id"], tags_to_remove)

    return True