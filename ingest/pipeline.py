"""
Main ingest script — run once (or on regulation updates).

Usage:
    python -m ingest.pipeline                         # all sources from sources.py
    python -m ingest.pipeline --source path/to/file.pdf --law-name "Moja Ustawa"
    python -m ingest.pipeline --source https://... --file-type pdf
"""
from __future__ import annotations

import argparse
from pathlib import Path

import requests
from rich.console import Console
from rich.table import Table

from .chunker import chunk_document
from .embedder import Embedder
from .parser import parse_html, parse_pdf
from .sources import LEGAL_SOURCES
from .store import VectorStore
from config import settings

console = Console()


def ingest_file(
    path: str,
    law_name: str,
    embedder: Embedder,
    store: VectorStore,
    file_type: str = "pdf",
) -> int:
    console.print(f"  Parsing [cyan]{path}[/cyan]")
    doc = parse_html(path) if file_type == "html" else parse_pdf(Path(path))
    chunks = chunk_document(doc, law_name=law_name)
    console.print(f"  Chunks: [yellow]{len(chunks)}[/yellow]")

    if not chunks:
        console.print("  [red]No chunks produced — skipping[/red]")
        return 0

    embeddings = embedder.embed_chunks(chunks)
    return store.upsert(chunks, embeddings)


def _download(url: str, cache_dir: Path = Path("knowledge_base")) -> Path:
    cache_dir.mkdir(exist_ok=True)
    filename = url.split("/")[-1] or "document.pdf"
    local = cache_dir / filename

    if local.exists():
        console.print(f"  Cache hit: [green]{local}[/green]")
        return local

    console.print(f"  Downloading {url}")
    resp = requests.get(url, timeout=60, stream=True)
    resp.raise_for_status()
    with open(local, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)
    console.print(f"  Saved: [green]{local}[/green]")
    return local


def run_full_ingest() -> None:
    embedder = Embedder(settings.embedding_model, settings.embedding_batch_size)
    store = VectorStore(collection_name=settings.qdrant_collection, path=settings.qdrant_path)
    store.ensure_collection(embedder.embedding_dim)

    table = Table(title="Ingest Results")
    table.add_column("Dokument", style="cyan")
    table.add_column("P", justify="center")
    table.add_column("Chunks", justify="right")
    table.add_column("Status")

    for src in sorted(LEGAL_SOURCES, key=lambda s: s.priority):
        console.rule(f"[bold]{src.name}[/bold]")
        try:
            path = str(_download(src.url)) if src.url.startswith("http") else src.url
            count = ingest_file(path, src.name, embedder, store, src.file_type)
            table.add_row(src.name, str(src.priority), str(count), "[green]OK[/green]")
        except Exception as e:
            console.print(f"  [red]ERROR: {e}[/red]")
            table.add_row(src.name, str(src.priority), "0", f"[red]{type(e).__name__}[/red]")

    console.print(table)
    console.print(f"\nTotal vectors in Qdrant: [bold]{store.count()}[/bold]")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest legal documents into Qdrant")
    parser.add_argument("--source", help="Path or URL to a single document")
    parser.add_argument("--law-name", help="Law name for chunk metadata")
    parser.add_argument("--file-type", choices=["pdf", "html"], default="pdf")
    args = parser.parse_args()

    if args.source:
        embedder = Embedder(settings.embedding_model, settings.embedding_batch_size)
        store = VectorStore(collection_name=settings.qdrant_collection, path=settings.qdrant_path)
        store.ensure_collection(embedder.embedding_dim)
        count = ingest_file(
            path=args.source,
            law_name=args.law_name or args.source,
            embedder=embedder,
            store=store,
            file_type=args.file_type,
        )
        console.print(f"Stored [bold]{count}[/bold] chunks")
    else:
        run_full_ingest()


if __name__ == "__main__":
    main()
