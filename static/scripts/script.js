const separator = "{tag}"


// Error messages
const notifications = document.querySelector(".flashes");
if (notifications) {
    notifications.addEventListener("click", (e) => {
        notifications.remove();
    });
}


// Add bookmark button
const add_button = document.querySelector(".add");
const bookmark_modal = document.querySelector("#bookmark-modal");
const delete_modal = document.querySelector("#delete-modal")
add_button.addEventListener("click", (e) => {
    show_modal("add");
});

// Modal setting
const show_modal = (action, id="") => {
    const form = bookmark_modal.querySelector("form");
    const delete_form = delete_modal.querySelector("form");
    
    if (action === "add") {
        form.setAttribute("action", "/new");
        bookmark_modal.querySelector(".confirm-btn").textContent = "Add";
        bookmark_modal.showModal();
    }
    else if (action === "edit") {
        form.reset();
        form.querySelector("textarea").textContent = "";
        form.querySelector(".tags-display").innerHTML = "";
        form.querySelector(".tags-db").value = "";
        form.setAttribute("action", `/edit/${id}`);
        bookmark_modal.querySelector(".confirm-btn").textContent = "Edit";
        bookmark_modal.showModal();
    }
    else if (action === "delete") {
        delete_form.setAttribute("action", `/delete/${id}`);
        delete_modal.showModal();
    }
}

// Bookmark modal
const close_button = bookmark_modal.querySelector(".close-btn");
close_button.addEventListener("click", (e) => {
    e.preventDefault();
    bookmark_modal.close();
});
// Delete modal
const delete_close_button = delete_modal.querySelector(".close-btn");
delete_close_button.addEventListener("click", (e) => {
    e.preventDefault();
    delete_modal.close();
});
// Adding tags in bookmark modal
const handle_add_tag = (e) => {
    const tag_list = get_current_tags();
    const value = tag_input.value.replace(separator, "").trim();
    if (value !== "" && !tag_list.includes(value)) {
        // Add tag to DB send list
        const tags_db = bookmark_modal.querySelector(".tags-db");
        tags_db.value += `${separator}${value}`;
        
        // Add tag to display list
        const tags_display = bookmark_modal.querySelector(".tags-display");
        const new_tag = document.createElement("li");
        new_tag.classList.add("tag");
        new_tag.textContent = value;
        tags_display.appendChild(new_tag);
    }
    tag_input.value = "";

};
const get_current_tags = () => {
    return Array.from(
        bookmark_modal.querySelector(".tags-display").querySelectorAll("li")
    ).map(tag => tag.textContent);
}
// Removing tags in bookmark modal
const tags_display = bookmark_modal.querySelector(".tags-display");
tags_display.addEventListener("click", (e) => {
    if (e.target.classList.contains("tag")) {
        const tags_db = bookmark_modal.querySelector(".tags-db");
        const value = e.target.textContent;
        
        tags_db.value = tags_db.value.replace(`${separator}${value}`, "")
        e.target.remove();
    }
});

const tag_input = bookmark_modal.querySelector(".tag-input");
const add_tag_button = bookmark_modal.querySelector(".add-tag")
tag_input.addEventListener("keypress", (e) => {
    if (e.key === "Enter"){
        e.preventDefault();
        handle_add_tag(e);
    }
});
add_tag_button.addEventListener("click", (e) => {
    e.preventDefault();
    handle_add_tag(e);
});

// Bookmark action buttons
const bookmarks = document.querySelector(".bookmarks");
bookmarks.addEventListener("click", (e) => {
    // Edit button
    if (e.target.classList.contains("edit")) {

        const id = e.target.value;
        show_modal("edit", id);

        // Populate modal with respective bookmark data
        const bookmark = Array.from(
            bookmarks.querySelectorAll("[data-bookmark-id]")
        ).filter(bookmark => bookmark.dataset.bookmarkId == id)[0];

        const url = bookmark.querySelector(".url").textContent.trim();
        let notes = bookmark.querySelector(".notes");
        let tags = Array.from(
            bookmark
            .querySelector(".tag-list")
            .querySelectorAll("li")
        )
        if (tags.length > 0) {
            tags = tags.map(tag => tag.textContent)
            bookmark_modal.querySelector(".tags-db").value = 
                separator + tags.join(separator);
        }

        bookmark_modal.querySelector(".url").value = url;
        if (notes) {
            bookmark_modal.querySelector("textarea").textContent = 
                notes.textContent.trim();
        }
        tags.forEach((tag) => {
            const new_tag = document.createElement("li");
            new_tag.classList.add("tag");
            new_tag.textContent = tag;
            bookmark_modal.querySelector(".tags-display").append(new_tag);
        });
    }

    // Delete button
    if (e.target.classList.contains("delete")) {
        const id = e.target.value;
        show_modal("delete", id);
    }
});

// Search bar for filter
const filter_search = document.querySelector("#filter-search");
const filter_input = filter_search.querySelector("input")
filter_input.addEventListener("input", (e) => {
    const keyword = filter_search.keyword.value;
    filter_search.setAttribute("action", "/filter="+keyword);
});