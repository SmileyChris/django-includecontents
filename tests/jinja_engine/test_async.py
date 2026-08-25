"""Rendering tests for Jinja environments built with ``enable_async=True``.

Django's own template layer is sync-only -- neither the Django nor the Jinja2
backend exposes an async render -- so these cover the extension being driven
through a Jinja ``Environment`` directly.

The tests drive the event loop with ``asyncio.run`` rather than async test
functions so that no extra pytest plugin is needed.
"""

from __future__ import annotations

import asyncio

from jinja2 import DictLoader, Environment

from includecontents.jinja2 import IncludeContentsExtension


def _loader() -> DictLoader:
    return DictLoader(
        {
            "components/card.html": (
                "{# props title, active=False #}\n"
                "{{ title }}::{{ contents }}::{{ active }}"
            ),
            "components/modal.html": (
                '{# props title="", size="md" #}\n'
                "<header>{{ contents.get('header') }}</header>"
                "<main>{{ contents }}</main>"
            ),
            "components/section.html": "<section>{{ contents }}</section>",
        }
    )


def _async_environment() -> Environment:
    return Environment(
        loader=_loader(), extensions=[IncludeContentsExtension], enable_async=True
    )


def _sync_environment() -> Environment:
    return Environment(loader=_loader(), extensions=[IncludeContentsExtension])


def _render(template_source: str, **context) -> str:
    """Render asynchronously, asserting the result matches the sync engine.

    Parity is the actual requirement: async mode must not change what a
    component renders, only how it gets there.
    """
    rendered_async = asyncio.run(
        _async_environment().from_string(template_source).render_async(**context)
    )
    rendered_sync = _sync_environment().from_string(template_source).render(**context)

    assert rendered_async == rendered_sync, "async render diverged from sync"
    return rendered_async


def test_renders_a_component_in_an_async_environment() -> None:
    assert _render("<include:section>Body</include:section>") == "<section>Body</section>"


def test_renders_named_and_default_contents() -> None:
    rendered = _render(
        "<include:modal>"
        "<content:header>Title</content:header>"
        "Main body"
        "</include:modal>"
    )

    assert rendered.strip() == "<header>Title</header><main>Main body</main>"


def test_renders_props_and_defaults() -> None:
    rendered = _render('<include:card title="Hi">Body</include:card>')

    assert rendered.strip() == "Hi::Body::False"


def test_renders_nested_components() -> None:
    rendered = _render(
        "<include:section>"
        "<include:section>Inner</include:section>"
        "</include:section>"
    )

    assert rendered.strip() == "<section><section>Inner</section></section>"


def test_resolves_template_expressions_in_attributes() -> None:
    """Attribute interpolation compiles its own mini-template, which must not
    try to render itself asynchronously."""
    rendered = _render('<include:card title="{{ name }}">Body</include:card>', name="Ada")

    assert rendered.strip() == "Ada::Body::False"


def test_concurrent_async_renders_do_not_leak_slot_content() -> None:
    """The async analogue of the threaded slot-leak test.

    Two renders are interleaved on a single event loop: A blocks inside its
    header slot until B has pushed its own frame, so if the captured contents
    were shared between tasks, A's slot would land in B.
    """
    env = _async_environment()

    a_inside_slot = asyncio.Event()
    b_frame_pushed = asyncio.Event()
    a_finished = asyncio.Event()

    async def gate_a():
        a_inside_slot.set()
        await asyncio.wait_for(b_frame_pushed.wait(), timeout=10)
        return ""

    async def gate_b():
        b_frame_pushed.set()
        await asyncio.wait_for(a_finished.wait(), timeout=10)
        return ""

    env.globals.update(gate_a=gate_a, gate_b=gate_b)

    template_a = env.from_string(
        "<include:modal>"
        "<content:header>{{ gate_a() }}A-SLOT</content:header>"
        "A-MAIN"
        "</include:modal>"
    )
    template_b = env.from_string(
        "<include:modal>"
        "<content:header>B-SLOT</content:header>"
        "B-MAIN{{ gate_b() }}"
        "</include:modal>"
    )

    async def main():
        task_a = asyncio.create_task(template_a.render_async())
        await asyncio.wait_for(a_inside_slot.wait(), timeout=10)
        task_b = asyncio.create_task(template_b.render_async())
        result_a = await asyncio.wait_for(task_a, timeout=10)
        a_finished.set()
        result_b = await asyncio.wait_for(task_b, timeout=10)
        return result_a, result_b

    result_a, result_b = asyncio.run(main())

    assert result_a.strip() == "<header>A-SLOT</header><main>A-MAIN</main>"
    assert result_b.strip() == "<header>B-SLOT</header><main>B-MAIN</main>"
