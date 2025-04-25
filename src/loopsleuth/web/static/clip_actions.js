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

// --- Per-clip tag editing functions removed: now handled only in detail view or via batch bar ---
// The following functions were removed as per-clip tag editing is no longer available in the grid view:
// - editTags
// - cancelEditTags
// - renderEditableTagChips
// - showTagSuggestionsStandard
// - addTagFromAutocomplete
// - saveTags
//
// Batch bar and detail view tag editing logic remain below.

// --- Batch Tag Input State ---
const batchAddTagsState = [];
const batchRemoveTagsState = [];

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
                tags.splice(idx, 1);
                renderBatchTagChips(type);
                // Debug: log chip removal
                if (type === 'add') console.log('[BatchAdd] chip removed:', tag, 'tags:', tags);
            };
            chip.appendChild(x);
            container.appendChild(chip);
        });
    }
    // Enable/disable Add button based on chip count
    if (type === 'add') {
        const addBtn = document.getElementById('batch-add-btn');
        if (addBtn) addBtn.disabled = tags.length === 0;
    }
}

function handleBatchTagInput(type) {
    const input = document.getElementById(`batch-${type}-tags-input`);
    const tags = type === 'add' ? batchAddTagsState : batchRemoveTagsState;
    input.addEventListener('keydown', function(e) {
        // Debug: log key events
        if (type === 'add') console.log('[BatchAdd] keydown:', e.key, 'input:', input.value, 'tags:', tags);
        if (e.key === 'Backspace' && input.value === '') {
            if (tags.length > 0) {
                tags.pop();
                renderBatchTagChips(type);
                e.preventDefault();
                return;
            }
        }
        // Keyboard navigation for autocomplete
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
        } else if (e.key === 'Tab') {
            if (suggestions.length > 0 && highlighted >= 0) {
                e.preventDefault();
                addBatchTagFromAutocomplete(input, type, suggestions[highlighted]);
                return;
            }
        } else if (e.key === 'Enter') {
            if (suggestions.length > 0 && highlighted >= 0) {
                e.preventDefault();
                addBatchTagFromAutocomplete(input, type, suggestions[highlighted]);
                return;
            } else {
                // Add tag from input if not empty and not duplicate
                const val = input.value.trim();
                if (val && !tags.map(t => t.toLowerCase()).includes(val.toLowerCase())) {
                    tags.push(val);
                    renderBatchTagChips(type);
                    input.value = '';
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
    });
    // Prevent dropdown from hiding on blur if a suggestion is being clicked
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
        renderBatchTagChips(type);
    }
    input.value = '';
    input._highlighted = -1;
    showBatchTagSuggestions(input, type);
    if (type === 'add') console.log('[BatchAdd] tag added from autocomplete:', tag, 'tags:', tags);
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
    console.log('[BatchBar] renderBatchActionBar called. Bar:', bar);
    if (!bar) {
        console.error('[BatchBar] #batch-action-bar not found in DOM');
        return;
    }
    console.log('[BatchBar] selectedClipIds:', Array.from(selectedClipIds));
    if (selectedClipIds.size === 0) {
        bar.style.display = 'none';
        bar.innerHTML = '';
        console.log('[BatchBar] No selection, hiding bar');
        return;
    }
    // --- Batch bar UI ---
    bar.style.display = '';
    bar.innerHTML = `
        <div class="batch-bar-section">
            <span class="batch-bar-label">${selectedClipIds.size} selected</span>
        </div>
        <div class="batch-bar-section">
            <span class="batch-bar-label">Add tags:</span>
            <span id="batch-add-tags-chips" class="tags-edit" style="display:inline-block;"></span>
            <input type="text" class="batch-bar-input" id="batch-add-tags-input" placeholder="Add tag..." autocomplete="off" style="width:160px; margin-top:0.3em; display:inline-block;" />
            <button class="batch-bar-btn" id="batch-add-btn">Add</button>
        </div>
        <div class="batch-bar-section">
            <span class="batch-bar-label">Remove tags:</span>
            <span id="batch-remove-tags-chips" class="tags-edit" style="display:inline-block;"></span>
            <input type="text" class="batch-bar-input" id="batch-remove-tags-input" placeholder="Remove tag..." autocomplete="off" style="width:160px; margin-top:0.3em; display:inline-block;" />
            <button class="batch-bar-btn" id="batch-remove-btn">Remove</button>
        </div>
        <div class="batch-bar-section">
            <button class="batch-bar-btn" id="batch-clear-btn">Clear all tags</button>
        </div>
        <span class="batch-bar-help" title="Shift+Click: range select, Ctrl/Cmd+Click: multi-select. Add/Remove tags for all selected clips.">?</span>
    `;
    renderBatchTagChips('add');
    renderBatchTagChips('remove');
    handleBatchTagInput('add');
    handleBatchTagInput('remove');
    // Wire up events (backend integration next)
    document.getElementById('batch-add-btn').onclick = (e) => {
        e.preventDefault(); // Prevent accidental form submission
        // Debug: log state before check
        console.log('[BatchAdd] Add button clicked. Current tags:', batchAddTagsState);
        if (batchAddTagsState.length === 0) {
            showToast('Enter tag(s) to add.', true);
            return;
        }
        const clipIds = Array.from(selectedClipIds).map(Number);
        console.log('[BatchAdd] Sending to backend:', {clip_ids: clipIds, add_tags: batchAddTagsState});
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
            for (const [clipId, tags] of Object.entries(data)) {
                renderTagChips(clipId, tags);
            }
            showToast('Tags added to selected clips.');
            batchAddTagsState.length = 0;
            renderBatchTagChips('add');
            document.getElementById('batch-add-tags-input').value = '';
            console.log('[BatchAdd] Success, cleared chips/input.');
        })
        .catch(err => {
            showToast('Batch add error: ' + err, true);
            console.error('[BatchAdd] Error:', err);
        });
    };
    document.getElementById('batch-remove-btn').onclick = () => {
        if (batchRemoveTagsState.length === 0) {
            showToast('Enter tag(s) to remove.', true);
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
            for (const [clipId, tags] of Object.entries(data)) {
                renderTagChips(clipId, tags);
            }
            showToast('Tags removed from selected clips.');
            batchRemoveTagsState.length = 0;
            renderBatchTagChips('remove');
            document.getElementById('batch-remove-tags-input').value = '';
        })
        .catch(err => {
            showToast('Batch remove error: ' + err, true);
        });
    };
    document.getElementById('batch-clear-btn').onclick = () => {
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
            for (const [clipId, tags] of Object.entries(data)) {
                renderTagChips(clipId, tags);
            }
            showToast('All tags cleared from selected clips.');
        })
        .catch(err => {
            showToast('Batch clear error: ' + err, true);
        });
    };
}

