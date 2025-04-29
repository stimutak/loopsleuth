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

// Store original tags for cancel
const originalTagsState = {};

// --- Outside click to save/exit edit mode ---
function handleOutsideClick(e) {
    if (!e.target.closest('.tags') && !e.target.closest('.tag-input-new')) {
        // Find the currently open tag input (if any)
        const openInput = document.querySelector('.tag-input-new[style*="inline-block"]');
        if (openInput) {
            const clipId = openInput.getAttribute('data-clip-id');
            saveTags({target: {getAttribute: () => clipId}, preventDefault: () => {}, stopPropagation: () => {}});
        }
        document.removeEventListener('mousedown', handleOutsideClick, true);
    }
}

// --- Per-clip tag editing logic for detail view (single-clip only) ---
// This restores chip-style tag editing, autocomplete, and ARIA/keyboard UX for the detail view only.
// These functions are not used in the grid or batch bar.

function editTags(event) {
    event.preventDefault();
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    const tagsText = document.getElementById(`tags-text-${clipId}`);
    const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
    const input = document.getElementById(`tag-input-new-${clipId}`);
    const saveBtn = document.getElementById(`save-tag-btn-${clipId}`);
    const cancelBtn = document.getElementById(`cancel-tag-btn-${clipId}`);
    if (!tagsText || !tagsEdit || !input || !saveBtn || !cancelBtn) return;
    // Parse current tags from chips
    const tags = Array.from(tagsText.querySelectorAll('.tag-chip:not(.tag-empty)')).map(chip => chip.textContent.trim());
    editTagsState[clipId] = [...tags];
    originalTagsState[clipId] = [...tags];
    // Hide static, show editor
    tagsText.style.display = 'none';
    tagsEdit.style.display = 'inline-block';
    input.style.display = 'inline-block';
    saveBtn.style.display = 'inline-block';
    cancelBtn.style.display = 'inline-block';
    renderEditableTagChips(clipId);
    input.value = '';
    input.focus();
    // Keyboard/ARIA/autocomplete
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-controls', 'tag-suggestions-dropdown');
    input.setAttribute('aria-activedescendant', '');
    input._highlighted = -1;
    input._suggestions = [];
    input.onkeydown = function(e) {
        const dropdown = document.getElementById('tag-suggestions-dropdown');
        let suggestions = input._suggestions || [];
        let highlighted = typeof input._highlighted === 'number' ? input._highlighted : -1;
        if (e.key === 'Backspace' && input.value === '') {
            if (editTagsState[clipId].length > 0) {
                editTagsState[clipId].pop();
                renderEditableTagChips(clipId);
                e.preventDefault();
                return;
            }
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (suggestions.length > 0) {
                highlighted = (highlighted + 1) % suggestions.length;
                input._highlighted = highlighted;
                showTagSuggestionsStandard(input, clipId);
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (suggestions.length > 0) {
                highlighted = (highlighted - 1 + suggestions.length) % suggestions.length;
                input._highlighted = highlighted;
                showTagSuggestionsStandard(input, clipId);
            }
        } else if (e.key === 'Tab') {
            if (suggestions.length > 0 && highlighted >= 0) {
                e.preventDefault();
                addTagFromAutocomplete(input, clipId, suggestions[highlighted]);
                return;
            }
        } else if (e.key === 'Enter') {
            if (suggestions.length > 0 && highlighted >= 0) {
                e.preventDefault();
                addTagFromAutocomplete(input, clipId, suggestions[highlighted]);
                return;
            } else {
                // Add tag from input if not empty and not duplicate
                const val = input.value.trim();
                if (val && !editTagsState[clipId].map(t => t.toLowerCase()).includes(val.toLowerCase())) {
                    editTagsState[clipId].push(val);
                    renderEditableTagChips(clipId);
                    input.value = '';
                }
                input._highlighted = -1;
                input._suggestions = [];
                showTagSuggestionsStandard(input, clipId);
                e.preventDefault();
            }
        } else if (e.key === 'Escape') {
            if (dropdown && dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
                input._suggestions = [];
                input._highlighted = -1;
                e.preventDefault();
                return;
            }
        }
    };
    input.oninput = function() {
        showTagSuggestionsStandard(input, clipId);
    };
    input.onblur = function() {
        setTimeout(() => {
            let dropdown = document.getElementById('tag-suggestions-dropdown');
            if (dropdown) dropdown.style.display = 'none';
        }, 180);
    };
    document.addEventListener('mousedown', handleOutsideClick, true);
}

function cancelEditTags(event) {
    event.preventDefault();
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    const tagsText = document.getElementById(`tags-text-${clipId}`);
    const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
    const input = document.getElementById(`tag-input-new-${clipId}`);
    const saveBtn = document.getElementById(`save-tag-btn-${clipId}`);
    const cancelBtn = document.getElementById(`cancel-tag-btn-${clipId}`);
    if (!tagsText || !tagsEdit || !input || !saveBtn || !cancelBtn) return;
    // Restore original tags
    renderTagChips(clipId, originalTagsState[clipId]);
    // Hide editor, show static
    tagsText.style.display = 'inline-block';
    tagsEdit.style.display = 'none';
    input.style.display = 'none';
    saveBtn.style.display = 'none';
    cancelBtn.style.display = 'none';
    input.value = '';
    document.removeEventListener('mousedown', handleOutsideClick, true);
}

function saveTags(event) {
    event.preventDefault();
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    const tags = editTagsState[clipId] || [];
    fetch(`/tag/${clipId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tags})
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showToast('Tag update failed: ' + data.error, true);
            return;
        }
        renderTagChips(clipId, data.tags);
        // Hide editor, show static
        const tagsText = document.getElementById(`tags-text-${clipId}`);
        const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
        const input = document.getElementById(`tag-input-new-${clipId}`);
        const saveBtn = document.getElementById(`save-tag-btn-${clipId}`);
        const cancelBtn = document.getElementById(`cancel-tag-btn-${clipId}`);
        if (!tagsText || !tagsEdit || !input || !saveBtn || !cancelBtn) return;
        tagsText.style.display = 'inline-block';
        tagsEdit.style.display = 'none';
        input.style.display = 'none';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        input.value = '';
        showToast('Tags updated.');
        document.removeEventListener('mousedown', handleOutsideClick, true);
    })
    .catch(err => {
        showToast('Tag update error: ' + err, true);
    });
}

function renderEditableTagChips(clipId) {
    const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
    if (!tagsEdit) return;
    const tags = editTagsState[clipId] || [];
    tagsEdit.innerHTML = '';
    tagsEdit.setAttribute('role', 'list');
    if (tags.length === 0) {
        tagsEdit.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
    } else {
        tags.forEach((tag, idx) => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip tag-edit';
            chip.setAttribute('role', 'listitem');
            chip.setAttribute('aria-label', `Tag: ${tag}`);
            chip.appendChild(document.createTextNode(tag));
            const x = document.createElement('span');
            x.className = 'tag-chip-x';
            x.textContent = '×';
            x.setAttribute('aria-label', `Remove tag ${tag}`);
            x.onclick = () => {
                editTagsState[clipId].splice(idx, 1);
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
        input._suggestions = [];
        input._highlighted = -1;
        input.setAttribute('aria-expanded', 'false');
        return;
    }
    fetch(`/tags?q=${encodeURIComponent(inputVal)}`)
        .then(r => r.json())
        .then(data => {
            if (!data.tags || data.tags.length === 0) {
                dropdown.style.display = 'none';
                input._suggestions = [];
                input._highlighted = -1;
                input.setAttribute('aria-expanded', 'false');
                return;
            }
            // Filter out tags already present (case-insensitive)
            const present = (editTagsState[clipId] || []).map(t => t.toLowerCase());
            const filtered = data.tags.filter(tag => !present.includes(tag.toLowerCase()));
            input._suggestions = filtered;
            input._highlighted = (typeof input._highlighted === 'number' && input._highlighted >= 0) ? input._highlighted : -1;
            filtered.forEach((tag, idx) => {
                const item = document.createElement('div');
                item.className = 'tag-suggestion-item';
                item.textContent = tag;
                item.setAttribute('role', 'option');
                item.setAttribute('id', `tag-suggestion-${clipId}-${idx}`);
                item.setAttribute('aria-selected', input._highlighted === idx ? 'true' : 'false');
                if (input._highlighted === idx) {
                    item.style.background = '#2a3a3a';
                    item.style.color = '#fff';
                    setTimeout(() => { item.scrollIntoView({block: 'nearest'}); }, 0);
                    input.setAttribute('aria-activedescendant', item.id);
                }
                item.onmouseenter = () => {
                    input._highlighted = idx;
                    showTagSuggestionsStandard(input, clipId);
                };
                item.onmousedown = (e) => {
                    e.preventDefault();
                    addTagFromAutocomplete(input, clipId, tag);
                    dropdown.style.display = 'none';
                };
                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
            input.setAttribute('aria-expanded', 'true');
        });
}

function addTagFromAutocomplete(input, clipId, tag) {
    if (!editTagsState[clipId].map(t => t.toLowerCase()).includes(tag.toLowerCase())) {
        editTagsState[clipId].push(tag);
        renderEditableTagChips(clipId);
    }
    input.value = '';
    input._highlighted = -1;
    showTagSuggestionsStandard(input, clipId);
}

// --- Batch Tag Input State ---
const batchAddTagsState = [];
const batchRemoveTagsState = [];

// --- Global selection state for both bars ---
const selectedClipIds = new Set();
let lastSelectedIndex = null;

// --- Toast/snackbar feedback for user actions ---
function showToast(message, isError = false) {
    let toast = document.getElementById('toast-snackbar');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast-snackbar';
        toast.style.position = 'fixed';
        toast.style.left = '50%';
        toast.style.bottom = '2.5em';
        toast.style.transform = 'translateX(-50%)';
        toast.style.background = isError ? '#c0392b' : '#23272a';
        toast.style.color = '#fff';
        toast.style.padding = '1em 2em';
        toast.style.borderRadius = '8px';
        toast.style.fontSize = '1.1em';
        toast.style.zIndex = 3000;
        toast.style.boxShadow = '0 2px 12px #000a';
        toast.style.opacity = 0;
        toast.style.transition = 'opacity 0.3s';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.opacity = 1;
    setTimeout(() => { toast.style.opacity = 0; }, 2200);
}

if (document.getElementById('batch-action-bar')) {
    // --- Batch selection: checkbox and card click
    function renderBatchTagChips(type) {
        const container = document.getElementById(`batch-${type}-tags-chips`);
        if (!container) return; // Prevent error if batch bar is not visible
        const tags = type === 'add' ? batchAddTagsState : batchRemoveTagsState;
        container.innerHTML = '';
        container.setAttribute('role', 'list');
        if (tags.length === 0) {
            container.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
        } else {
            tags.forEach((tag, idx) => {
                const chip = document.createElement('span');
                chip.className = 'tag-chip tag-edit';
                chip.setAttribute('role', 'listitem');
                chip.setAttribute('aria-label', `Tag: ${tag}`);
                chip.appendChild(document.createTextNode(tag));
                const x = document.createElement('span');
                x.className = 'tag-chip-x';
                x.textContent = '×';
                x.setAttribute('aria-label', `Remove tag ${tag}`);
                x.onclick = () => {
                    // Remove tag from state and re-render chips and button state
                    tags.splice(idx, 1);
                    renderBatchTagChips(type);
                    // Also update Remove button state if this is the remove field
                    if (type === 'remove') {
                        const removeBtn = document.getElementById('batch-remove-btn');
                        if (removeBtn) removeBtn.disabled = batchRemoveTagsState.length === 0;
                    }
                };
                chip.appendChild(x);
                container.appendChild(chip);
            });
        }
        // Enable/disable Add/Remove button based on chip count
        if (type === 'add') {
            const addBtn = document.getElementById('batch-add-btn');
            if (addBtn) addBtn.disabled = tags.length === 0;
        } else if (type === 'remove') {
            const removeBtn = document.getElementById('batch-remove-btn');
            if (removeBtn) removeBtn.disabled = tags.length === 0;
        }
    }
    function handleBatchTagInput(type) {
        const input = document.getElementById(`batch-${type}-tags-input`);
        const tags = type === 'add' ? batchAddTagsState : batchRemoveTagsState;
        input.addEventListener('keydown', function(e) {
            if (type === 'add') console.log('[BatchAdd] keydown:', e.key, 'input:', input.value, 'tags:', tags);
            if (e.key === 'Backspace' && input.value === '') {
                if (tags.length > 0) {
                    tags.pop();
                    renderBatchTagChips(type);
                    e.preventDefault();
                    return;
                }
            }
            const dropdown = document.getElementById('batch-tag-suggestions-dropdown');
            let suggestions = input._suggestions || [];
            let highlighted = typeof input._highlighted === 'number' ? input._highlighted : -1;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (suggestions.length > 0) {
                    highlighted = (highlighted + 1) % suggestions.length;
                    input._highlighted = highlighted;
                    showBatchTagSuggestions(input, type);
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (suggestions.length > 0) {
                    highlighted = (highlighted - 1 + suggestions.length) % suggestions.length;
                    input._highlighted = highlighted;
                    showBatchTagSuggestions(input, type);
                }
            } else if (e.key === 'Tab' || e.key === 'Enter') {
                if (suggestions.length > 0 && highlighted >= 0) {
                    e.preventDefault();
                    addBatchTagFromAutocomplete(input, type, suggestions[highlighted]);
                    setTimeout(() => input.focus(), 0);
                    return;
                } else if (e.key === 'Enter' || e.key === 'Tab') {
                    // Add tag from input if not empty and not duplicate
                    const val = input.value.trim();
                    if (val && !tags.map(t => t.toLowerCase()).includes(val.toLowerCase())) {
                        tags.push(val);
                        console.log('[BatchAdd] tag added from input:', val, 'tags:', tags);
                        renderBatchTagChips(type);
                        input.value = '';
                        setTimeout(() => input.focus(), 0);
                    } else {
                        if (!val) console.log('[BatchAdd] ignored empty input');
                        else console.log('[BatchAdd] ignored duplicate:', val);
                    }
                    input._highlighted = -1;
                    input._suggestions = [];
                    showBatchTagSuggestions(input, type);
                    e.preventDefault();
                }
            } else if (e.key === 'Escape') {
                if (dropdown && dropdown.style.display === 'block') {
                    dropdown.style.display = 'none';
                    input._suggestions = [];
                    input._highlighted = -1;
                    e.preventDefault();
                    return;
                }
            }
        });
        input.addEventListener('input', function() {
            if (type === 'add') console.log('[BatchAdd] input event:', input.value, 'tags:', tags);
            showBatchTagSuggestions(input, type);
            // Enable Add button if there is a non-empty input or at least one chip
            const addBtn = document.getElementById('batch-add-btn');
            if (addBtn) addBtn.disabled = !(tags.length > 0 || input.value.trim().length > 0);
        });
        input.addEventListener('blur', function() {
            setTimeout(() => {
                let dropdown = document.getElementById('batch-tag-suggestions-dropdown');
                if (dropdown) dropdown.style.display = 'none';
            }, 180);
        });
    }
    function addBatchTagFromAutocomplete(input, type, tag) {
        const tags = type === 'add' ? batchAddTagsState : batchRemoveTagsState;
        if (!tags.map(t => t.toLowerCase()).includes(tag.toLowerCase())) {
            tags.push(tag);
            console.log('[BatchAdd] tag added from autocomplete:', tag, 'tags:', tags);
            renderBatchTagChips(type);
        } else {
            console.log('[BatchAdd] ignored duplicate from autocomplete:', tag);
        }
        input.value = '';
        input._highlighted = -1;
        showBatchTagSuggestions(input, type);
        setTimeout(() => input.focus(), 0);
    }
    function showBatchTagSuggestions(input, type) {
        let dropdown = document.getElementById('batch-tag-suggestions-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'batch-tag-suggestions-dropdown';
            dropdown.className = 'tag-suggestions-dropdown';
            dropdown.setAttribute('role', 'listbox');
            document.body.appendChild(dropdown);
        }
        const rect = input.getBoundingClientRect();
        dropdown.style.position = 'absolute';
        dropdown.style.left = `${rect.left + window.scrollX}px`;
        dropdown.style.top = `${rect.bottom + window.scrollY}px`;
        dropdown.style.width = `${rect.width}px`;
        dropdown.innerHTML = '';
        input.setAttribute('role', 'combobox');
        input.setAttribute('aria-autocomplete', 'list');
        input.setAttribute('aria-expanded', dropdown.style.display === 'block' ? 'true' : 'false');
        input.setAttribute('aria-controls', 'batch-tag-suggestions-dropdown');
        input.setAttribute('aria-activedescendant', '');
        const tags = type === 'add' ? batchAddTagsState : batchRemoveTagsState;
        const inputVal = input.value.trim().toLowerCase();
        if (!inputVal) {
            dropdown.style.display = 'none';
            input._suggestions = [];
            input._highlighted = -1;
            input.setAttribute('aria-expanded', 'false');
            return;
        }
        if (type === 'remove') {
            // Only suggest tags present in the selection and not already chips
            const suggestionsSource = getUnionTagsOfSelectedClips();
            const present = tags.map(t => t.toLowerCase());
            const filtered = suggestionsSource.filter(tag => tag.toLowerCase().startsWith(inputVal) && !present.includes(tag.toLowerCase()));
            console.log('[BatchAutocomplete] REMOVE suggestions:', filtered);
            if (filtered.length === 0) {
                dropdown.style.display = 'none';
                input._suggestions = [];
                input._highlighted = -1;
                input.setAttribute('aria-expanded', 'false');
                return;
            }
            input._suggestions = filtered;
            input._highlighted = (typeof input._highlighted === 'number' && input._highlighted >= 0) ? input._highlighted : -1;
            filtered.forEach((tag, idx) => {
                const item = document.createElement('div');
                item.className = 'tag-suggestion-item';
                item.textContent = tag;
                item.setAttribute('role', 'option');
                item.setAttribute('id', `batch-tag-suggestion-${type}-${idx}`);
                item.setAttribute('aria-selected', input._highlighted === idx ? 'true' : 'false');
                if (input._highlighted === idx) {
                    item.style.background = '#2a3a3a';
                    item.style.color = '#fff';
                    setTimeout(() => { item.scrollIntoView({block: 'nearest'}); }, 0);
                    input.setAttribute('aria-activedescendant', item.id);
                }
                item.onmouseenter = () => {
                    input._highlighted = idx;
                    showBatchTagSuggestions(input, type);
                };
                item.onmousedown = (e) => {
                    e.preventDefault();
                    addBatchTagFromAutocomplete(input, type, tag);
                    dropdown.style.display = 'none';
                };
                dropdown.appendChild(item);
            });
            dropdown.style.display = 'block';
            input.setAttribute('aria-expanded', 'true');
            return;
        }
        // Default: add mode, fetch from backend
        fetch(`/tags?q=${encodeURIComponent(inputVal)}`)
            .then(r => r.json())
            .then(data => {
                if (!data.tags || data.tags.length === 0) {
                    dropdown.style.display = 'none';
                    input._suggestions = [];
                    input._highlighted = -1;
                    input.setAttribute('aria-expanded', 'false');
                    return;
                }
                // Filter out tags already present (case-insensitive)
                const present = tags.map(t => t.toLowerCase());
                const filtered = data.tags.filter(tag => !present.includes(tag.toLowerCase()));
                console.log('[BatchAutocomplete] ADD suggestions:', filtered);
                if (filtered.length === 0) {
                    dropdown.style.display = 'none';
                    input._suggestions = [];
                    input._highlighted = -1;
                    input.setAttribute('aria-expanded', 'false');
                    return;
                }
                input._suggestions = filtered;
                input._highlighted = (typeof input._highlighted === 'number' && input._highlighted >= 0) ? input._highlighted : -1;
                filtered.forEach((tag, idx) => {
                    const item = document.createElement('div');
                    item.className = 'tag-suggestion-item';
                    item.textContent = tag;
                    item.setAttribute('role', 'option');
                    item.setAttribute('id', `batch-tag-suggestion-${type}-${idx}`);
                    item.setAttribute('aria-selected', input._highlighted === idx ? 'true' : 'false');
                    if (input._highlighted === idx) {
                        item.style.background = '#2a3a3a';
                        item.style.color = '#fff';
                        setTimeout(() => { item.scrollIntoView({block: 'nearest'}); }, 0);
                        input.setAttribute('aria-activedescendant', item.id);
                    }
                    item.onmouseenter = () => {
                        input._highlighted = idx;
                        showBatchTagSuggestions(input, type);
                    };
                    item.onmousedown = (e) => {
                        e.preventDefault();
                        addBatchTagFromAutocomplete(input, type, tag);
                        dropdown.style.display = 'none';
                    };
                    dropdown.appendChild(item);
                });
                dropdown.style.display = 'block';
                input.setAttribute('aria-expanded', 'true');
            });
    }
    function getUnionTagsOfSelectedClips() {
        const tagSet = new Set();
        selectedClipIds.forEach(clipId => {
            const tagsText = document.getElementById(`tags-text-${clipId}`);
            if (tagsText) {
                tagsText.querySelectorAll('.tag-chip:not(.tag-empty)').forEach(chip => {
                    tagSet.add(chip.textContent.trim());
                });
            }
        });
        return Array.from(tagSet).sort((a, b) => a.localeCompare(b));
    }
    function syncBatchRemoveTagsWithSelection() {
        const unionTags = getUnionTagsOfSelectedClips();
        // Only add tags that are not already in the remove state
        unionTags.forEach(tag => {
            if (!batchRemoveTagsState.map(t => t.toLowerCase()).includes(tag.toLowerCase())) {
                batchRemoveTagsState.push(tag);
            }
        });
        // Remove tags from batchRemoveTagsState that are no longer present in the selection
        for (let i = batchRemoveTagsState.length - 1; i >= 0; i--) {
            if (!unionTags.map(t => t.toLowerCase()).includes(batchRemoveTagsState[i].toLowerCase())) {
                batchRemoveTagsState.splice(i, 1);
            }
        }
        renderBatchTagChips('remove');
    }
    function renderBatchActionBar() {
        const bar = document.getElementById('batch-action-bar');
        if (!bar) {
            console.error('[BatchBar] #batch-action-bar not found in DOM');
            return;
        }
        // Always show the bar, but disable actions if nothing is selected
        bar.style.display = 'flex';
        const count = selectedClipIds.size;
        bar.innerHTML = `
            <div class="batch-bar-section">
                <span class="batch-bar-label">${count} selected</span>
            </div>
            <div class="batch-bar-section">
                <span class="batch-bar-label">Add tags:</span>
                <span id="batch-add-tags-chips" class="tags-edit" style="display:inline-block;"></span>
                <input type="text" class="batch-bar-input" id="batch-add-tags-input" placeholder="Add tag..." autocomplete="off" style="width:120px; margin-top:0.2em; display:inline-block;" />
                <button class="batch-bar-btn" id="batch-add-btn" ${count === 0 ? 'disabled' : ''}>Add</button>
            </div>
            <div class="batch-bar-section">
                <span class="batch-bar-label">Remove tags:</span>
                <span id="batch-remove-tags-chips" class="tags-edit" style="display:inline-block;"></span>
                <input type="text" class="batch-bar-input" id="batch-remove-tags-input" placeholder="Remove tag..." autocomplete="off" style="width:120px; margin-top:0.2em; display:inline-block;" />
                <button class="batch-bar-btn" id="batch-remove-btn" title="Removes only the tags shown as chips from all selected clips" ${count === 0 ? 'disabled' : ''}>Remove</button>
                <span class="batch-bar-help" style="font-size:0.85em; color:#aaa; margin-left:0.5em;" title="Select tags to remove, then press Remove to apply to all selected clips. Removing a chip only removes it from this list, not from the clips until you press Remove.">?</span>
            </div>
            <div class="batch-bar-section">
                <button class="batch-bar-btn" id="batch-clear-btn" ${count === 0 ? 'disabled' : ''}>Clear all tags</button>
            </div>
            <span class="batch-bar-help" title="Shift+Click: range select. Ctrl+Click (Windows/Linux) for multi-select. Cmd+Click may not work on macOS in all browsers. Use checkboxes for robust multi-select.">?</span>
        `;
        renderBatchTagChips('add');
        renderBatchTagChips('remove');
        handleBatchTagInput('add');
        handleBatchTagInput('remove');
        // Wire up events (backend integration next)
        document.getElementById('batch-add-btn').onclick = (e) => {
            e.preventDefault();
            if (count === 0 || batchAddTagsState.length === 0) {
                showToast('Select clips and enter tag(s) to add.', true);
                return;
            }
            const clipIds = Array.from(selectedClipIds).map(Number);
            fetch('/batch_tag', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: clipIds, add_tags: batchAddTagsState})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showToast('Batch add failed: ' + data.error, true);
                    return;
                }
                updateAllTagChips(data);
                showToast('Tags added to selected clips.');
                batchAddTagsState.length = 0;
                renderBatchTagChips('add');
                document.getElementById('batch-add-tags-input').value = '';
                setTimeout(() => document.getElementById('batch-add-tags-input').focus(), 0);
            })
            .catch(err => {
                showToast('Batch add error: ' + err, true);
            });
        };
        const removeBtn = document.getElementById('batch-remove-btn');
        removeBtn.disabled = count === 0 || batchRemoveTagsState.length === 0;
        removeBtn.onclick = () => {
            if (count === 0 || batchRemoveTagsState.length === 0) {
                showToast('Select clips and tags to remove.', true);
                return;
            }
            const clipIds = Array.from(selectedClipIds).map(Number);
            fetch('/batch_tag', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: clipIds, remove_tags: batchRemoveTagsState})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showToast('Batch remove failed: ' + data.error, true);
                    return;
                }
                updateAllTagChips(data);
                showToast('Tags removed from selected clips.');
                batchRemoveTagsState.length = 0;
                renderBatchTagChips('remove');
                document.getElementById('batch-remove-tags-input').value = '';
            })
            .catch(err => {
                showToast('Batch remove error: ' + err, true);
            });
        };
        const clearBtn = document.getElementById('batch-clear-btn');
        clearBtn.disabled = count === 0;
        clearBtn.onclick = () => {
            if (count === 0) return;
            if (!confirm('Clear all tags from selected clips?')) return;
            const clipIds = Array.from(selectedClipIds).map(Number);
            fetch('/batch_tag', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: clipIds, clear: true})
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) {
                    showToast('Batch clear failed: ' + data.error, true);
                    return;
                }
                updateAllTagChips(data);
                showToast('All tags cleared from selected clips.');
            })
            .catch(err => {
                showToast('Batch clear error: ' + err, true);
            });
        };
    }
    function updateCardSelectionUI() {
        console.log('[updateCardSelectionUI] called');
        document.querySelectorAll('.card[data-clip-id]').forEach(card => {
            const clipId = card.getAttribute('data-clip-id');
            const checkbox = card.querySelector('.select-clip-checkbox');
            if (selectedClipIds.has(clipId)) {
                card.classList.add('selected');
                checkbox.checked = true;
            } else {
                card.classList.remove('selected');
                checkbox.checked = false;
            }
        });
        // Show/hide batch action bar and render controls
        renderBatchActionBar();
        syncBatchRemoveTagsWithSelection();
        renderSelectedClipsBar();
    }

    document.addEventListener('DOMContentLoaded', function() {
        // --- Removed redundant card event handler block ---
        // All card event handlers (selection, checkbox, PiP, etc.) are now attached exclusively
        // via afterGridUpdate() and attachCardEventHandlers() for robustness and maintainability.
        // See the end of this file for afterGridUpdate definition and usage.
        //
        // This prevents duplicate handlers and ensures consistent selection logic after grid updates.
        //
        // If you need to add new per-card logic, do so in attachCardEventHandlers().
        //
        // (No card selection logic here.)
    });
}

// --- Utility: Render static tag chips for a clip (used by both grid and detail views) ---
function renderTagChips(clipId, tags) {
    const tagsText = document.getElementById(`tags-text-${clipId}`);
    if (!tagsText) return;
    tagsText.innerHTML = '';
    if (!tags || tags.length === 0) {
        tagsText.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
    } else {
        tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip';
            chip.appendChild(document.createTextNode(tag));
            tagsText.appendChild(chip);
        });
    }
}

// --- PATCH: Decouple playlist filtering from target selection ---
// Filtering uses ?playlist_id in the URL, target selection uses selectedPlaylistIds (sidebar checkboxes)
function getActiveFilterPlaylistId() {
    const params = new URLSearchParams(window.location.search);
    return params.get('playlist_id') || null;
}

// --- On page load, do NOT set selectedPlaylistIds from filter param ---
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize selectedPlaylistIds as empty; sidebar checkboxes will update it
    selectedPlaylistIds = [];
    renderSelectedClipsBar();
    renderPlaylistSidebar();
    // Show/hide clear filter button
    const clearBtn = document.getElementById('clear-playlist-filter-btn');
    if (clearBtn) {
        clearBtn.style.display = getActiveFilterPlaylistId() ? '' : 'none';
        clearBtn.onclick = function() {
            const params = new URLSearchParams(window.location.search);
            params.delete('playlist_id');
            window.location.search = params.toString();
        };
        clearBtn.onkeydown = function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                clearBtn.click();
            }
        };
    }
});

// --- In renderPlaylistSidebar, checkboxes reflect only selectedPlaylistIds, not filter ---
function renderPlaylistSidebar(cbAfter) {
    const listDiv = document.getElementById('playlist-list');
    const createBtn = document.getElementById('playlist-create-btn');
    const detailsDiv = document.getElementById('playlist-details');
    if (!listDiv || !createBtn) return;
    fetch('/playlists')
        .then(r => r.json())
        .then(data => {
            if (!data.playlists) return;
            listDiv.innerHTML = '';
            data.playlists.forEach((pl, idx) => {
                const item = document.createElement('div');
                item.className = 'playlist-item';
                item.dataset.playlistId = pl.id;
                // --- Multi-select checkbox (target for add/remove) ---
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'playlist-checkbox';
                checkbox.tabIndex = 0;
                checkbox.setAttribute('aria-label', `Select playlist ${pl.name} as target`);
                checkbox.checked = selectedPlaylistIds.includes(String(pl.id));
                checkbox.onclick = (e) => {
                    e.stopPropagation();
                    if (selectedPlaylistIds.includes(String(pl.id))) {
                        selectedPlaylistIds = selectedPlaylistIds.filter(id => id !== String(pl.id));
                    } else {
                        selectedPlaylistIds = [...selectedPlaylistIds, String(pl.id)];
                    }
                    renderSelectedClipsBar();
                    item.classList.toggle('selected', checkbox.checked);
                };
                item.appendChild(checkbox);
                // --- Playlist name (no filtering on click) ---
                const nameSpan = document.createElement('span');
                nameSpan.textContent = pl.name;
                nameSpan.className = 'playlist-name';
                nameSpan.title = pl.name;
                nameSpan.style.marginLeft = '0.5em';
                item.appendChild(nameSpan);
                // --- Filter icon/button ---
                const filterBtn = document.createElement('button');
                filterBtn.className = 'playlist-filter-btn';
                filterBtn.title = 'Filter grid by this playlist';
                filterBtn.innerHTML = '<span style="font-size:1.1em;">🔍</span>';
                filterBtn.style.marginLeft = '0.7em';
                filterBtn.style.background = 'none';
                filterBtn.style.border = 'none';
                filterBtn.style.cursor = 'pointer';
                filterBtn.tabIndex = 0;
                filterBtn.onclick = (e) => {
                    e.stopPropagation();
                    const params = new URLSearchParams(window.location.search);
                    params.set('playlist_id', pl.id);
                    window.location.search = params.toString();
                };
                item.appendChild(filterBtn);
                filterBtn.onkeydown = (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        filterBtn.click();
                    }
                };
                // --- Highlight if selected as target ---
                if (selectedPlaylistIds.includes(String(pl.id))) {
                    item.classList.add('selected');
                    item.classList.add('selected-multi');
                }
                listDiv.appendChild(item);
            });
            // --- Highlight the currently filtered playlist ---
            const params = new URLSearchParams(window.location.search);
            const activeFilterId = params.get('playlist_id');
            if (activeFilterId) {
                const activeItem = listDiv.querySelector(`.playlist-item[data-playlist-id="${activeFilterId}"]`);
                if (activeItem) activeItem.classList.add('active-filter');
            }
            if (cbAfter) cbAfter();
        });
    createBtn.onclick = () => {
        const name = prompt('New playlist name:');
        if (!name) return;
        fetch('/playlists', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                showToast('Create failed: ' + data.error, true);
                return;
            }
            // --- PATCH: If clips are selected, immediately add them to the new playlist ---
            const newPlaylistId = data.id;
            const selectedClips = Array.from(selectedClipIds);
            if (selectedClips.length > 0) {
                fetch('/playlists/clips', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ clip_ids: selectedClips.map(Number), playlist_ids: [newPlaylistId] })
                })
                .then(resp => resp.ok ? resp.json() : Promise.reject(resp))
                .then(() => {
                    // Show toast and highlight affected clips
                    showToast(`Created playlist and added ${selectedClips.length} clip${selectedClips.length > 1 ? 's' : ''} to "${name}"`);
                    renderPlaylistSidebar(() => {
                        selectedPlaylistIds = [...selectedPlaylistIds, String(newPlaylistId)];
                        attachPlaylistCheckboxHandlers();
                        renderSelectedClipsBar();
                    });
                    // Highlight affected clips
                    setTimeout(() => {
                        selectedClips.forEach(id => {
                            const card = document.querySelector(`.card[data-clip-id='${id}']`);
                            if (card) {
                                card.classList.add('playlist-added-highlight');
                                setTimeout(() => card.classList.remove('playlist-added-highlight'), 3500);
                            }
                        });
                    }, 400);
                })
                .catch(() => {
                    showToast('Playlist created, but failed to add clips.', true);
                    renderPlaylistSidebar(() => {
                        selectedPlaylistIds = [...selectedPlaylistIds, String(newPlaylistId)];
                        attachPlaylistCheckboxHandlers();
                        renderSelectedClipsBar();
                    });
                });
            } else {
                showToast('Playlist created.');
                renderPlaylistSidebar(() => {
                    selectedPlaylistIds = [...selectedPlaylistIds, String(newPlaylistId)];
                    attachPlaylistCheckboxHandlers();
                    renderSelectedClipsBar();
                });
            }
        });
    };
    detailsDiv.innerHTML = '<em>Select a playlist to view details.</em>';
}

// --- PATCH: Utility to re-attach checkbox event handlers after sidebar updates ---
function attachPlaylistCheckboxHandlers() {
    const listDiv = document.getElementById('playlist-list');
    if (!listDiv) return;
    const items = listDiv.querySelectorAll('.playlist-item');
    items.forEach(item => {
        const checkbox = item.querySelector('.playlist-checkbox');
        if (checkbox) {
            checkbox.onclick = (e) => {
                e.stopPropagation();
                const plId = item.dataset.playlistId;
                if (selectedPlaylistIds.includes(String(plId))) {
                    selectedPlaylistIds = selectedPlaylistIds.filter(id => id !== String(plId));
                } else {
                    selectedPlaylistIds = [...selectedPlaylistIds, String(plId)];
                }
                renderSelectedClipsBar();
                item.classList.toggle('selected', checkbox.checked);
            };
        }
    });
}

// --- Pills: highlight all active pills for selected playlists ---
function getActivePlaylistIds() {
    return selectedPlaylistIds;
}

// --- Selected Clips Bar: Always Visible, Responsive ---
function renderSelectedClipsBar() {
    console.log('renderSelectedClipsBar called');
    const bar = document.getElementById('selected-clips-bar');
    if (!bar) return;
    const count = selectedClipIds.size;
    const playlistEnabled = count > 0 && selectedPlaylistIds.length > 0;
    bar.style.display = '';
    bar.innerHTML = `
        <span class="selected-bar-label">${count} selected</span>
        <button class="selected-bar-btn" id="selected-export-btn" ${count === 0 ? 'disabled' : ''} title="Export selected clip paths">
            <span class="selected-bar-icon">📄</span> Export List
        </button>
        <button class="selected-bar-btn" id="selected-copy-btn" ${count === 0 ? 'disabled' : ''} title="Copy/move selected files">
            <span class="selected-bar-icon">📁</span> Copy to Folder
        </button>
        <button class="selected-bar-btn" id="selected-preview-grid-btn" ${count === 0 ? 'disabled' : ''} title="Preview selected clips in a floating grid">
            <span class="selected-bar-icon">🎬</span> Preview Grid
        </button>
        <button class="selected-bar-btn" id="selected-add-to-playlist-btn" ${playlistEnabled ? '' : 'disabled'} title="Add selected clips to playlist">
            <span class="selected-bar-icon">➕</span> Add to Playlist
        </button>
        <button class="selected-bar-btn" id="selected-remove-from-playlist-btn" ${playlistEnabled ? '' : 'disabled'} title="Remove selected clips from playlist">
            <span class="selected-bar-icon">➖</span> Remove from Playlist
        </button>
        <button class="selected-bar-btn" id="selected-clear-btn" ${count === 0 ? 'disabled' : ''} title="Clear selection">
            <span class="selected-bar-icon">✖️</span> Clear
        </button>
    `;
    console.log('Bar rendered, attaching handlers');
    const previewBtn = document.getElementById('selected-preview-grid-btn');
    console.log('Attaching handler to', previewBtn);
    previewBtn.onclick = function(e) {
        e.preventDefault();
        console.log('Button native click');
        if (selectedClipIds.size === 0) return;
        const selected = Array.from(selectedClipIds);
        console.log('About to call openPreviewGrid with', selected);
        openPreviewGrid(selected);
    };
    document.getElementById('selected-export-btn').onclick = async (e) => {
        if (count === 0) return;
        const ids = Array.from(selectedClipIds).map(Number);
        try {
            const resp = await fetch('/export_selected', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: ids})
            });
            if (!resp.ok) {
                const err = await resp.json();
                showToast('Export failed: ' + (err.error || resp.status), true);
                return;
            }
            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'keepers.txt';
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                window.URL.revokeObjectURL(url);
                a.remove();
            }, 100);
            showToast('Exported keepers.txt');
        } catch (err) {
            showToast('Export error: ' + err, true);
        }
    };
    document.getElementById('selected-copy-btn').onclick = async (e) => {
        if (count === 0) return;
        let dest = prompt('Copy selected files to which folder? (absolute path)');
        if (!dest) return;
        const ids = Array.from(selectedClipIds).map(Number);
        try {
            const resp = await fetch('/copy_selected', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: ids, dest_folder: dest})
            });
            const data = await resp.json();
            if (!resp.ok || data.error) {
                showToast('Copy failed: ' + (data.error || resp.status), true);
                return;
            }
            const ok = Object.values(data.results).filter(v => v === 'ok').length;
            const err = Object.values(data.results).length - ok;
            let msg = `Copied ${ok} file(s)`;
            if (err > 0) msg += `, ${err} error(s)`;
            showToast(msg + '.');
            if (err > 0) {
                console.warn('[Copy] Errors:', data.results);
            }
        } catch (err) {
            showToast('Copy error: ' + err, true);
        }
    };
    document.getElementById('selected-add-to-playlist-btn').onclick = async (e) => {
        // Multi-playlist support: send both selectedPlaylistIds and selectedClipIds
        if (!selectedPlaylistIds.length || selectedClipIds.size === 0) return;
        const ids = Array.from(selectedClipIds).map(Number);
        const playlistIds = selectedPlaylistIds.map(Number);
        // --- PATCH: Store summary for post-reload feedback ---
        // Fetch playlist names for summary
        let playlistNames = [];
        try {
            const resp = await fetch('/playlists');
            const data = await resp.json();
            if (data && data.playlists) {
                playlistNames = data.playlists.filter(pl => playlistIds.includes(pl.id)).map(pl => pl.name);
            }
        } catch {}
        try {
            const resp = await fetch('/playlists/clips', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clip_ids: ids, playlist_ids: playlistIds })
            });
            if (resp.ok) {
                // --- PATCH: Store summary in localStorage for feedback after reload ---
                localStorage.setItem('playlistAddSummary', JSON.stringify({
                    clipIds: ids,
                    playlistNames: playlistNames,
                    count: ids.length
                }));
                showToast('Added to selected playlist(s)!', 'success');
                clearSelection();
                setTimeout(() => window.location.reload(), 600); // Give toast time to show, then reload grid
            } else {
                showToast('Failed to add to playlist(s)', 'error');
            }
        } finally {
            document.getElementById('selected-add-to-playlist-btn').disabled = false;
        }
    };
    document.getElementById('selected-remove-from-playlist-btn').onclick = async (e) => {
        if (!selectedPlaylistIds.length) {
            showToast('Select a playlist first.', true);
            return;
        }
        const ids = Array.from(selectedClipIds).map(Number);
        try {
            const resp = await fetch('/playlists/clips/remove', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: ids})
            });
            const data = await resp.json();
            if (!resp.ok || data.error) {
                showToast('Remove from playlist failed: ' + (data.error || resp.status), true);
                return;
            }
            showToast('Removed from playlist.');
            selectPlaylist(selectedPlaylistIds[0]);
            // --- PATCH: Reload grid to show updated playlist pills ---
            setTimeout(() => window.location.reload(), 600);
        } catch (err) {
            showToast('Remove from playlist error: ' + err, true);
        }
    };
    document.getElementById('selected-clear-btn').onclick = (e) => {
        if (count === 0) return;
        selectedClipIds.clear();
        updateCardSelectionUI();
    };
}

document.addEventListener('DOMContentLoaded', function() {
    renderSelectedClipsBar();
    renderPlaylistSidebar();
});

// --- Preview Grid logic ---
function openPreviewGrid(selectedClipIds) {
    console.log('openPreviewGrid called with:', selectedClipIds);
    if (!selectedClipIds || selectedClipIds.length === 0) {
        console.log('No selectedClipIds, aborting');
        return;
    }
    let overlay = document.getElementById('preview-grid-overlay');
    if (overlay) overlay.remove();
    overlay = document.createElement('div');
    overlay.id = 'preview-grid-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.background = 'rgba(18,20,24,0.97)';
    overlay.style.zIndex = '3000';
    overlay.style.display = 'flex';
    overlay.style.flexDirection = 'column';
    overlay.style.padding = '2em';
    overlay.innerHTML = `<button id="close-preview-grid" style="position:absolute; top:1em; right:1.5em; font-size:1.5em; background:none; border:none; color:#aaa; cursor:pointer;">✖</button>`;
    const grid = document.createElement('div');
    const n = selectedClipIds.length;

    // Ensure overlay fills viewport
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    // Use grid: one column per video, always fill overlay
    grid.style.display = 'grid';
    grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(320px, 1fr))';
    grid.style.justifyContent = 'center';
    grid.style.alignItems = 'start';
    grid.style.gap = '1.5em';
    grid.style.width = '100vw';
    grid.style.height = 'auto';

    let foundCount = 0;
    selectedClipIds.forEach(clipId => {
        const card = document.querySelector(`.card[data-clip-id='${clipId}']`);
        if (!card) {
            console.log('No card found for clipId', clipId);
            return;
        }
        foundCount++;
        const filename = card.querySelector('.filename').textContent;
        const videoUrl = '/media/' + card.getAttribute('data-path');
        const cell = document.createElement('div');
        cell.style.background = '#181a1b';
        cell.style.borderRadius = '10px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.alignItems = 'center';
        cell.style.justifyContent = 'center';
        cell.style.padding = '0.7em';
        cell.style.margin = 'auto';
        cell.style.maxWidth = '800px';
        cell.style.width = '100%';
        cell.style.height = 'auto';
        cell.style.aspectRatio = '16 / 9';
        cell.style.display = 'flex';
        cell.style.alignItems = 'center';
        cell.style.justifyContent = 'center';
        cell.style.margin = 'auto';
        cell.innerHTML = `<div style='font-size:0.93em;color:#bbb;margin-bottom:0.3em;'>${filename}</div>`;
        const video = document.createElement('video');
        video.src = videoUrl;
        video.controls = true;
        video.muted = true;
        video.style.maxWidth = '100%';
        video.style.maxHeight = '100%';
        video.style.width = '100%';
        video.style.height = '100%';
        video.style.objectFit = 'contain';
        video.style.borderRadius = '6px';
        video.style.background = '#111';
        cell.appendChild(video);
        const controls = document.createElement('div');
        controls.style.display = 'flex';
        controls.style.gap = '0.7em';
        controls.style.marginTop = '0.3em';
        const playBtn = document.createElement('button');
        playBtn.textContent = '▶';
        playBtn.title = 'Play/Pause';
        playBtn.onclick = () => { video.paused ? video.play() : video.pause(); };
        const muteBtn = document.createElement('button');
        muteBtn.textContent = '🔇';
        muteBtn.title = 'Mute/Unmute';
        muteBtn.onclick = () => { video.muted = !video.muted; muteBtn.textContent = video.muted ? '🔇' : '🔊'; };
        const closeBtn = document.createElement('button');
        closeBtn.textContent = '✖';
        closeBtn.title = 'Close';
        closeBtn.onclick = () => { cell.remove(); };
        controls.appendChild(playBtn);
        controls.appendChild(muteBtn);
        controls.appendChild(closeBtn);
        cell.appendChild(controls);
        grid.appendChild(cell);
    });
    console.log('Preview grid: found', foundCount, 'cards out of', n);
    overlay.appendChild(grid);
    document.body.appendChild(overlay);
    console.log('Preview grid overlay appended to DOM');
    document.getElementById('close-preview-grid').onclick = () => overlay.remove();
}

// --- Patch: Always update tag chips in grid and detail after batch tag actions ---
function updateAllTagChips(data) {
    for (const [clipId, tags] of Object.entries(data)) {
        renderTagChips(clipId, tags);
        // Also update detail view if present
        const detailTags = document.getElementById(`tags-text-detail-${clipId}`);
        if (detailTags) {
            detailTags.innerHTML = '';
            if (!tags || tags.length === 0) {
                detailTags.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
            } else {
                tags.forEach(tag => {
                    const chip = document.createElement('span');
                    chip.className = 'tag-chip';
                    chip.appendChild(document.createTextNode(tag));
                    detailTags.appendChild(chip);
                });
            }
        }
    }
}

// --- Patch: Preview grid button enable/disable and click handler ---
function patchSelectedClipsBarForPreviewGrid() {
    const bar = document.getElementById('selected-clips-bar');
    if (!bar) return;
    let btn = document.getElementById('selected-preview-grid-btn');
    if (!btn) {
        btn = document.createElement('button');
        btn.id = 'selected-preview-grid-btn';
        btn.className = 'selected-bar-btn';
        btn.innerHTML = '<span class="selected-bar-icon">🎬</span> Preview Grid';
        btn.title = 'Preview selected clips in a floating grid';
        bar.appendChild(btn);
    }
    function updateBtn() {
        const selected = document.querySelectorAll('.card.selected');
        btn.disabled = selected.length === 0;
    }
    btn.onclick = function() {
        const selected = Array.from(document.querySelectorAll('.card.selected')).map(card => card.getAttribute('data-clip-id'));
        if (selected.length > 0) openPreviewGrid(selected);
    };
    document.addEventListener('selectionchange', updateBtn);
    document.addEventListener('click', updateBtn);
    updateBtn();
}
document.addEventListener('DOMContentLoaded', patchSelectedClipsBarForPreviewGrid);

// --- Attach all card event handlers (selection, hover, checkbox, PiP) ---
function attachCardEventHandlers() {
    const cards = document.querySelectorAll('.card[data-clip-id]');
    console.log('[attachCardEventHandlers] Found', cards.length, 'cards');
    if (cards.length === 0) {
        console.warn('[attachCardEventHandlers] No .card elements found!');
    }
    cards.forEach(card => {
        card.setAttribute('tabindex', '0');
        // Remove previous handlers to avoid duplicates
        card.onmouseover = card.onmouseout = card.onfocus = card.onblur = null;
        card.onclick = null;
        // Visual hover/focus effect
        card.addEventListener('mouseover', () => card.classList.add('card-hover'));
        card.addEventListener('mouseout', () => card.classList.remove('card-hover'));
        card.addEventListener('focus', () => card.classList.add('card-hover'));
        card.addEventListener('blur', () => card.classList.remove('card-hover'));
        // Card-wide click for selection (except on links/buttons/inputs/checkboxes/PiP)
        card.addEventListener('click', function(e) {
            e.preventDefault(); // Prevent default browser behavior
            const clipId = card.getAttribute('data-clip-id');
            // Only skip if the target is a link, button, input, or certain controls
            if (e.target.closest('a,button,input,.pip-btn,.custom-checkbox,.select-clip-checkbox')) return;
            // --- Selection logic with Cmd/Ctrl+Click enabled for testing ---
            const allCards = Array.from(document.querySelectorAll('.card[data-clip-id]'));
            const idx = allCards.indexOf(card);
            const isShift = e.shiftKey;
            const isCtrl = e.ctrlKey || e.metaKey; // Enable Cmd/Ctrl+Click for multi-select
            if (isShift && lastSelectedIndex !== null) {
                // Shift+Click: range select
                const [start, end] = [lastSelectedIndex, idx].sort((a, b) => a - b);
                for (let i = start; i <= end; i++) {
                    selectedClipIds.add(allCards[i].getAttribute('data-clip-id'));
                }
                lastSelectedIndex = idx;
            } else if (isCtrl) {
                // Cmd/Ctrl+Click: toggle selection, never clear all
                if (selectedClipIds.has(clipId)) {
                    selectedClipIds.delete(clipId);
                } else {
                    selectedClipIds.add(clipId);
                }
                // Do not update lastSelectedIndex (keeps anchor for shift+click)
            } else {
                // Single click: always select only this card
                selectedClipIds.clear();
                selectedClipIds.add(clipId);
                lastSelectedIndex = idx;
            }
            updateCardSelectionUI();
        });
        // Checkbox click: always toggle selection, never clear all
        const checkbox = card.querySelector('.select-clip-checkbox');
        if (checkbox) {
            checkbox.onclick = function(e) {
                e.stopPropagation();
                const clipId = card.getAttribute('data-clip-id');
                if (checkbox.checked) {
                    selectedClipIds.add(clipId);
                } else {
                    selectedClipIds.delete(clipId);
                }
                lastSelectedIndex = Array.from(document.querySelectorAll('.card[data-clip-id]')).indexOf(card);
                updateCardSelectionUI();
            };
        }
        // PiP button click
        const pipBtn = card.querySelector('.pip-btn');
        if (pipBtn) {
            pipBtn.onclick = function(e) {
                e.stopPropagation();
                const clipId = card.getAttribute('data-clip-id');
                const video = document.getElementById('pip-video-' + clipId);
                if (video && card) {
                    const videoUrl = '/media/' + card.getAttribute('data-path');
                    video.src = videoUrl;
                    video.currentTime = 0;
                    video.load();
                    video.muted = true;
                    video.onerror = null;
                    video.addEventListener('error', function onVideoError() {
                        let errMsg = 'Unknown error';
                        if (video.error) {
                            switch (video.error.code) {
                                case 1: errMsg = 'MEDIA_ERR_ABORTED'; break;
                                case 2: errMsg = 'MEDIA_ERR_NETWORK'; break;
                                case 3: errMsg = 'MEDIA_ERR_DECODE'; break;
                                case 4: errMsg = 'MEDIA_ERR_SRC_NOT_SUPPORTED'; break;
                            }
                        }
                        showToast('Video error: ' + errMsg + ' (' + video.src + ')', 6000);
                    }, { once: true });
                    let canplayTimeout = setTimeout(() => {
                        showToast('Could not load video for PiP: ' + videoUrl, 6000);
                        video.removeEventListener('canplay', onCanPlay);
                    }, 10000);
                    function onCanPlay() {
                        clearTimeout(canplayTimeout);
                        video.removeEventListener('canplay', onCanPlay);
                        video.play().then(() => {
                            if (document.pictureInPictureElement) {
                                document.exitPictureInPicture();
                            }
                            if (video.webkitSupportsPresentationMode && typeof video.webkitSetPresentationMode === 'function') {
                                try {
                                    video.webkitSetPresentationMode('picture-in-picture');
                                } catch (err) {
                                    showToast('Picture-in-Picture not supported in this browser.');
                                }
                            } else if (video.requestPictureInPicture) {
                                video.requestPictureInPicture().catch(err => {
                                    showToast('Picture-in-Picture not supported or failed.');
                                });
                            } else {
                                showToast('Picture-in-Picture not supported in this browser.');
                            }
                        }).catch(err => {
                            showToast('Could not play video for PiP.');
                        });
                    }
                    video.addEventListener('canplay', onCanPlay);
                }
            };
        }
    });
}
// Call attachCardEventHandlers after every grid update and on DOMContentLoaded
function afterGridUpdate() {
    console.log('[afterGridUpdate] called');
    attachCardEventHandlers();
    updateCardSelectionUI();
    attachPlaylistPillRemoveHandlers(); // Attach remove handlers for playlist pills
}
document.addEventListener('DOMContentLoaded', afterGridUpdate);

/**
 * Render the batch duplicate review UI on /duplicates page.
 * Fetches /api/duplicates and renders each group with canonical and duplicates.
 * For each duplicate, show action buttons: Keep, Delete, Ignore.
 * Uses showToast for feedback. Updates UI after actions.
 */
window.renderDuplicateReviewUI = function() {
    const container = document.getElementById('duplicate-review-container');
    if (!container) return;
    container.innerHTML = '<div class="loading">Loading duplicate groups...</div>';
    fetch('/api/duplicates')
        .then(r => r.json())
        .then(data => {
            if (!data.duplicate_groups || data.duplicate_groups.length === 0) {
                container.innerHTML = '<div class="empty">No duplicates flagged for review.</div>';
                return;
            }
            container.innerHTML = '';
            data.duplicate_groups.forEach(group => {
                const canonical = group.canonical;
                const dups = group.duplicates;
                // Canonical card
                const canonicalCard = `
                  <div class="canonical-clip">
                    <h3>Canonical</h3>
                    <img src="/thumbs/${canonical.thumbnail_path ? canonical.thumbnail_path.split('/').pop() : 'missing.jpg'}" alt="Canonical thumbnail">
                    <div><b>${canonical.filename}</b></div>
                    <div class="meta">ID: ${canonical.id} | Duration: ${canonical.duration || '?'} | Size: ${canonical.size || '?'}<br>pHash: <span style="font-family:monospace;">${canonical.phash || '?'}</span></div>
                  </div>
                `;
                // Duplicates list
                const dupCards = dups.map(dup => `
                  <div class="duplicate-card" data-clip-id="${dup.id}">
                    <img src="/thumbs/${dup.thumbnail_path ? dup.thumbnail_path.split('/').pop() : 'missing.jpg'}" alt="Duplicate thumbnail">
                    <div>
                      <b>${dup.filename}</b><br>
                      <span class="meta">ID: ${dup.id} | Duration: ${dup.duration || '?'} | Size: ${dup.size || '?'}<br>pHash: <span style="font-family:monospace;">${dup.phash || '?'}</span></span>
                    </div>
                    <div class="duplicate-actions">
                      <button onclick="window.handleDuplicateAction(${dup.id}, 'keep', ${canonical.id})">Keep</button>
                      <button onclick="window.handleDuplicateAction(${dup.id}, 'delete', ${canonical.id})">Delete</button>
                      <button onclick="window.handleDuplicateAction(${dup.id}, 'ignore', ${canonical.id})">Ignore</button>
                      <button onclick="window.handleDuplicateAction(${dup.id}, 'merge', ${canonical.id})">Merge</button>
                    </div>
                  </div>
                `).join('');
                const groupDiv = document.createElement('div');
                groupDiv.className = 'duplicate-group';
                groupDiv.innerHTML = canonicalCard + `<div class="duplicate-clips">${dupCards}</div>`;
                container.appendChild(groupDiv);
            });
        })
        .catch(err => {
            container.innerHTML = `<div class="error">Failed to load duplicates: ${err}</div>`;
        });
};

/**
 * Handle actions for a duplicate: keep, delete, ignore.
 * (Backend endpoints for these actions must be implemented.)
 */
window.handleDuplicateAction = function(dupId, action, canonicalId) {
    fetch('/api/duplicate_action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({dup_id: dupId, action, canonical_id: canonicalId})
    })
    .then(r => r.json())
    .then(data => {
        if (data.error) {
            showToast('Action failed: ' + data.error, true);
            return;
        }
        // Remove the duplicate card from the UI
        const card = document.querySelector(`.duplicate-card[data-clip-id='${dupId}']`);
        if (card) {
            const group = card.closest('.duplicate-group');
            card.remove();
            // If no more duplicates in group, remove the group
            if (group && group.querySelectorAll('.duplicate-card').length === 0) {
                group.remove();
            }
        }
        let msg = '';
        if (action === 'keep') msg = 'Marked as not duplicate.';
        else if (action === 'delete') msg = 'Duplicate deleted.';
        else if (action === 'ignore') msg = 'Duplicate ignored.';
        else if (action === 'merge') {
            msg = 'Merged tags/playlists and deleted duplicate.';
            if (data.tags_merged && data.tags_merged.length > 0) {
                msg += ` Tags merged: ${data.tags_merged.join(', ')}.`;
            }
            if (data.playlists_merged && data.playlists_merged.length > 0) {
                msg += ` Playlists merged: ${data.playlists_merged.join(', ')}.`;
            }
        }
        showToast(msg);
        // If no groups left, show empty message
        const container = document.getElementById('duplicate-review-container');
        if (container && container.querySelectorAll('.duplicate-group').length === 0) {
            container.innerHTML = '<div class="empty">No duplicates flagged for review.</div>';
        }
    })
    .catch(err => {
        showToast('Action error: ' + err, true);
    });
};

// --- PATCH: On page load, show persistent toast and highlight affected clips if playlistAddSummary exists ---
document.addEventListener('DOMContentLoaded', function() {
    const summaryRaw = localStorage.getItem('playlistAddSummary');
    if (summaryRaw) {
        localStorage.removeItem('playlistAddSummary');
        try {
            const summary = JSON.parse(summaryRaw);
            let msg = '';
            if (summary.count && summary.playlistNames && summary.playlistNames.length > 0) {
                msg = `Added ${summary.count} clip${summary.count > 1 ? 's' : ''} to playlist${summary.playlistNames.length > 1 ? 's' : ''}: ${summary.playlistNames.join(', ')}`;
            } else {
                msg = 'Clips added to playlist.';
            }
            // Show persistent toast (longer duration)
            showToast(msg);
            // Highlight affected clips
            setTimeout(() => {
                summary.clipIds.forEach(id => {
                    const card = document.querySelector(`.card[data-clip-id='${id}']`);
                    if (card) {
                        card.classList.add('playlist-added-highlight');
                        setTimeout(() => card.classList.remove('playlist-added-highlight'), 3500);
                    }
                });
            }, 400); // Wait for grid to render
        } catch {}
    }
});

/* Add this CSS to your style.css for the highlight effect:
.playlist-added-highlight {
    box-shadow: 0 0 0 4px #3fa7ffcc, 0 2px 12px #000a;
    background: #1a6fff22 !important;
    transition: box-shadow 0.3s, background 0.3s;
}
*/

// --- PATCH: Add support for removing a clip from a playlist directly from the grid ---
function attachPlaylistPillRemoveHandlers() {
    document.querySelectorAll('.playlist-pill[data-clip-id][data-playlist-id] .playlist-pill-remove').forEach(btn => {
        btn.onclick = function(e) {
            e.stopPropagation();
            const clipId = btn.closest('.playlist-pill').getAttribute('data-clip-id');
            const playlistId = btn.closest('.playlist-pill').getAttribute('data-playlist-id');
            if (!clipId || !playlistId) return;
            fetch('/playlists/clips/remove', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({clip_ids: [Number(clipId)], playlist_id: Number(playlistId)})
            })
            .then(resp => resp.json())
            .then(data => {
                if (data && !data.error) {
                    // Remove the pill from the UI
                    btn.closest('.playlist-pill').remove();
                    showToast('Removed from playlist.');
                } else {
                    showToast('Failed to remove from playlist.', true);
                }
            })
            .catch(() => showToast('Remove from playlist error.', true));
        };
    });
} 