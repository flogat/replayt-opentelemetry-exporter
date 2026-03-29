from importlib.metadata import PackageNotFoundError, version

from replayt_opentelemetry_exporter.tracing import (
    RunSummary,
    build_meter_provider,
    build_resource,
    build_tracer_provider,
    generate_run_summary,
    get_workflow_tracer,
    install_meter_provider,
    install_tracer_provider,
    record_exporter_error,
    record_run_outcome,
    workflow_run_span,
)

try:
    __version__ = version("replayt-opentelemetry-exporter")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
    "build_resource",
    "build_tracer_provider",
    "build_meter_provider",
    "install_tracer_provider",
    "install_meter_provider",
    "get_workflow_tracer",
    "workflow_run_span",
    "RunSummary",
    "generate_run_summary",
    "record_run_outcome",
    "record_exporter_error",
]
