// Token page JavaScript functionality

function toggleSection(button) {
    const content = button.closest('section').querySelector('.collapsible-content');
    const toggleText = button.querySelector('.toggle-text');
    const toggleIcon = button.querySelector('.toggle-icon');
    const isExpanded = button.getAttribute('aria-expanded') === 'true';

    if (isExpanded) {
        content.style.display = 'none';
        toggleText.textContent = 'Show Sources';
        button.setAttribute('aria-expanded', 'false');
        toggleIcon.style.transform = 'rotate(0deg)';
    } else {
        content.style.display = 'block';
        toggleText.textContent = 'Hide Sources';
        button.setAttribute('aria-expanded', 'true');
        toggleIcon.style.transform = 'rotate(180deg)';
    }
}

// Copy to clipboard functionality for token pages
function copyToClipboard(text, button) {
    navigator.clipboard.writeText(text).then(function() {
        // Visual feedback
        const originalText = button.innerHTML;
        button.classList.add('copied');
        button.innerHTML = button.innerHTML.replace(/CSS|Class/, 'Copied!');

        setTimeout(function() {
            button.classList.remove('copied');
            button.innerHTML = originalText;
        }, 2000);
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}