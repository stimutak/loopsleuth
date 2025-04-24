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

function editTags(event) {
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    // Get initial tags from static chips
    const staticChips = document.querySelectorAll(`#tags-text-${clipId} .tag-chip:not(.tag-empty)`);
    const tagsArr = Array.from(staticChips).map(chip => chip.textContent.trim());
    editTagsState[clipId] = [...tagsArr];
    originalTagsState[clipId] = [...tagsArr]; // Store for cancel
    // Hide static chips, show edit mode
    document.getElementById(`tags-text-${clipId}`).style.display = 'none';
    document.getElementById(`tags-edit-${clipId}`).style.display = 'inline-block';
    document.getElementById(`tag-input-new-${clipId}`).style.display = 'inline-block';
    document.getElementById(`save-tag-btn-${clipId}`).style.display = 'inline-block';
    let cancelBtn = document.getElementById(`cancel-tag-btn-${clipId}`);
    if (cancelBtn) cancelBtn.style.display = 'inline-block';
    renderEditableTagChips(clipId);
    const input = document.getElementById(`tag-input-new-${clipId}`);
    input.value = '';
    input.focus();
    // Remove previous listeners
    input.oninput = null;
    input.onkeydown = null;
    input.addEventListener('input', () => showTagSuggestionsStandard(input, clipId));
    input.addEventListener('keydown', function(e) {
        const suggestions = input._suggestions || [];
        let highlighted = typeof input._highlighted === 'number' ? input._highlighted : -1;
        const dropdown = document.getElementById('tag-suggestions-dropdown');
        // --- 1. Escape closes dropdown, not edit mode ---
        if (e.key === 'Escape') {
            if (dropdown && dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
                input._suggestions = [];
                input._highlighted = -1;
                e.preventDefault();
                return;
            } else {
                // Save tags and exit edit mode (same as clicking Save)
                saveTags({target: {getAttribute: () => clipId}, preventDefault: () => {}, stopPropagation: () => {}});
                return;
            }
        }
        // --- 2. Backspace in empty input removes last tag chip ---
        if (e.key === 'Backspace' && input.value === '') {
            let tags = editTagsState[clipId] || [];
            if (tags.length > 0) {
                tags.pop();
                editTagsState[clipId] = tags;
                renderEditableTagChips(clipId);
                e.preventDefault();
                return;
            }
        }
        if (e.key === 'ArrowDown') {
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
                // Save tags and exit edit mode (same as clicking Save)
                saveTags({target: {getAttribute: () => clipId}, preventDefault: () => {}, stopPropagation: () => {}});
            }
        }
    }, {capture: true});
    // --- 3. Clicking outside tag editor saves and exits ---
    document.addEventListener('mousedown', handleOutsideClick, true);
}

function cancelEditTags(event) {
    const clipId = event.target.getAttribute('data-clip-id');
    // Restore static chips to original tags
    renderTagChips(clipId, originalTagsState[clipId] || []);
    document.getElementById(`tags-text-${clipId}`).style.display = '';
    document.getElementById(`tags-edit-${clipId}`).style.display = 'none';
    document.getElementById(`tag-input-new-${clipId}`).style.display = 'none';
    document.getElementById(`save-tag-btn-${clipId}`).style.display = 'none';
    let cancelBtn = document.getElementById(`cancel-tag-btn-${clipId}`);
    if (cancelBtn) cancelBtn.style.display = 'none';
}

function renderEditableTagChips(clipId) {
    const tagsEdit = document.getElementById(`tags-edit-${clipId}`);
    const tags = editTagsState[clipId] || [];
    tagsEdit.innerHTML = '';
    tagsEdit.setAttribute('role', 'list'); // ARIA: tag chip list
    if (tags.length === 0) {
        tagsEdit.innerHTML = '<span class="tag-chip tag-empty">No tags</span>';
    } else {
        tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip tag-edit';
            chip.setAttribute('role', 'listitem'); // ARIA: tag chip item
            chip.setAttribute('aria-label', `Tag: ${tag}`);
            chip.appendChild(document.createTextNode(tag));
            const x = document.createElement('span');
            x.className = 'tag-chip-x';
            x.textContent = '×';
            x.setAttribute('aria-label', `Remove tag ${tag}`);
            x.onclick = () => {
                editTagsState[clipId] = editTagsState[clipId].filter(t => t !== tag);
                renderEditableTagChips(clipId);
            };
            chip.appendChild(x);
            tagsEdit.appendChild(chip);
        });
    }
}

