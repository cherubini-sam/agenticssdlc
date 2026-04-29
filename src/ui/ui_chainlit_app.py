"""Wires the multi-agent SDLC pipeline to a Chainlit chat interface with live step streaming."""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any

import bcrypt
import chainlit as cl
from chainlit.input_widget import Select, Slider, Switch

from src.agents.agents_manager import AgentsManager
from src.agents.agents_utils import (
    AGENTS_MANAGER_AGENT_NAME,
    AGENTS_MANAGER_PHASE_MAX,
    AGENTS_MANAGER_PHASE_MIN,
)
from src.analytics.analytics_bigquery_ingest import AnalyticsBigqueryIngest
from src.analytics.analytics_supabase_ingest import AnalyticsSupabaseIngest
from src.api.middleware.api_middleware_observability import record_active_workflows, record_metrics
from src.api.schemas.api_schemas_task import ApiSchemasTaskRequest
from src.ui.ui_chainlit_formatters import (
    ui_chainlit_utils_confidence_badge,
    ui_chainlit_utils_format_agent_trace,
    ui_chainlit_utils_format_phase_output,
)
from src.ui.ui_chainlit_utils import (
    UI_CHAINLIT_APP_DEFAULT_MAX_RETRIES,
    UI_CHAINLIT_APP_DEFAULT_REFLECTOR_THRESHOLD,
    UI_CHAINLIT_APP_DEFAULT_VALIDATOR_THRESHOLD,
    UI_CHAINLIT_APP_DEFAULT_VERBOSITY,
    UI_CHAINLIT_APP_STREAM_TIMEOUT,
    UI_CHAINLIT_UTILS_GRAPH_NODES,
    UI_CHAINLIT_UTILS_PHASE_META,
    UI_CHAINLIT_UTILS_STARTERS,
    UI_CHAINLIT_UTILS_STEP_INIT_TOKEN,
    UI_CHAINLIT_UTILS_STEP_TYPE_LLM,
    UI_CHAINLIT_UTILS_TASK_PHASES,
)

logger = logging.getLogger(__name__)

_active_workflow_count: int = 0


@cl.author_rename
async def ui_chainlit_app_author_rename(author: str) -> str:
    """Override default Chainlit author labels with our brand name."""

    mapping = {
        "Chatbot": "Agentics SDLC",
        "chatbot": "Agentics SDLC",
        "viewer": "Agentics SDLC",
    }
    return mapping.get(author, author)


@cl.set_starters
async def ui_chainlit_app_set_starters() -> list[cl.Starter]:
    """Populate the empty-chat prompt suggestions from the starters config."""

    return [
        cl.Starter(
            label=starter["label"],
            message=starter["message"],
            icon=starter["icon"],
        )
        for starter in UI_CHAINLIT_UTILS_STARTERS
    ]


@cl.password_auth_callback
def ui_chainlit_app_auth_callback(_username: str, password: str) -> cl.User | None:
    """Validate login against the bcrypt hash in UI_AUTH_PASSWORD_HASH env var.

    Args:
        _username: Accepted but ignored; any value is valid.
        password: Plain-text password to verify against the stored bcrypt hash.

    Returns:
        cl.User with role "viewer" on success; None if the env var is unset,
        the password does not match, or bcrypt raises an exception.
    """

    pw_hash = os.getenv("UI_AUTH_PASSWORD_HASH", "").strip()
    if not pw_hash:
        logger.warning("UI_AUTH_PASSWORD_HASH is not set — rejecting login")
        return None
    try:
        if bcrypt.checkpw(password.encode("utf-8"), pw_hash.encode("utf-8")):
            return cl.User(
                identifier="Agentics SDLC",
                display_name="Agentics SDLC",
                metadata={"role": "viewer"},
            )
    except Exception as exc:
        logger.exception("bcrypt verification raised: %r", exc)
    return None


@cl.action_callback("show_results")
async def ui_chainlit_app_show_results(action: cl.Action) -> None:
    """Push stored Markdown to the frontend via a custom Socket.IO event."""

    task_id: str = action.value
    md_content: str = cl.user_session.get(
        f"result_md_{task_id}",
        "# Agentics SDLC Workflow\n\n_No content stored for this task._",
    )
    await cl.context.emitter.emit("show_results_modal", {"content": md_content})