function updateCardSelectionUI() {
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
}

// --- Batch selection: checkbox and card click
const selectedClipIds = new Set();
let lastSelectedIndex = null;

document.addEventListener('DOMContentLoaded', function() {
    // Make all grid cards focusable and add keyboard listeners
    const cards = document.querySelectorAll('.card[data-clip-id]');
    cards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', function(e) {
            // Only trigger if not typing in an input/textarea/contenteditable
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) return;
            if (e.key === 'e' || e.key === 'Enter') {
                const editLink = card.querySelector('.edit-tag-btn-link');
                if (editLink) {
                    // Navigate to detail view for tag editing
                    window.location.href = editLink.href;
                    e.preventDefault();
                }
            }
        });
    });
    // Make tag section in detail view focusable and keyboard accessible
    const tagSections = document.querySelectorAll('.meta .tags');
    tagSections.forEach(section => {
        section.setAttribute('tabindex', '0');
        section.addEventListener('keydown', function(e) {
            // Only trigger if not typing in an input/textarea/contenteditable
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) return;
            if (e.key === 'e' || e.key === 'Enter') {
                const editBtn = section.querySelector('.edit-tag-btn');
                if (editBtn) {
                    editBtn.click();
                    setTimeout(() => {
                        const clipId = editBtn.getAttribute('data-clip-id');
                        const input = document.getElementById(`tag-input-new-${clipId}`);
                        if (input) input.focus();
                    }, 10);
                    e.preventDefault();
                }
            }
        });
    });

    function getCardElements() {
        return Array.from(document.querySelectorAll('.card[data-clip-id]'));
    }

    document.querySelectorAll('.card[data-clip-id]').forEach((card, idx, allCards) => {
        const clipId = card.getAttribute('data-clip-id');
        const checkbox = card.querySelector('.select-clip-checkbox');
        // Checkbox click
        checkbox.addEventListener('click', function(e) {
            console.log('[DEBUG] Checkbox clicked for clip', clipId, 'checked:', checkbox.checked);
            e.stopPropagation();
            // FIX: Always toggle only this card, never clear others
            if (checkbox.checked) {
                selectedClipIds.add(clipId);
            } else {
                selectedClipIds.delete(clipId);
            }
            lastSelectedIndex = idx;
            updateCardSelectionUI();
        });
        // Card click (not on links/buttons/inputs)
        card.addEventListener('click', function(e) {
            if (e.target.closest('a,button,input')) return;
            console.log('[DEBUG] Card clicked for clip', clipId);
            const isCtrl = e.ctrlKey || e.metaKey;
            const isShift = e.shiftKey;
            if (isShift && lastSelectedIndex !== null) {
                // Range select
                const cards = getCardElements();
                const thisIndex = cards.indexOf(card);
                const [start, end] = [lastSelectedIndex, thisIndex].sort((a, b) => a - b);
                for (let i = start; i <= end; i++) {
                    selectedClipIds.add(cards[i].getAttribute('data-clip-id'));
                }
            } else if (isCtrl) {
                // Toggle only this
                if (selectedClipIds.has(clipId)) {
                    selectedClipIds.delete(clipId);
                } else {
                    selectedClipIds.add(clipId);
                }
                lastSelectedIndex = idx;
            } else {
                // Normal click: select only this if not already selected
                if (!selectedClipIds.has(clipId)) {
                    selectedClipIds.clear();
                    selectedClipIds.add(clipId);
                } else {
                    selectedClipIds.delete(clipId);
                }
                lastSelectedIndex = idx;
            }
            updateCardSelectionUI();
        });
    });
    updateCardSelectionUI();

    // Minimal test: force batch bar to show TEST
    // const bar = document.getElementById('batch-action-bar');
    // if (bar) {
    //     bar.innerHTML = 'TEST';
    //     bar.style.display = 'block';
    //     console.log('[BatchBar] TEST: Bar found and set to TEST');
    // } else {
    //     console.error('[BatchBar] TEST: #batch-action-bar not found in DOM');
    // }
}); 