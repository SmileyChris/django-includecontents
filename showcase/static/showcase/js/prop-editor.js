/**
 * Interactive prop editor for component showcase
 */

(function() {
    'use strict';

    let latestPreviewHtml = '';

    /**
     * Get CSRF token from cookie
     */
    function getCsrfToken() {
        const name = 'csrftoken=';
        const decodedCookies = decodeURIComponent(document.cookie || '');
        const cookies = decodedCookies.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name)) {
                return cookie.slice(name.length);
            }
        }
        return '';
    }

    // Wait for DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        // Check if this component has a showcase template
        if (hasShowcaseTemplate()) {
            initShowcasePreview();
        } else {
            initPropEditor();
        }
        initPreviewControls();
        initCodeTabs();
        // Copy buttons are now handled by copy-clipboard.js
        initExampleLoaders();
    });

    /**
     * Check if this component has a showcase template
     */
    function hasShowcaseTemplate() {
        return document.querySelector('.showcase-indicator') !== null;
    }

    /**
     * Initialize showcase preview for components with showcase templates
     */
    function initShowcasePreview() {
        // Load the showcase template immediately
        loadShowcaseTemplate();
    }

    /**
     * Load showcase template content
     */
    function loadShowcaseTemplate() {
        const iframePreviewUrl = `/showcase/${componentData.category}/${componentData.slug}/iframe-preview/`;
        const ajaxPreviewUrl = `/showcase/${componentData.category}/${componentData.slug}/preview/`;

        // Create a form and submit to iframe for showcase preview
        const iframe = document.getElementById('component-preview-iframe');
        if (!iframe) {
            return;
        }

        const form = document.createElement('form');
        form.method = 'POST';
        form.action = iframePreviewUrl;
        form.target = 'component-preview-iframe';
        form.style.display = 'none';

        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = getCsrfToken();
        form.appendChild(csrfInput);

        // Add empty data for showcase template
        const dataInput = document.createElement('input');
        dataInput.type = 'hidden';
        dataInput.name = 'data';
        dataInput.value = JSON.stringify({
            props: {},
            content: '',
            content_blocks: {}
        });
        form.appendChild(dataInput);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

        // Also get the HTML for the HTML preview mode
        fetch(ajaxPreviewUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                props: {},
                content: '',
                content_blocks: {}
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Preview error:', data.error);
            } else {
                updatePreviewHTML(data.html);
            }
        })
        .catch(error => {
            console.error('Preview error:', error);
        });
    }

    /**
     * Initialize the prop editor form
     */
    function initPropEditor() {
        const form = document.getElementById('prop-editor-form');
        if (!form) return;

        // Get all prop inputs
        const propInputs = form.querySelectorAll('[data-prop]');
        const contentInput = document.getElementById('content-input');
        const contentBlocks = form.querySelectorAll('.content-block');

        // Function to update preview
        const updatePreview = debounce(function() {
            const props = {};

            // Collect prop values
            propInputs.forEach(input => {
                const propName = input.dataset.prop;
                if (input.type === 'checkbox') {
                    props[propName] = input.checked;
                } else if (input.type === 'number') {
                    props[propName] = parseInt(input.value) || 0;
                } else {
                    props[propName] = input.value;
                }
            });

            // Collect content
            const content = contentInput ? contentInput.value : '';

            // Collect content blocks
            const blocks = {};
            contentBlocks.forEach(block => {
                const blockName = block.dataset.block;
                blocks[blockName] = block.value;
            });

            const missingRequired = Array.from(propInputs).filter(input => {
                if (input.dataset.required !== 'true') {
                    return false;
                }
                if (input.type === 'checkbox') {
                    return !input.checked;
                }
                if (input.type === 'number') {
                    return input.value === '' || isNaN(Number(input.value));
                }
                return !input.value || input.value.trim() === '';
            });

            if (missingRequired.length) {
                showError('Please complete all required props to preview this component.');
                return;
            }

            // Send preview request
            sendPreviewRequest(props, content, blocks);
        }, 300);

        // Add event listeners
        propInputs.forEach(input => {
            input.addEventListener('change', updatePreview);
            input.addEventListener('input', updatePreview);
        });

        if (contentInput) {
            contentInput.addEventListener('input', updatePreview);
        }

        contentBlocks.forEach(block => {
            block.addEventListener('input', updatePreview);
        });

        // Prevent form submission
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            updatePreview();
        });

        // Load first example if available, otherwise use initial preview
        loadFirstExampleOrDefaults();
        updatePreview();
    }

    /**
     * Load first example props and content if available
     */
    function loadFirstExampleOrDefaults() {
        if (typeof componentData !== 'undefined' && componentData.examples && componentData.examples.length > 0) {
            const firstExample = componentData.examples[0];
            if (firstExample.props || firstExample.code) {
                loadExampleData(firstExample.props || {}, firstExample.code || '');
            }
        }
    }

    /**
     * Load example data into form
     */
    function loadExampleData(exampleProps, exampleCode) {
        const form = document.getElementById('prop-editor-form');
        const contentInput = document.getElementById('content-input');

        if (!form) return;

        const initialProps = (typeof componentData !== 'undefined' && componentData.initialProps) || {};
        const propInputs = form.querySelectorAll('[data-prop]');

        // Set prop values
        propInputs.forEach(input => {
            const propName = input.dataset.prop;
            let value;

            if (Object.prototype.hasOwnProperty.call(exampleProps, propName)) {
                value = exampleProps[propName];
            } else if (Object.prototype.hasOwnProperty.call(initialProps, propName)) {
                value = initialProps[propName];
            } else if (input.type === 'checkbox') {
                value = false;
            } else {
                value = '';
            }

            if (input.type === 'checkbox') {
                input.checked = Boolean(value);
            } else {
                input.value = value != null ? value : '';
            }
        });

        // Parse and set content from example code
        let parsedContent = { defaultContent: '', blocks: {} };
        if (exampleCode) {
            try {
                parsedContent = parseExampleCode(exampleCode);
            } catch (error) {
                console.warn('Failed to parse example code', error);
            }
        }

        if (contentInput) {
            contentInput.value = parsedContent.defaultContent || '';
        }

        const blockInputs = form.querySelectorAll('.content-block');
        blockInputs.forEach(block => {
            const blockName = block.dataset.block;
            const blockValue = (parsedContent.blocks && parsedContent.blocks[blockName]) || '';
            block.value = blockValue;
        });
    }

    /**
     * Send preview request to server using iframe
     */
    function sendPreviewRequest(props, content, contentBlocks) {
        const iframePreviewUrl = `/showcase/${componentData.category}/${componentData.slug}/iframe-preview/`;
        const ajaxPreviewUrl = `/showcase/${componentData.category}/${componentData.slug}/preview/`;

        // Create a form and submit to iframe for preview
        const iframe = document.getElementById('component-preview-iframe');
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = iframePreviewUrl;
        form.target = 'component-preview-iframe';
        form.style.display = 'none';

        // Add CSRF token
        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = getCsrfToken();
        form.appendChild(csrfInput);

        // Add data as hidden input
        const dataInput = document.createElement('input');
        dataInput.type = 'hidden';
        dataInput.name = 'data';
        dataInput.value = JSON.stringify({
            props: props,
            content: content,
            content_blocks: contentBlocks
        });
        form.appendChild(dataInput);

        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

        // Also get template code via AJAX for code blocks
        fetch(ajaxPreviewUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                props: props,
                content: content,
                content_blocks: contentBlocks
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else {
                latestPreviewHtml = data.html;
                updateCodeBlocks(data.template_code, props, content, contentBlocks);
                updatePreviewHTML(data.html);
            }
        })
        .catch(error => {
            console.error('Preview error:', error);
            showError('Failed to update preview');
        });
    }

    /**
     * Update preview HTML content (for HTML view toggle)
     */
    function updatePreviewHTML(html) {
        const previewHtml = document.getElementById('component-preview-html');
        latestPreviewHtml = html;

        if (previewHtml) {
            previewHtml.textContent = latestPreviewHtml.trim();
        }
    }

    /**
     * Listen for iframe resize messages
     */
    window.addEventListener('message', function(event) {
        if (event.data.type === 'resize') {
            const iframe = document.getElementById('component-preview-iframe');
            if (iframe) {
                iframe.style.height = event.data.height + 'px';
            }
        }
    });

    /**
     * Update code blocks with current configuration
     */
    function updateCodeBlocks(templateCode, props, content, contentBlocks) {
        // Update Django template code
        const djangoCode = document.getElementById('django-template-code');
        if (djangoCode) {
            djangoCode.textContent = templateCode;
        }

        // Update HTML syntax code
        const htmlCode = document.getElementById('html-template-code');
        if (htmlCode) {
            let htmlSyntax = `<${componentData.tagName}`;

            // Add props as attributes
            for (const [key, value] of Object.entries(props)) {
                if (value === true) {
                    htmlSyntax += ` ${key}`;
                } else if (value === false) {
                    // Skip false boolean values
                } else if (value !== '' && value != null) {
                    htmlSyntax += ` ${key}="${value}"`;
                }
            }

            // Check if we have content
            if (content || Object.keys(contentBlocks).length > 0) {
                htmlSyntax += '>\n';

                if (content) {
                    htmlSyntax += `  ${content}\n`;
                }

                for (const [blockName, blockContent] of Object.entries(contentBlocks)) {
                    if (blockContent) {
                        htmlSyntax += `  <content:${blockName}>\n    ${blockContent}\n  </content:${blockName}>\n`;
                    }
                }

                htmlSyntax += `</${componentData.tagName}>`;
            } else {
                htmlSyntax += ' />';
            }

            htmlCode.textContent = htmlSyntax;
        }
    }

    /**
     * Initialize preview size controls
     */
    function initPreviewControls() {
        const controls = document.querySelectorAll('.preview-controls button');
        const frame = document.querySelector('.preview-section');
        const iframe = document.getElementById('component-preview-iframe');
        const previewHtml = document.getElementById('component-preview-html');

        if (!controls.length || !frame || !iframe || !previewHtml) return;

        let activePreviewMode = frame.dataset.mode || 'desktop';

        if (!frame.dataset.view) {
            frame.dataset.view = 'preview';
        }

        controls.forEach(button => {
            button.addEventListener('click', function() {
                const mode = this.dataset.mode || 'desktop';

                // Always update button states first for all modes
                controls.forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                if (mode === 'desktop') {
                    iframe.removeAttribute('hidden');
                    previewHtml.setAttribute('hidden', '');
                    frame.dataset.view = 'preview';

                    // Toggle between desktop (1024px) and desktop-wide (1280px)
                    const currentMode = frame.dataset.mode;
                    if (currentMode === 'desktop') {
                        frame.dataset.mode = 'desktop-wide';
                    } else if (currentMode === 'desktop-wide') {
                        frame.dataset.mode = 'desktop';
                    } else {
                        // Coming from mobile/wide/html - start with desktop-wide
                        frame.dataset.mode = 'desktop-wide';
                    }
                    activePreviewMode = frame.dataset.mode;
                } else if (mode === 'html') {
                    iframe.setAttribute('hidden', '');
                    previewHtml.removeAttribute('hidden');
                    frame.dataset.view = 'html';
                    frame.dataset.mode = 'wide';
                } else {
                    activePreviewMode = mode;
                    iframe.removeAttribute('hidden');
                    previewHtml.setAttribute('hidden', '');
                    frame.dataset.view = 'preview';
                    frame.dataset.mode = activePreviewMode;
                }
            });
        });
    }

    /**
     * Initialize code tabs
     */
    function initCodeTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        const codeBlocks = document.querySelectorAll('.code-block');

        if (!tabs.length) return;

        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetTab = this.dataset.tab;

                // Update active states
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // Show/hide code blocks
                codeBlocks.forEach(block => {
                    if (block.id === `${targetTab}-code`) {
                        block.classList.add('active');
                    } else {
                        block.classList.remove('active');
                    }
                });
            });
        });
    }

    // Copy buttons are now handled by copy-clipboard.js

    /**
     * Initialize example loaders
     */
    function initExampleLoaders() {
        const loaders = document.querySelectorAll('.load-example');
        const form = document.getElementById('prop-editor-form');
        const contentInput = document.getElementById('content-input');

        if (!loaders.length || !form) {
            return;
        }

        loaders.forEach(loader => {
            loader.addEventListener('click', function() {
                let exampleProps = {};
                const propsPayload = this.dataset.props;

                if (propsPayload) {
                    try {
                        exampleProps = JSON.parse(decodeURIComponent(propsPayload));
                    } catch (error) {
                        console.warn('Failed to parse example props', error);
                        exampleProps = {};
                    }
                }

                const initialProps = (typeof componentData !== 'undefined' && componentData.initialProps) || {};
                const propInputs = form.querySelectorAll('[data-prop]');

                propInputs.forEach(input => {
                    const propName = input.dataset.prop;
                    let value;

                    if (Object.prototype.hasOwnProperty.call(exampleProps, propName)) {
                        value = exampleProps[propName];
                    } else if (Object.prototype.hasOwnProperty.call(initialProps, propName)) {
                        value = initialProps[propName];
                    } else if (input.type === 'checkbox') {
                        value = false;
                    } else {
                        value = '';
                    }

                    if (input.type === 'checkbox') {
                        input.checked = Boolean(value);
                    } else {
                        input.value = value != null ? value : '';
                    }
                });

                let parsedContent = { defaultContent: '', blocks: {} };
                const codePayload = this.dataset.code;

                if (codePayload) {
                    try {
                        const snippet = decodeURIComponent(codePayload);
                        parsedContent = parseExampleCode(snippet);
                    } catch (error) {
                        console.warn('Failed to parse example code', error);
                    }
                }

                if (contentInput) {
                    contentInput.value = parsedContent.defaultContent || '';
                }

                const blockInputs = form.querySelectorAll('.content-block');
                blockInputs.forEach(block => {
                    const blockName = block.dataset.block;
                    const blockValue = (parsedContent.blocks && parsedContent.blocks[blockName]) || '';
                    block.value = blockValue;
                });

                form.dispatchEvent(new Event('submit', { cancelable: true }));

                const iframe = document.getElementById('component-preview-iframe');
                if (iframe) {
                    try {
                        iframe.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } catch (error) {
                        iframe.scrollIntoView();
                    }
                }
            });
        });
    }

    function parseExampleCode(snippet) {
        const result = { defaultContent: '', blocks: {} };

        if (!snippet) {
            return result;
        }

        const includeMatch = snippet.match(/<include:[^>]*>([\s\S]*?)<\/include:[^>]+>/);
        if (!includeMatch) {
            return result;
        }

        let inner = includeMatch[1];

        const blockRegex = /<content:([\w:-]+)>([\s\S]*?)<\/content:\1>/g;
        inner = inner.replace(blockRegex, function(match, name, blockContent) {
            result.blocks[name] = blockContent.trim();
            return '';
        });

        result.defaultContent = inner.trim();
        return result;
    }

    /**
     * Show error message
     */
    function showError(message) {
        const iframe = document.getElementById('component-preview-iframe');
        const previewHtml = document.getElementById('component-preview-html');
        if (iframe) {
            // Create error content and display in iframe
            const errorHTML = `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                            padding: 1rem;
                            margin: 0;
                        }
                        .error-message {
                            padding: 1rem;
                            background: #fee2e2;
                            border: 1px solid #fecaca;
                            border-radius: 0.375rem;
                            color: #dc2626;
                        }
                    </style>
                </head>
                <body>
                    <div class="error-message">
                        <strong>Error:</strong> ${message}
                    </div>
                </body>
                </html>
            `;
            iframe.src = 'data:text/html;charset=utf-8,' + encodeURIComponent(errorHTML);
        }

        if (previewHtml) {
            previewHtml.textContent = `<!-- ${message} -->`;
        }
    }

    // Copy functionality moved to copy-clipboard.js

    /**
     * Debounce function to limit API calls
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
})();