@cl.action_callback("export_markdown")
async def ui_chainlit_app_export_markdown(action: cl.Action) -> None:
    """Serve the stored Markdown as a downloadable .md file."""

    task_id: str = action.value
    md_content: str = cl.user_session.get(
        f"result_md_{task_id}",
        "# Agentics SDLC -- Workflow Result\n\n_No content stored for this task._",
    )
    filename = f"agentics_result_{task_id[:8]}.md"
    await cl.Message(
        content="",
        elements=[
            cl.File(
                name=filename,
                content=md_content.encode("utf-8"),
                display="inline",
            )
        ],
    ).send()


@cl.on_settings_update
async def ui_chainlit_app_on_settings_update(settings: dict) -> None:
    """Persist updated slider/toggle values into the session."""

    cl.user_session.set("chat_settings", settings)


@cl.on_chat_start
async def ui_chainlit_app_on_chat_start() -> None:
    """Compile the LangGraph, send welcome message, and set up ChatSettings."""

    try:
        manager: AgentsManager = await AgentsManager.agents_manager_create()
        cl.user_session.set("manager", manager)
        cl.user_session.set("bq_logger", AnalyticsBigqueryIngest())
        cl.user_session.set("sb_logger", AnalyticsSupabaseIngest())
    except Exception as exc:
        await cl.Message(
            content=(
                f"**Initialisation failed:** `{exc}`\n\n"
                "Please verify your `.env` file and GCP credentials "
                "(run: `gcloud auth application-default login`) and restart."
            )
        ).send()
        return

    settings = cl.ChatSettings(
        [
            Slider(
                id="reflector_confidence_threshold",
                label="Confidence Threshold",
                initial=UI_CHAINLIT_APP_DEFAULT_REFLECTOR_THRESHOLD,
                min=0.0,
                max=1.0,
                step=0.05,
                tooltip="Minimum confidence to approve the plan",
            ),
            Slider(
                id="validator_confidence_threshold",
                label="Score Threshold",
                initial=UI_CHAINLIT_APP_DEFAULT_VALIDATOR_THRESHOLD,
                min=0.0,
                max=1.0,
                step=0.05,
                tooltip="Minimum score to pass the result",
            ),
            Slider(
                id="max_retries",
                label="Max Retries",
                initial=UI_CHAINLIT_APP_DEFAULT_MAX_RETRIES,
                min=1,
                max=5,
                step=1,
                tooltip="Maximum retry attempts when agent rejects",
            ),
            Select(
                id="verbosity",
                label="Output Verbosity",
                values=["concise", "standard", "detailed"],
                initial_value=UI_CHAINLIT_APP_DEFAULT_VERBOSITY,
                tooltip="Controls the detail level of agent outputs",
            ),
            Switch(
                id="show_agent_trace",
                label="Show Agent Trace",
                initial=True,
                tooltip="Show the progress tracker panel",
            ),
        ]
    )
    await settings.send()
    cl.user_session.set("chat_settings", settings.settings())
    cl.user_session.set("avatars_setup", True)


@cl.on_stop
async def ui_chainlit_app_on_stop() -> None:
    """Let the streaming loop know the user hit stop, and snapshot for resume."""

    cl.user_session.set("stop_requested", True)
    active = cl.user_session.get("_active_run")
    if active:
        cl.user_session.set("interrupted_run", active)


