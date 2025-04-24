// LoopSleuth: Shared JS for starring and tag editing (grid & detail views)
// All actions use data-clip-id attributes for robust event handling.

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
    document.getElementById(`tags-text-${clipId}`).style.display = 'none';
    document.getElementById(`tag-input-${clipId}`).style.display = '';
    document.getElementById(`save-tag-btn-${clipId}`).style.display = '';
    document.getElementById(`tag-input-${clipId}`).focus();
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
    // Parse comma-separated input into array
    const tags = input.value.split(',').map(t => t.trim()).filter(t => t.length > 0);
    fetch(`/tag/${clipId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({tags})
    })
    .then(r => r.json())
    .then(data => {
        if (data.tags !== undefined) {
            renderTagChips(clipId, data.tags);
        }
        document.getElementById(`tags-text-${clipId}`).style.display = '';
        input.style.display = 'none';
        document.getElementById(`save-tag-btn-${clipId}`).style.display = 'none';
    });
} 