// --- Enhanced Autocomplete UX ---
function showTagSuggestionsStandard(input, clipId) {
    let dropdown = document.getElementById('tag-suggestions-dropdown');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.id = 'tag-suggestions-dropdown';
        dropdown.className = 'tag-suggestions-dropdown';
        // --- ARIA: dropdown as listbox ---
        dropdown.setAttribute('role', 'listbox');
        document.body.appendChild(dropdown);
    }
    const rect = input.getBoundingClientRect();
    dropdown.style.position = 'absolute';
    dropdown.style.left = `${rect.left + window.scrollX}px`;
    dropdown.style.top = `${rect.bottom + window.scrollY}px`;
    dropdown.style.width = `${rect.width}px`;
    dropdown.innerHTML = '';
    // --- ARIA: input attributes ---
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', dropdown.style.display === 'block' ? 'true' : 'false');
    input.setAttribute('aria-controls', 'tag-suggestions-dropdown');
    input.setAttribute('aria-activedescendant', '');
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
                // --- ARIA: suggestion as option ---
                item.setAttribute('role', 'option');
                item.setAttribute('id', `tag-suggestion-${clipId}-${idx}`);
                item.setAttribute('aria-selected', input._highlighted === idx ? 'true' : 'false');
                if (input._highlighted === idx) {
                    item.style.background = '#2a3a3a';
                    item.style.color = '#fff';
                    // --- Scroll highlighted into view ---
                    setTimeout(() => { item.scrollIntoView({block: 'nearest'}); }, 0);
                    // --- ARIA: active descendant ---
                    input.setAttribute('aria-activedescendant', item.id);
                }
                item.onmouseenter = () => {
                    input._highlighted = idx;
                    showTagSuggestionsStandard(input, clipId);
                };
                // Use mousedown instead of click to prevent input blur before selection
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
    // Prevent duplicates (case-insensitive)
    const tags = editTagsState[clipId] || [];
    if (!tags.map(t => t.toLowerCase()).includes(tag.toLowerCase())) {
        editTagsState[clipId].push(tag);
        renderEditableTagChips(clipId);
    }
    input.value = '';
    input._highlighted = -1;
    showTagSuggestionsStandard(input, clipId);
}

