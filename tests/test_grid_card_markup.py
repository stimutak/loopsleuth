import re
import pytest

@pytest.fixture(scope="module")
def render_clip_card_html():
    # Simulate the JS template literal output for renderClipCard
    def render_clip_card(clip):
        tags_html = (
            ''.join(f'<span class="tag-chip">{tag}</span>' for tag in clip.get('tags', []))
            if clip.get('tags') else '<span class="tag-chip tag-empty">No tags</span>'
        )
        duration_html = f'<div class="duration">{(clip["duration"]//60)}:{str(clip["duration"]%60).zfill(2)} min</div>' if clip.get('duration') is not None else ''
        size_html = f'<div class="size">{clip["size"]}</div>' if clip.get('size') else ''
        modified_html = f'<div class="modified">{clip["modified_at"][:10]} {clip["modified_at"][11:16]}</div>' if clip.get('modified_at') else ''
        return f'''
        <div class="card" data-clip-id="{clip['id']}" data-path="{clip['path'].replace(' ', '%20')}">
            <label class="custom-checkbox-label">
                <input type="checkbox" class="select-clip-checkbox" aria-label="Select clip {clip['filename']}" />
                <span class="custom-checkbox"></span>
            </label>
            <a class="card-link" href="/clip/{clip['id']}">
                <img class="thumb" src="{clip['thumb_url']}" alt="Thumbnail for {clip['filename']}" />
            </a>
            <div class="meta">
                <a class="card-link" href="/clip/{clip['id']}">
                    <div class="filename">{clip['filename']}</div>
                </a>
                {duration_html}
                {size_html}
                {modified_html}
                <div class="star" style="cursor:pointer;" data-clip-id="{clip['id']}" title="Toggle star">{'★' if clip.get('starred') else '☆'}</div>
                <button class="pip-btn" data-clip-id="{clip['id']}" title="Picture-in-Picture preview">⧉ PiP</button>
                <video id="pip-video-{clip['id']}" src="/media/{clip['path'].replace(' ', '%20')}" style="display:none;" muted playsinline></video>
                <div class="tags">
                    <span class="tags-text" id="tags-text-{clip['id']}">{tags_html}</span>
                    <a href="/clip/{clip['id']}" class="edit-tag-btn-link" style="margin-left:0.5em; font-size:0.9em; text-decoration:none;" title="Edit tags in detail view">✎</a>
                </div>
            </div>
        </div>
        '''
    return render_clip_card

def test_render_clip_card_markup_all_fields(render_clip_card_html):
    clip = {
        'id': 123,
        'filename': 'test.mp4',
        'thumb_url': '/static/test.jpg',
        'path': 'E:/media/test.mp4',
        'duration': 95,
        'size': '12 MB',
        'modified_at': '2024-06-15T12:34:56',
        'starred': True,
        'tags': ['loop', 'vibe']
    }
    html = render_clip_card_html(clip)
    assert 'select-clip-checkbox' in html
    assert 'pip-btn' in html
    assert 'tag-chip' in html
    assert 'card-link' in html
    assert 'data-path' in html
    assert 'test.mp4' in html
    assert '12 MB' in html
    assert '2024-06-15' in html
    assert '★' in html
    assert 'loop' in html and 'vibe' in html
    assert '<div class="duration">1:35 min</div>' in html
    assert '<div class="size">12 MB</div>' in html
    assert '<div class="modified">2024-06-15 12:34</div>' in html

def test_render_clip_card_markup_no_tags(render_clip_card_html):
    clip = {
        'id': 124,
        'filename': 'no_tags.mp4',
        'thumb_url': '/static/no_tags.jpg',
        'path': 'E:/media/no_tags.mp4',
        'duration': 60,
        'size': '8 MB',
        'modified_at': '2024-06-16T10:00:00',
        'starred': False,
        'tags': []
    }
    html = render_clip_card_html(clip)
    assert 'tag-chip tag-empty' in html
    assert 'No tags' in html
    assert '☆' in html

def test_render_clip_card_markup_missing_fields(render_clip_card_html):
    clip = {
        'id': 125,
        'filename': 'missing_fields.mp4',
        'thumb_url': '/static/missing.jpg',
        'path': 'E:/media/missing fields.mp4',  # test path with space
        # duration, size, modified_at omitted
        'starred': False,
        'tags': None
    }
    html = render_clip_card_html(clip)
    assert 'select-clip-checkbox' in html
    assert 'pip-btn' in html
    assert 'card-link' in html
    assert 'data-path="E:/media/missing%20fields.mp4"' in html
    assert 'missing_fields.mp4' in html
    assert '☆' in html
    assert 'tag-chip tag-empty' in html
    assert 'No tags' in html
    assert '<div class="duration">' not in html
    assert '<div class="size">' not in html
    assert '<div class="modified">' not in html

def test_render_clip_card_markup_empty_tags_array(render_clip_card_html):
    clip = {
        'id': 126,
        'filename': 'empty_tags.mp4',
        'thumb_url': '/static/empty.jpg',
        'path': 'E:/media/empty_tags.mp4',
        'duration': 30,
        'size': '2 MB',
        'modified_at': '2024-06-17T09:00:00',
        'starred': True,
        'tags': []
    }
    html = render_clip_card_html(clip)
    assert 'tag-chip tag-empty' in html
    assert 'No tags' in html
    assert '★' in html
    assert 'empty_tags.mp4' in html

def test_render_clip_card_markup(render_clip_card_html):
    clip = {
        'id': 123,
        'filename': 'test.mp4',
        'thumb_url': '/static/test.jpg',
        'path': 'E:/media/test.mp4',
        'duration': 95,
        'size': '12 MB',
        'modified_at': '2024-06-15T12:34:56',
        'starred': True,
        'tags': ['loop', 'vibe']
    }
    html = render_clip_card_html(clip)
    # Check for all required elements
    assert 'select-clip-checkbox' in html
    assert 'pip-btn' in html
    assert 'tag-chip' in html
    assert 'card-link' in html
    assert 'data-path' in html
    assert 'test.mp4' in html
    assert '12 MB' in html
    assert '2024-06-15' in html
    assert '★' in html or '☆' in html
    assert 'loop' in html and 'vibe' in html 