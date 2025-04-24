// LoopSleuth: Shared JS for starring and tag editing (grid & detail views)
// All actions use data-clip-id attributes for robust event handling.

/**
 * Debounce utility for limiting function calls.
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

/**
 * Show autocomplete suggestions for the tag input, fetching from backend by prefix.
 */
const showTagSuggestions = debounce(function(input, currentTags) {
    let dropdown = document.getElementById('tag-suggestions-dropdown');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'tag-suggestions-dropdown';
        dropdown.className = 'tag-suggestions-dropdown';
        document.body.appendChild(dropdown);
    }
    const rect = input.getBoundingClientRect();
    dropdown.style.position = 'absolute';
    dropdown.style.left = `${rect.left + window.scrollX}px`;
    dropdown.style.top = `${rect.bottom + window.scrollY}px`;
    dropdown.style.width = `${rect.width}px`;
    dropdown.innerHTML = '';
    const inputVal = input.value.split(',').pop().trim().toLowerCase();
    if (!inputVal) {
        dropdown.style.display = 'none';
        return;
    }
    fetch(`/tags?q=${encodeURIComponent(inputVal)}`)
        .then(r => r.json())
        .then(data => {
            if (!data.tags || data.tags.length === 0) {
                dropdown.style.display = 'none';
                return;
            }
            // Filter out tags already present
            const filtered = data.tags.filter(tag => !currentTags.includes(tag));
            if (filtered.length === 0) {
                dropdown.style.display = 'none';
                return;
            }
            filtered.forEach(tag => {
                const item = document.createElement('div');
                item.className = 'tag-suggestion-item';
                item.textContent = tag;
                item.onclick = () => {
                    addTagToInput(input, tag);
                    dropdown.style.display = 'none';
                };
                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
        });
}, 120);

/**
 * Add a tag to the input field, avoiding duplicates.
 */
function addTagToInput(input, tag) {
    let tags = input.value.split(',').map(t => t.trim());
    // Replace the last (possibly partial) tag with the selected suggestion
    if (tags.length === 0) {
        tags = [tag];
    } else {
        tags[tags.length - 1] = tag;
    }
    // Remove duplicates
    tags = tags.filter((t, i) => t.length > 0 && tags.indexOf(t) === i);
    input.value = tags.join(', ');
    input.dispatchEvent(new Event('input'));
}

/**
 * Remove a tag from the input field.
 */
function removeTagFromInput(input, tag) {
    let tags = input.value.split(',').map(t => t.trim()).filter(t => t.length > 0);
    tags = tags.filter(t => t !== tag);
    input.value = tags.join(', ');
    input.dispatchEvent(new Event('input'));
}

/**
 * Toggle the 'starred' state of a clip via AJAX.
 * Updates the star icon on success.
 */
function toggleStar(event) {
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    fetch(`/star/${clipId}`, {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            if (data.starred !== undefined) {
                event.target.textContent = data.starred ? '★' : '☆';
            }
        });
}

/**
 * Show the tag input for editing, hide static tag text.
 */
function editTags(event) {
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    // Hide static chips, show input and editable chips
    document.getElementById(`tags-text-${clipId}`).style.display = 'none';
    document.getElementById(`tag-input-${clipId}`).style.display = '';
    document.getElementById(`tags-edit-${clipId}`).style.display = '';
    document.getElementById(`save-tag-btn-${clipId}`).style.display = '';
    document.getElementById(`tag-input-${clipId}`).focus();
    renderEditableTagChips(clipId);
    const input = document.getElementById(`tag-input-${clipId}`);
    // Remove any previous listeners to avoid stacking
    input.oninput = null;
    input.onkeyup = null;
    input.addEventListener('input', () => renderEditableTagChips(clipId));
    input.addEventListener('keyup', (e) => {
        if (e.key.length === 1 || e.key === 'Backspace') {
            let tags = input.value.split(',').map(t => t.trim()).filter(t => t.length > 0);
            showTagSuggestions(input, tags);
        } else if (e.key === 'Escape') {
            let dropdown = document.getElementById('tag-suggestions-dropdown');
            if (dropdown) dropdown.style.display = 'none';
        }
    });
}

/**
 * Handle Enter key in tag input to trigger save.
 */
function tagInputKey(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        event.stopPropagation();
        saveTags(event);
    }
}

/**
 * Render tag chips into the tags-text span for a given clip.
 * @param {string} clipId
 * @param {Array<string>} tags
 */
function renderTagChips(clipId, tags) {
    const tagsText = document.getElementById(`tags-text-${clipId}`);
    if (!tagsText) return;
    tagsText.innerHTML = '';
    if (tags.length === 0) {
        tagsText.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
    } else {
        tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip';
            chip.textContent = tag;
            // Add X for deletion
            const x = document.createElement('span');
            x.className = 'tag-chip-x';
            x.textContent = '×';
            x.onclick = () => {
                // Remove tag and update input if in edit mode
                const input = document.getElementById(`tag-input-${clipId}`);
                if (input && input.style.display !== 'none') {
                    removeTagFromInput(input, tag);
                } else {
                    // If not in edit mode, switch to edit mode and remove tag
                    editTags({target: {getAttribute: () => clipId}, stopPropagation: () => {}});
                    setTimeout(() => {
                        const input = document.getElementById(`tag-input-${clipId}`);
                        removeTagFromInput(input, tag);
                    }, 0);
                }
            };
            chip.appendChild(x);
            tagsText.appendChild(chip);
        });
    }
}

/**
 * Save the edited tags via AJAX, update UI on success.
 */
function saveTags(event) {
    event.preventDefault();
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    const input = document.getElementById(`tag-input-${clipId}`);
    // Always send tags as an array
    const tags = input.value.split(',').map(t => t.trim()).filter(t => t.length > 0);
    fetch(`/tag/${clipId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tags: tags})
    })
    .then(r => r.json())
    .then(data => {
        if (data.tags !== undefined) {
            renderTagChips(clipId, data.tags);
        } else if (data.error) {
            alert('Error saving tags: ' + data.error);
        }
        // Hide edit mode, show static chips
        document.getElementById(`tags-text-${clipId}`).style.display = '';
        input.style.display = 'none';
        document.getElementById(`tags-edit-${clipId}`).style.display = 'none';
        document.getElementById(`save-tag-btn-${clipId}`).style.display = 'none';
    })
    .catch(err => {
        alert('Error saving tags: ' + err);
    });
}

/**
 * Render editable tag chips with X for removal.
 */
function renderEditableTagChips(clipId) {
    const input = document.getElementById(`tag-input-${clipId}`);
    const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
    let tags = input.value.split(',').map(t => t.trim()).filter(t => t.length > 0);
    tagsEdit.innerHTML = '';
    if (tags.length === 0) {
        tagsEdit.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
    } else {
        tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip tag-edit';
            chip.textContent = tag;
            const x = document.createElement('span');
            x.className = 'tag-chip-x';
            x.textContent = '×';
            x.onclick = () => removeTagFromInput(input, tag);
            chip.appendChild(x);
            tagsEdit.appendChild(chip);
        });
    }
} 