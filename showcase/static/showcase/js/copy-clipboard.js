/**
 * Copy to clipboard functionality for the showcase
 */

function copyToClipboard(text, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    navigator.clipboard.writeText(text).then(function() {
        // Show feedback
        showCopyFeedback(event ? event.target : null, '✅ Copied!');
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
        showCopyFeedback(event ? event.target : null, '❌ Failed');
    });
}

function copyComponentSyntax(componentName, event) {
    const htmlSyntax = `<include:${componentName}>`;
    copyToClipboard(htmlSyntax, event);
}

function copyComponentTemplateSyntax(componentName, props, event) {
    let templateSyntax = `{% includecontents "${componentName}"`;

    if (props && Object.keys(props).length > 0) {
        templateSyntax += ' with';
        for (const [key, value] of Object.entries(props)) {
            templateSyntax += ` ${key}="${value}"`;
        }
    }

    templateSyntax += ' %}{% endincludecontents %}';

    copyToClipboard(templateSyntax, event);
}

function copyTokenCSSVar(tokenPath, event) {
    const cssVar = `var(--${tokenPath.replace(/\./g, '-')})`;
    copyToClipboard(cssVar, event);
}

function copyFromElement(elementId, event) {
    const element = document.getElementById(elementId);
    if (element) {
        copyToClipboard(element.textContent, event);
    }
}

function showCopyFeedback(button, message) {
    if (!button) return;

    const originalText = button.textContent;
    const originalBackground = button.style.background;

    button.textContent = message;
    button.style.background = message.includes('✅') ? '#10b981' : '#ef4444';
    button.disabled = true;

    setTimeout(() => {
        button.textContent = originalText;
        button.style.background = originalBackground;
        button.disabled = false;
    }, 1500);
}

// Initialize copy buttons when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers to copy buttons
    document.querySelectorAll('[data-copy]').forEach(button => {
        button.addEventListener('click', function(event) {
            const textToCopy = this.getAttribute('data-copy');
            copyToClipboard(textToCopy, event);
        });
    });

    // Add copy functionality to code blocks
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.className = 'copy-code-btn';
        button.textContent = '📋 Copy';
        button.title = 'Copy code';

        button.addEventListener('click', function(event) {
            copyToClipboard(block.textContent, event);
        });

        const container = block.parentElement;
        container.style.position = 'relative';
        container.appendChild(button);
    });
});