@cl.on_message
async def ui_chainlit_app_on_message(message: cl.Message) -> None:
    """Run the full Phase 1-6 workflow, streaming each agent step into the chat."""

    manager: AgentsManager | None = cl.user_session.get("manager")
    if manager is None:
        await cl.Message(content="Session not initialised. Please refresh the page.").send()
        return

    cl.user_session.set("stop_requested", False)

    # Read user-tunable settings
    _settings: dict = cl.user_session.get("chat_settings") or {}
    # Backwards compat: old key was "confidence_threshold", now split into two
    _reflector_threshold = float(
        _settings.get("reflector_confidence_threshold")
        or _settings.get("confidence_threshold")
        or UI_CHAINLIT_APP_DEFAULT_REFLECTOR_THRESHOLD
    )
    _validator_threshold = float(
        _settings.get("validator_confidence_threshold")
        or UI_CHAINLIT_APP_DEFAULT_VALIDATOR_THRESHOLD
    )
    _max_retries = int(_settings.get("max_retries", UI_CHAINLIT_APP_DEFAULT_MAX_RETRIES))
    _verbosity: str = str(_settings.get("verbosity", UI_CHAINLIT_APP_DEFAULT_VERBOSITY))
    _show_agent_trace: bool = bool(_settings.get("show_agent_trace", True))

    # Resume from interrupted run if one exists
    interrupted = cl.user_session.get("interrupted_run")
    _resume = interrupted is not None
    if _resume:
        task_id = interrupted["task_id"]
        _completed_nodes: set[str] = set(interrupted.get("completed_nodes", []))
        cl.user_session.set("interrupted_run", None)
    else:
        task_id = str(uuid.uuid4())
        _completed_nodes = set()

    request = ApiSchemasTaskRequest(task_id=task_id, content=message.content)

    global _active_workflow_count
    start_time = time.monotonic()
    _active_workflow_count += 1
    record_active_workflows(_active_workflow_count)

    # TaskList: live progress tracker in the sidebar
    task_list: cl.TaskList | None = None
    phase_tasks: dict[str, cl.Task] = {}

    if _show_agent_trace:
        task_list = cl.TaskList()
        task_list.status = "Running"
        for node_key, phase_title in UI_CHAINLIT_UTILS_TASK_PHASES:
            status = cl.TaskStatus.DONE if node_key in _completed_nodes else cl.TaskStatus.READY
            task = cl.Task(title=phase_title, status=status)
            await task_list.add_task(task)
            phase_tasks[node_key] = task
        await task_list.send()

    open_steps: dict[str, cl.Step] = {}
    current_node: list[str] = [""]
    token_counts: dict[str, int] = {}
    # Snapshot active run so on_stop can save it for later resumption
    cl.user_session.set(
        "_active_run", {"task_id": task_id, "completed_nodes": list(_completed_nodes)}
    )

    running: dict[str, Any] = {
        "task_id": task_id,
        "content": message.content,
        "messages": [],
        "confidence": 0.0,
        "result": None,
        "error": None,
        "approved": False,
        "protocol_status": None,
    }

    stream_timeout = UI_CHAINLIT_APP_STREAM_TIMEOUT

    try:
        event_gen = manager.agents_manager_stream_events(
            request,
            confidence_threshold=_reflector_threshold,
            validator_confidence_threshold=_validator_threshold,
            max_retries=_max_retries,
            verbosity=_verbosity,
            resume=_resume,
        ).__aiter__()
        while True:
            if cl.user_session.get("stop_requested"):
                running["error"] = "Stopped by user"
                for s in open_steps.values():
                    s.output = "Stopped by user"
                    await s.__aexit__(None, None, None)
                open_steps.clear()
                break

            try:
                event = await asyncio.wait_for(event_gen.__anext__(), timeout=stream_timeout)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                running["error"] = f"Workflow timed out after {stream_timeout}s"
                for s in open_steps.values():
                    s.output = f"Timed out after {stream_timeout}s"
                    await s.__aexit__(None, None, None)
                open_steps.clear()
                break

            kind: str = event.get("event", "")
            name: str = event.get("name", "")
            data: dict = event.get("data", {})

            if kind == "on_chain_start" and name in UI_CHAINLIT_UTILS_GRAPH_NODES:
                # On retry, reset downstream phases so the tracker looks right
                if name == "retry_increment":
                    if task_list:
                        for retry_phase in (
                            "librarian",
                            "architect",
                            "review",
                            "execute",
                            "verify",
                        ):
                            if retry_phase in phase_tasks:
                                phase_tasks[retry_phase].status = cl.TaskStatus.READY
                        await task_list.update()

                _, label, stype, _ = UI_CHAINLIT_UTILS_PHASE_META[name]
                step = cl.Step(
                    name=label,
                    type=stype,  # type: ignore[arg-type]  # widened to str in our PHASE_META table
                    show_input=False,
                )
                await step.__aenter__()
                # Non-LLM steps never receive on_chat_model_stream tokens, so stream
                # the init token to force the accordion open immediately. For LLM steps
                # the first model token serves this role and avoids a "…" prefix on content.
                if stype != UI_CHAINLIT_UTILS_STEP_TYPE_LLM:
                    await step.stream_token(UI_CHAINLIT_UTILS_STEP_INIT_TOKEN)
                open_steps[name] = step
                current_node[0] = name
                token_counts[name] = 0

                if task_list and name in phase_tasks:
                    phase_tasks[name].status = cl.TaskStatus.RUNNING
                    await task_list.update()

            elif kind == "on_chat_model_stream":
                active = current_node[0]
                if active and active in open_steps:
                    chunk = data.get("chunk")
                    if chunk is not None:
                        content = getattr(chunk, "content", "")
                        if isinstance(content, str) and content:
                            await open_steps[active].stream_token(content)
                            token_counts[active] = token_counts.get(active, 0) + len(content)

            elif kind == "on_chain_end" and name in UI_CHAINLIT_UTILS_GRAPH_NODES:
                current_node[0] = ""
                step = open_steps.pop(name, None)  # type: ignore[arg-type]
                if step is None:
                    continue

                output: dict = data.get("output", {})

                for k, v in output.items():
                    if k == "messages":
                        running["messages"].extend(v or [])
                    else:
                        running[k] = v

                token_counts.pop(name, 0)
                formatted = ui_chainlit_utils_format_phase_output(name, output)
                if formatted:
                    step.output = formatted

                await step.__aexit__(None, None, None)

                if task_list and name in phase_tasks:
                    phase_tasks[name].status = cl.TaskStatus.DONE
                    await task_list.update()

                # Keep the snapshot current so stop+resume works mid-pipeline
                _completed_nodes.add(name)
                cl.user_session.set(
                    "_active_run",
                    {"task_id": task_id, "completed_nodes": list(_completed_nodes)},
                )

            elif kind == "on_chain_error":
                err_msg = str(data.get("error", "Workflow error"))
                running["error"] = err_msg

                active = current_node[0]
                if task_list and active and active in phase_tasks:
                    phase_tasks[active].status = cl.TaskStatus.FAILED
                    await task_list.update()

                for s in open_steps.values():
                    s.output = f"ERROR: {err_msg}"
                    await s.__aexit__(None, None, None)
                open_steps.clear()
                break

    except Exception as exc:
        running["error"] = str(exc)
        for s in open_steps.values():
            s.output = f"Unexpected error: {exc}"
            await s.__aexit__(None, None, None)
        open_steps.clear()

    # Close any steps that somehow didn't finish cleanly
    for node, s in list(open_steps.items()):
        s.output = "Phase did not complete cleanly."
        await s.__aexit__(None, None, None)

    if task_list:
        task_list.status = "Done" if not running.get("error") else "Failed"
        await task_list.update()

    cl.user_session.set("_active_run", None)

    # Analytics (fire-and-forget, never blocks the UI)
    _workflow_latency_ms = (time.monotonic() - start_time) * 1000
    _workflow_status = "failed" if running.get("error") else "completed"
    _workflow_confidence = float(running.get("confidence", 0.0))
    _bq_status = "success" if _workflow_status == "completed" else "error"
    _phases_done = sorted(
        {
            msg["phase"]
            for msg in running["messages"]
            if "phase" in msg
            and AGENTS_MANAGER_PHASE_MIN <= msg["phase"] <= AGENTS_MANAGER_PHASE_MAX
        }
    )
    _phase_reached = _phases_done[-1] if _phases_done else 0

    _bq_logger: AnalyticsBigqueryIngest | None = cl.user_session.get("bq_logger")
    if _bq_logger:
        await _bq_logger.analytics_bigquery_log_agent_call(
            session_id=task_id,
            agent_name=AGENTS_MANAGER_AGENT_NAME,
            phase=_phase_reached,
            latency_ms=_workflow_latency_ms,
            confidence=_workflow_confidence,
            status=_bq_status,
            task_content=message.content,
            error=running.get("error"),
        )

    _sb_logger: AnalyticsSupabaseIngest | None = cl.user_session.get("sb_logger")
    if _sb_logger and _sb_logger.is_enabled:
        await _sb_logger.analytics_supabase_log_agent_call(
            session_id=task_id,
            agent_name=AGENTS_MANAGER_AGENT_NAME,
            phase=_phase_reached,
            latency_ms=_workflow_latency_ms,
            confidence=_workflow_confidence,
            status=_bq_status,
            task_content=message.content,
            error=running.get("error"),
        )
        asyncio.create_task(
            _sb_logger.analytics_supabase_upsert_workflow_snapshot(
                session_id=task_id,
                phase_reached=_phase_reached,
                retry_count=0,
                final_status=_workflow_status,
                confidence=_workflow_confidence,
                latency_ms=_workflow_latency_ms,
                snapshot_data={
                    "phases_completed": _phases_done,
                    "agent_trace": running["messages"],
                    "error": running.get("error"),
                },
            )
        )

    # Build final result
    _active_workflow_count -= 1
    record_active_workflows(max(0, _active_workflow_count))
    latency_ms = (time.monotonic() - start_time) * 1000
    final_status: str = "failed" if running.get("error") else "completed"
    confidence = float(running.get("confidence", 0.0))

    record_metrics(
        agent=AGENTS_MANAGER_AGENT_NAME,
        phase="6",
        status=final_status,
        latency_s=latency_ms / 1000.0,
        confidence=confidence if confidence > 0 else None,
    )
    result: str | None = running.get("result")
    error: str | None = running.get("error")

    phases = sorted(
        {
            msg["phase"]
            for msg in running["messages"]
            if "phase" in msg
            and AGENTS_MANAGER_PHASE_MIN <= msg["phase"] <= AGENTS_MANAGER_PHASE_MAX
        }
    )

    badge = ui_chainlit_utils_confidence_badge(confidence)

    # Markdown export (stored in session for the download button)
    md_parts: list[str] = [
        "# Agentics SDLC Workflow",
        "",
        f"**Task ID:** `{task_id}`  ",
        f"**Status:** {final_status}  ",
        f"**Confidence:** {badge} `{confidence:.2f}`  ",
        f"**Phases:** `{phases}`  ",
        f"**Latency:** `{latency_ms:.0f} ms`",
        "",
    ]
    if result:
        md_parts += ["## Result", "", result, ""]
    if error:
        md_parts += ["## Error", "", f"```\n{error}\n```", ""]

    trace_md = ui_chainlit_utils_format_agent_trace(running["messages"])
    if _show_agent_trace and trace_md and trace_md != "_No agent trace available._":
        md_parts += ["", "---", "", trace_md]

    full_md = "\n".join(md_parts)
    cl.user_session.set(f"result_md_{task_id}", full_md)

    # Final chat message
    phases_str = " > ".join(str(p) for p in phases) if phases else "--"

    result_parts: list[str] = [
        f"**{final_status.upper()}** | {badge} `{confidence:.2f}`"
        f" | `{latency_ms:.0f} ms` | `#{task_id[:8]}`",
        "",
        f"**Phases executed:** `{phases_str}`",
    ]
    if error:
        result_parts += ["", f"> **Error:** {error}"]

    elements: list = []
    if result:
        elements.append(
            cl.Text(
                name="Show Results",
                content=result,
                display="side",
            )
        )
    elif error:
        elements.append(
            cl.Text(
                name="Show Error Details",
                content=f"# Error Details\n\n```\n{error}\n```",
                display="side",
            )
        )
    if _show_agent_trace and trace_md and trace_md != "_No agent trace available._":
        elements.append(
            cl.Text(
                name="Agent Trace",
                content=trace_md,
                display="side",
            )
        )

    actions: list = [
        cl.Action(
            name="show_results",
            value=task_id,
            label="Show Results",
            description="Open full workflow result in a modal",
        ),
        cl.Action(
            name="export_markdown",
            value=task_id,
            label="Download .MD",
            description="Download the full workflow result as a Markdown file",
        ),
    ]

    await cl.Message(
        content="\n".join(result_parts),
        elements=elements,
        actions=actions,
    ).send()
