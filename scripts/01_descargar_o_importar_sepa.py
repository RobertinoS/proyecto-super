from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path


DATASET_URLS = {
    "minoristas": "https://datos.produccion.gob.ar/dataset/sepa-precios",
    "mayoristas": "https://datos.produccion.gob.ar/dataset/precios-claros-sepa-mayoristas",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def describe_file(path: Path) -> dict:
    item = {
        "name": path.name,
        "path": str(path),
        "suffix": path.suffix.lower(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "role_guess": guess_role(path.name),
    }
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            item["zip_members"] = [
                {"name": member.filename, "bytes": member.file_size, "role_guess": guess_role(member.filename)}
                for member in archive.infolist()
                if not member.is_dir()
            ]
    return item


def guess_role(name: str) -> str:
    low = name.lower()
    if "precio" in low:
        return "precios"
    if "producto" in low:
        return "productos"
    if "sucursal" in low:
        return "sucursales"
    if "comercio" in low or "bandera" in low:
        return "comercios"
    if low.endswith(".csv"):
        return "csv"
    return "desconocido"


def extract_zip_csvs(zip_path: Path, output_dir: Path) -> list[dict]:
    extracted: list[dict] = []
    extract_dir = output_dir / "extracted" / zip_path.stem
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            suffix = Path(member.filename).suffix.lower()
            if suffix not in {".csv", ".txt"}:
                continue
            target = extract_dir / Path(member.filename).name
            with archive.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(describe_file(target))
    return extracted


def manual_import(input_path: Path, output_dir: Path) -> dict:
    if not input_path.exists():
        raise FileNotFoundError(f"No existe el archivo de entrada: {input_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    imported_dir = output_dir / "manual"
    imported_dir.mkdir(parents=True, exist_ok=True)
    target = imported_dir / input_path.name
    if input_path.resolve() != target.resolve():
        shutil.copy2(input_path, target)
    manifest = {
        "created_at": utc_now(),
        "mode": "manual",
        "source_path": str(input_path),
        "stored_path": str(target),
        "dataset_urls": DATASET_URLS,
        "files": [describe_file(target)],
        "extracted": extract_zip_csvs(target, output_dir) if zipfile.is_zipfile(target) else [],
        "notes": [
            "Los ZIP oficiales SEPA se descargan desde datos.produccion.gob.ar.",
            "Este importador no requiere credenciales ni servicios pagos.",
            "Los archivos en data/raw/sepa quedan ignorados por Git.",
        ],
    }
    write_manifest(output_dir / "sepa_import_manifest.json", manifest)
    return manifest


def download_plan(output_dir: Path, download_url: str | None, allow_download: bool) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "created_at": utc_now(),
        "mode": "download-plan",
        "dataset_urls": DATASET_URLS,
        "download_url": download_url,
        "download_executed": False,
        "notes": [
            "Modo preparado para descarga futura.",
            "Usar recursos ZIP publicos de los datasets oficiales.",
            "No usa credenciales, APIs privadas ni servicios pagos.",
        ],
    }
    if download_url and allow_download:
        target = output_dir / "downloaded" / Path(download_url.split("?")[0]).name
        target.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(download_url, target)
        manifest["download_executed"] = True
        manifest["stored_path"] = str(target)
        manifest["files"] = [describe_file(target)]
        manifest["extracted"] = extract_zip_csvs(target, output_dir) if zipfile.is_zipfile(target) else []
    write_manifest(output_dir / "sepa_download_plan.json", manifest)
    return manifest


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    root = project_root()
    parser = argparse.ArgumentParser(description="Importa o prepara descarga de archivos SEPA.")
    parser.add_argument("--mode", choices=["manual", "download-plan"], required=True)
    parser.add_argument("--input", help="ZIP/CSV local para modo manual.")
    parser.add_argument("--output-dir", default=str(root / "data" / "raw" / "sepa"))
    parser.add_argument("--download-url", help="URL publica futura de un recurso ZIP/CSV SEPA.")
    parser.add_argument("--allow-download", action="store_true", help="Ejecuta descarga si se provee --download-url.")
    args = parser.parse_args()

    try:
        output_dir = Path(args.output_dir)
        if args.mode == "manual":
            if not args.input:
                raise ValueError("El modo manual requiere --input.")
            manifest = manual_import(Path(args.input), output_dir)
        else:
            manifest = download_plan(output_dir, args.download_url, args.allow_download)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({"ok": True, "mode": args.mode, "manifest": manifest}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
