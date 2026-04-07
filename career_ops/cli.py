"""Command-line interface for Career-Ops."""

import asyncio
import os
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from .pipeline import Pipeline
from .tracker import ApplicationStatus

console = Console()


@click.group()
@click.option("--config", "-c", default="config/profile.yml", help="Config file path")
@click.option("--db", "-d", default="data/applications.db", help="Database path")
@click.pass_context
def cli(ctx, config, db):
    """Career-Ops Python - AI-powered job search automation."""
    ctx.ensure_object(dict)
    ctx.obj["pipeline"] = Pipeline(config_path=config, db_path=db)


@cli.command()
@click.argument("url")
@click.option("--pdf/--no-pdf", default=True, help="Generate PDF resume")
@click.pass_context
def evaluate(ctx, url, pdf):
    """Evaluate a single job URL."""
    pipeline = ctx.obj["pipeline"]

    console.print(f"🔍 Evaluating: {url}", style="bold blue")

    result = asyncio.run(pipeline.evaluate_job(url, generate_pdf=pdf))
    evaluation = result["evaluation"]

    # Display results
    console.print()
    console.print(f"Company: {evaluation.company}", style="bold")
    console.print(f"Role: {evaluation.role}")
    console.print()

    # Score table
    table = Table(title="Evaluation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Score", f"{evaluation.overall_score}/5")
    table.add_row("Grade", evaluation.grade)
    table.add_row("Recommendation", evaluation.recommendation.replace("_", " ").title())
    table.add_row("Application ID", str(result["app_id"]))

    console.print(table)

    if result["pdf_path"]:
        console.print(f"📄 PDF: {result['pdf_path']}", style="dim")

    console.print()
    console.print("Reasoning:", style="bold")
    console.print(evaluation.reasoning)


@cli.command()
@click.argument("urls_file", type=click.Path(exists=True))
@click.option("--parallel", "-p", default=3, help="Max concurrent evaluations")
@click.option("--pdf/--no-pdf", default=True, help="Generate PDFs")
@click.pass_context
def batch(ctx, urls_file, parallel, pdf):
    """Evaluate multiple jobs from a file."""
    pipeline = ctx.obj["pipeline"]

    with open(urls_file, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    console.print(f"🚀 Batch evaluating {len(urls)} jobs (max {parallel} concurrent)", style="bold blue")

    results = asyncio.run(pipeline.evaluate_batch(urls, max_concurrent=parallel))

    # Summary table
    table = Table(title=f"Batch Results ({len(results)}/{len(urls)} successful)")
    table.add_column("Company", style="cyan")
    table.add_column("Role", style="magenta")
    table.add_column("Score", justify="right")
    table.add_column("Grade")
    table.add_column("Recommendation")

    for result in results:
        eval = result["evaluation"]
        table.add_row(
            eval.company[:30],
            eval.role[:40],
            str(eval.overall_score),
            eval.grade,
            eval.recommendation.replace("_", " ").title(),
        )

    console.print(table)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show pipeline statistics."""
    pipeline = ctx.obj["pipeline"]
    stats = pipeline.get_pipeline_stats()

    table = Table(title="Pipeline Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Applications", str(stats.total))
    table.add_row("Strong Apply", str(stats.strong_apply_count))
    table.add_row("Average Score", f"{stats.average_score}/5")
    table.add_row("Response Rate", f"{stats.response_rate}%")

    console.print(table)

    # Status breakdown
    console.print()
    console.print("Status Breakdown:", style="bold")
    for status, count in stats.by_status.items():
        if count > 0:
            console.print(f"  {status}: {count}")


@cli.command()
@click.option("--status", "-s", help="Filter by status")
@click.option("--min-score", "-m", type=float, help="Minimum score filter")
@click.option("--limit", "-l", type=int, default=20, help="Max results")
@click.pass_context
def list(ctx, status, min_score, limit):
    """List applications in pipeline."""
    pipeline = ctx.obj["pipeline"]

    status_enum = ApplicationStatus(status) if status else None
    apps = pipeline.get_applications(status=status_enum, min_score=min_score)
    apps = apps[:limit]

    if not apps:
        console.print("No applications found.", style="yellow")
        return

    table = Table(title=f"Applications (showing {len(apps)})")
    table.add_column("ID", justify="right", style="cyan")
    table.add_column("Company", style="green")
    table.add_column("Role")
    table.add_column("Score", justify="right")
    table.add_column("Status")

    for app in apps:
        table.add_row(
            str(app.id),
            app.company[:25],
            app.role[:40],
            f"{app.score:.1f}" if app.score else "N/A",
            app.status,
        )

    console.print(table)


@cli.command()
@click.argument("app_id", type=int)
@click.argument("status")
@click.option("--notes", "-n", help="Optional notes")
@click.pass_context
def update(ctx, app_id, status, notes):
    """Update application status."""
    pipeline = ctx.obj["pipeline"]

    try:
        status_enum = ApplicationStatus(status)
        pipeline.update_application_status(app_id, status_enum, notes)
        console.print(f"✅ Updated application {app_id} to {status}", style="green")
    except ValueError as e:
        console.print(f"❌ Invalid status: {status}", style="red")
        console.print(f"Valid statuses: {', '.join(s.value for s in ApplicationStatus)}")


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Launch Streamlit dashboard."""
    import subprocess
    console.print("🚀 Launching Streamlit dashboard...", style="bold blue")
    subprocess.run(["streamlit", "run", "dashboard/app.py"])


if __name__ == "__main__":
    cli()
