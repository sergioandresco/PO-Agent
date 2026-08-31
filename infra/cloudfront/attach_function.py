#!/usr/bin/env python3
"""Crea, publica y asocia la CloudFront Function que resuelve las rutas del export.

El export estatico produce un index.html por ruta (out/dashboard/index.html). S3
detras de un Origin Access Control no agrega index.html por su cuenta -- eso solo
lo hace el endpoint de website publico, que no usamos porque el bucket es privado.
Sin esta funcion, /dashboard y /sign-in caen al fallback y sirven la landing.

Idempotente: si la funcion ya existe la actualiza en lugar de fallar.

    python infra/cloudfront/attach_function.py --distribution-id E1VV8OB80DHKIK
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import time

import boto3

COMMENT = "Resuelve rutas del export estatico de Next.js"
RUNTIME = "cloudfront-js-2.0"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--distribution-id", required=True)
    ap.add_argument("--profile", default="po-agent")
    ap.add_argument("--name", default="po-agent-append-index")
    ap.add_argument(
        "--code",
        default=str(pathlib.Path(__file__).with_name("append-index.js")),
    )
    args = ap.parse_args()

    code_path = pathlib.Path(args.code)
    if not code_path.is_file():
        print(f"ERROR: no encuentro {code_path}", file=sys.stderr)
        return 1
    code = code_path.read_bytes()

    cf = boto3.Session(profile_name=args.profile).client("cloudfront")
    config = {"Comment": COMMENT, "Runtime": RUNTIME}

    # 1 -- crear o actualizar en la etapa DEVELOPMENT
    try:
        current = cf.describe_function(Name=args.name, Stage="DEVELOPMENT")
        result = cf.update_function(
            Name=args.name,
            IfMatch=current["ETag"],
            FunctionConfig=config,
            FunctionCode=code,
        )
        print(f"1/4  funcion '{args.name}' actualizada")
    except cf.exceptions.NoSuchFunctionExists:
        result = cf.create_function(
            Name=args.name, FunctionConfig=config, FunctionCode=code
        )
        print(f"1/4  funcion '{args.name}' creada")

    # 2 -- publicar a LIVE (sin esto, CloudFront rechaza la asociacion)
    published = cf.publish_function(Name=args.name, IfMatch=result["ETag"])
    arn = published["FunctionSummary"]["FunctionMetadata"]["FunctionARN"]
    print(f"2/4  publicada a LIVE\n     {arn}")

    # 3 -- asociar al comportamiento de cache por defecto
    dist = cf.get_distribution_config(Id=args.distribution_id)
    dist_config = dist["DistributionConfig"]
    dist_config["DefaultCacheBehavior"]["FunctionAssociations"] = {
        "Quantity": 1,
        "Items": [{"FunctionARN": arn, "EventType": "viewer-request"}],
    }
    cf.update_distribution(
        Id=args.distribution_id,
        IfMatch=dist["ETag"],
        DistributionConfig=dist_config,
    )
    print(f"3/4  asociada a {args.distribution_id} como viewer-request")

    # 4 -- invalidar: los 404 que ya se sirvieron estan cacheados en el edge
    cf.create_invalidation(
        DistributionId=args.distribution_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/*"]},
            "CallerReference": f"attach-function-{int(time.time())}",
        },
    )
    print("4/4  invalidacion /* creada")

    print("\nListo. La distribucion tarda 3-8 minutos en propagar el cambio.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