function saveTags(event) {
    event.preventDefault();
    event.stopPropagation();
    const clipId = event.target.getAttribute('data-clip-id');
    const input = document.getElementById(`tag-input-new-${clipId}`);
    let tags = editTagsState[clipId] || [];
    // If input is non-empty and not a duplicate, add it as a tag
    const inputVal = input.value.trim();
    if (inputVal && !tags.map(t => t.toLowerCase()).includes(inputVal.toLowerCase())) {
        tags.push(inputVal);
        editTagsState[clipId] = tags;
        renderEditableTagChips(clipId);
        input.value = '';
    }
    // Now send tags to backend
    fetch(`/tag/${clipId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tags: tags})
    })
    .then(r => r.json())
    .then(data => {
        if (data.tags !== undefined) {
            renderTagChips(clipId, data.tags);
            originalTagsState[clipId] = [...data.tags]; // Update original tags after save
        } else if (data.error) {
            alert('Error saving tags: ' + data.error);
        }
        // Hide edit mode, show static chips
        document.getElementById(`tags-text-${clipId}`).style.display = '';
        document.getElementById(`tags-edit-${clipId}`).style.display = 'none';
        document.getElementById(`tag-input-new-${clipId}`).style.display = 'none';
        document.getElementById(`save-tag-btn-${clipId}`).style.display = 'none';
        let cancelBtn = document.getElementById(`cancel-tag-btn-${clipId}`);
        if (cancelBtn) cancelBtn.style.display = 'none';
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
            chip.appendChild(document.createTextNode(tag));
            // Add X for deletion (only in edit mode, not static view)
            tagsText.appendChild(chip);
        });
    }
}

// --- Keyboard accessibility for tag editing (grid and detail views) ---

// Batch selection: checkbox and card click
const selectedClipIds = new Set();
let lastSelectedIndex = null;

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
            <input type="text" class="batch-bar-input" id="batch-add-tags" placeholder="Add tag(s)..." autocomplete="off" />
            <button class="batch-bar-btn" id="batch-add-btn">Add</button>
        </div>
        <div class="batch-bar-section">
            <span class="batch-bar-label">Remove tags:</span>
            <input type="text" class="batch-bar-input" id="batch-remove-tags" placeholder="Remove tag(s)..." autocomplete="off" />
            <button class="batch-bar-btn" id="batch-remove-btn">Remove</button>
        </div>
        <div class="batch-bar-section">
            <button class="batch-bar-btn" id="batch-clear-btn">Clear all tags</button>
        </div>
        <span class="batch-bar-help" title="Shift+Click: range select, Ctrl/Cmd+Click: multi-select. Add/Remove tags for all selected clips.">?</span>
    `;
    console.log('[BatchBar] Rendered batch bar with controls');
    // Wire up events (backend integration next)
    document.getElementById('batch-add-btn').onclick = () => {
        alert('Batch add tags: ' + document.getElementById('batch-add-tags').value);
    };
    document.getElementById('batch-remove-btn').onclick = () => {
        alert('Batch remove tags: ' + document.getElementById('batch-remove-tags').value);
    };
    document.getElementById('batch-clear-btn').onclick = () => {
        alert('Batch clear all tags for selected');
    };

    // --- Batch Tag Autocomplete Logic ---
    // Attach autocomplete to both batch tag inputs
    attachBatchTagAutocomplete(document.getElementById('batch-add-tags'));
    attachBatchTagAutocomplete(document.getElementById('batch-remove-tags'));
}

/**
 * Attach autocomplete dropdown to a batch tag input field.
 * Suggestions are fetched from /tags?q= and inserted as comma-separated tags.
 */
function attachBatchTagAutocomplete(input) {
    if (!input) return;
    input.addEventListener('input', function() {
        const inputVal = input.value.split(',').pop().trim().toLowerCase();
        let dropdown = document.getElementById('batch-tag-suggestions-dropdown');
        if (!dropdown) {
            dropdown = document.createElement('div');
            dropdown.id = 'batch-tag-suggestions-dropdown';
            dropdown.className = 'tag-suggestions-dropdown';
            document.body.appendChild(dropdown);
        }
        const rect = input.getBoundingClientRect();
        dropdown.style.position = 'absolute';
        dropdown.style.left = `${rect.left + window.scrollX}px`;
        dropdown.style.top = `${rect.bottom + window.scrollY}px`;
        dropdown.style.width = `${rect.width}px`;
        dropdown.innerHTML = '';
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
                // Filter out tags already present in the input (case-insensitive)
                const present = input.value.split(',').map(t => t.trim().toLowerCase());
                const filtered = data.tags.filter(tag => !present.includes(tag.toLowerCase()));
                if (filtered.length === 0) {
                    dropdown.style.display = 'none';
                    return;
                }
                filtered.forEach(tag => {
                    const item = document.createElement('div');
                    item.className = 'tag-suggestion-item';
                    item.textContent = tag;
                    item.onmousedown = (e) => {
                        e.preventDefault();
                        // Insert tag as comma-separated value
                        let tags = input.value.split(',').map(t => t.trim()).filter(t => t.length > 0);
                        // Replace last (possibly partial) tag with selected
                        if (tags.length === 0) {
                            tags = [tag];
                        } else {
                            tags[tags.length - 1] = tag;
                        }
                        // Remove duplicates
                        tags = tags.filter((t, i) => tags.indexOf(t) === i);
                        input.value = tags.join(', ') + ', ';
                        input.focus();
                        dropdown.style.display = 'none';
                    };
                    dropdown.appendChild(item);
                });
                dropdown.style.display = 'block';
            });
    });
    // Hide dropdown on blur
    input.addEventListener('blur', function() {
        setTimeout(() => {
            let dropdown = document.getElementById('batch-tag-suggestions-dropdown');
            if (dropdown) dropdown.style.display = 'none';
        }, 120);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Make all grid cards focusable and add keyboard listeners
    const cards = document.querySelectorAll('.card[data-clip-id]');
    cards.forEach(card => {
        card.setAttribute('tabindex', '0');
        card.addEventListener('keydown', function(e) {
            // Only trigger if not typing in an input/textarea/contenteditable
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName) || e.target.isContentEditable) return;
            if (e.key === 'e' || e.key === 'Enter') {
                const editBtn = card.querySelector('.edit-tag-btn');
                if (editBtn) {
                    editBtn.click();
                    setTimeout(() => {
                        const clipId = card.getAttribute('data-clip-id');
                        const input = document.getElementById(`tag-input-new-${clipId}`);
                        if (input) input.focus();
                    }, 10);
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
    }

    document.querySelectorAll('.card[data-clip-id]').forEach((card, idx, allCards) => {
        const clipId = card.getAttribute('data-clip-id');
        const checkbox = card.querySelector('.select-clip-checkbox');
        // Checkbox click
        checkbox.addEventListener('click', function(e) {
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