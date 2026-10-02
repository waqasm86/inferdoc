"""Diagnose a previously saved run; requires a live Nemotron call."""

import argparse

import inferdoc
from inferdoc.storage import ArtifactStore

parser = argparse.ArgumentParser()
parser.add_argument("run_id")
parser.add_argument("--artifact-dir", default=".inferdoc/runs")
args = parser.parse_args()
report = inferdoc.diagnose(ArtifactStore(args.artifact_dir).load(args.run_id))
print(report.model_dump_json(indent=2))
