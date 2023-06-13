from flask import Flask, flash, redirect, render_template, request, url_for
from helpers import *
import validators

# Application initialization
app = Flask(__name__)
app.secret_key = "tempsecretkey"

# Initial database startup
connection = get_connection()
initialize_database(connection)
connection.close()


# Environmental variables
separator = "{tag}"

# Routing
# Index
@app.route("/", methods=["GET", "POST"])
def index():
    connection = get_connection()
    
    bookmarks_query = connection.execute(
        """
        SELECT *
        FROM bookmarks
        ORDER BY timestamp DESC;
        """
    ).fetchall()
    bookmarks_list = [dict(bookmark) for bookmark in bookmarks_query]

    tags_query = connection.execute(
        """
        SELECT DISTINCT tag
        FROM tags
        """
    ).fetchall()
    tags_list = [list(tag)[0] for tag in tags_query]
    connection.close()

    get_tags(bookmarks_list)
    get_preview(bookmarks_list)

    return render_template(
        "index.html", 
        bookmarks=bookmarks_list,
        tags=tags_list
    )

# Filters
@app.route("/filter=<keyword>", methods=["GET", "POST"])
def filter(keyword):
    connection = get_connection()
    filter_query = connection.execute(
        """
        SELECT *
        FROM bookmarks
        WHERE id IN (
            SELECT DISTINCT bookmark_id
            FROM tags
            WHERE tag=?
        );
        """,
        [keyword]
    ).fetchall()
    bookmarks_list = [dict(bookmark) for bookmark in filter_query]

    tags_query = connection.execute(
        """
        SELECT DISTINCT tag
        FROM tags
        """
    ).fetchall()
    tags_list = [list(tag)[0] for tag in tags_query]
    connection.close()

    get_tags(bookmarks_list)
    get_preview(bookmarks_list)

    return render_template(
        "index.html", 
        bookmarks=bookmarks_list,
        tags=tags_list,
        keyword=keyword
    )

# New Bookmark
@app.route("/new", methods=["POST"])
def new_bookmark():
    error_message = None

    url = request.form.get("url")
    notes = request.form.get("notes")
    tags = []
    if request.form.get("tags-db"):
        tags = request.form.get("tags-db").split(separator)[1:]
        # Normalize styling and removes duplicates
        tags = list(set([tag for tag in tags]))

    # Add bookmark if valid URL and not already in database
    if (validators.url(url) and not check_duplicate(url)):
        add_bookmark(url, notes, tags)
    else:
        error_message = "URL invalid or duplicate"
        flash(error_message)

    return redirect("/")

@app.route("/delete/<id>", methods=["POST"])
def delete_bookmark(id):
    connection = get_connection();
    connection.execute(
        """
            DELETE FROM bookmarks
            WHERE id=?;
        """,
        [id]
    )

    connection.execute(
        """
            DELETE FROM tags
            WHERE bookmark_id=?;
        """,
        [id]
    )
    connection.commit()
    connection.close()

    return redirect("/")

@app.route("/edit/<id>", methods=["POST"])
def edit_bookmark(id):
    bookmark = {}
    bookmark["id"] = id
    bookmark["url"] = request.form.get("url")
    bookmark["notes"] = request.form.get("notes")
    bookmark["tags"] = []
    if request.form.get("tags-db"):
        tags = request.form.get("tags-db").split(separator)[1:]
        # Normalize styling and removes duplicates
        bookmark["tags"] = list(set([tag for tag in tags]))
    
    if (
        not validators.url(bookmark["url"]) or
        not update_bookmark(bookmark)
    ):
        error_message = "URL invalid or duplicate"
        flash(error_message)
    
    return redirect("/")


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True, threaded=True)