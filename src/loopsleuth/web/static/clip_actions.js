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

// --- Standard Tag Input State ---
// Store tag arrays for each clip in edit mode
const editTagsState = {};

function editTags(event) {
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    // Get initial tags from static chips
    const staticChips = document.querySelectorAll(`#tags-text-${clipId} .tag-chip:not(.tag-empty)`);
    editTagsState[clipId] = Array.from(staticChips).map(chip => chip.textContent.trim());
    // Hide static chips, show edit mode
    document.getElementById(`tags-text-${clipId}`).style.display = 'none';
    document.getElementById(`tags-edit-${clipId}`).style.display = '';
    document.getElementById(`tag-input-new-${clipId}`).style.display = '';
    document.getElementById(`save-tag-btn-${clipId}`).style.display = '';
    renderEditableTagChips(clipId);
    const input = document.getElementById(`tag-input-new-${clipId}`);
    input.value = '';
    input.focus();
    // Remove previous listeners
    input.oninput = null;
    input.onkeydown = null;
    // Autocomplete and add tag on Enter/Tab/Comma
    input.addEventListener('input', () => showTagSuggestionsStandard(input, clipId));
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === 'Tab' || e.key === ',') {
            e.preventDefault();
            const val = input.value.trim();
            if (val && !editTagsState[clipId].includes(val)) {
                editTagsState[clipId].push(val);
                input.value = '';
                renderEditableTagChips(clipId);
            }
        } else if (e.key === 'Backspace' && input.value === '') {
            // Remove last tag if input is empty
            editTagsState[clipId].pop();
            renderEditableTagChips(clipId);
        }
    });
}

function renderEditableTagChips(clipId) {
    const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
    const tags = editTagsState[clipId] || [];
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
            x.onclick = () => {
                editTagsState[clipId] = editTagsState[clipId].filter(t => t !== tag);
                renderEditableTagChips(clipId);
            };
            chip.appendChild(x);
            tagsEdit.appendChild(chip);
        });
    }
}

function showTagSuggestionsStandard(input, clipId) {
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
    const inputVal = input.value.trim().toLowerCase();
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
            const filtered = data.tags.filter(tag => !editTagsState[clipId].includes(tag));
            if (filtered.length === 0) {
                dropdown.style.display = 'none';
                return;
            }
            filtered.forEach(tag => {
                const item = document.createElement('div');
                item.className = 'tag-suggestion-item';
                item.textContent = tag;
                item.onclick = () => {
                    editTagsState[clipId].push(tag);
                    input.value = '';
                    renderEditableTagChips(clipId);
                    dropdown.style.display = 'none';
                };
                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
        });
}

function saveTags(event) {
    event.preventDefault();
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    const tags = editTagsState[clipId] || [];
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
        document.getElementById(`tags-edit-${clipId}`).style.display = 'none';
        document.getElementById(`tag-input-new-${clipId}`).style.display = 'none';
        document.getElementById(`save-tag-btn-${clipId}`).style.display = 'none';
    })
    .catch(err => {
        alert('Error saving tags: ' + err);
    });
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