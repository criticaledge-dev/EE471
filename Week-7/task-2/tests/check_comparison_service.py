"""Real two-model comparison; no training, dataset downloads or service stops."""
import base64
import hashlib
import json
from pathlib import Path
import sys

from http_helpers import command, request, upload, same_scores

ROOT = Path(__file__).resolve().parents[1]
MODELS = {
    "baseline": (5075, "artifacts/baseline/cifar10_last.pth", "results/baseline/reload_reference.json"),
    "optimized": (5076, "artifacts/optimized/cifar10_optimized.pth", "results/hpo/optimized_reload_reference.json"),
}


def main():
    local, direct, before_logs = {}, {}, {}
    for name, (port, checkpoint, reference) in MODELS.items():
        image_name = f"ee471-week7-cifar10-{name}:latest"
        local[name] = json.loads(command("docker", "run", "--rm", "--network", "none", "--entrypoint", "python",
            "--mount", f"type=bind,source={ROOT},target=/work", "--workdir", "/work", image_name,
            "-B", "predict.py", "--checkpoint", checkpoint, "--reference", reference))
        sources = {file: hashlib.sha256((ROOT / file).read_bytes()).hexdigest()
                   for file in ("cog_runner.py", "model.py", "preprocessing.py")}
        script = f'''
from pathlib import Path
from unittest.mock import patch
import hashlib, cog_runner
assert cog_runner.MODEL_NAME == {'cifar10-'+name!r}
assert hashlib.sha256(cog_runner.CHECKPOINT.read_bytes()).hexdigest() == {local[name]['checkpoint_sha256']!r}
assert list(Path('/src').rglob('*.pth')) == [Path('/src/checkpoint.pth')]
for file, expected in {sources!r}.items():
    assert hashlib.sha256(Path('/src',file).read_bytes()).hexdigest() == expected
for file in ['data','train.py','optimize.py','evaluate.py','results','demo_samples','website','.env','.venv']:
    assert not Path('/src',file).exists(),file
r=cog_runner.Runner();r.setup()
assert not r.model.training and next(r.model.parameters()).device.type=='cpu'
with patch.object(cog_runner,'CHECKPOINT',Path('/missing.pth')):
    try:r.setup()
    except RuntimeError as error:assert 'README' in str(error)
    else:raise AssertionError('missing weights accepted')
with patch.dict(cog_runner.CONFIG,sha256='invalid'):
    try:r.setup()
    except RuntimeError as error:assert 'SHA256' in str(error)
    else:raise AssertionError('wrong checkpoint hash accepted')
print('OFFLINE_IMAGE_OK: one correct checkpoint; original identical sources; CPU/eval; safe missing/hash failures')
'''
        print(command("docker", "run", "--rm", "--network", "none", "--entrypoint", "python", image_name, "-B", "-c", script))
    assert local["baseline"]["image"] == local["optimized"]["image"] == "test_00000_label_3_cat.png"
    image = ROOT / "demo_samples" / local["baseline"]["image"]
    print(command(sys.executable, "postman/make_request.py", str(image)))
    body = (ROOT / "outputs/postman-request.json").read_bytes()
    env = json.loads((ROOT / "outputs/postman-environment.json").read_text())
    assert json.loads(env["values"][0]["value"]) == json.loads(body)
    for name, (port, _, _) in MODELS.items():
        code, reply = request(port, "/predictions", body)
        assert code == 200 and reply["status"] == "succeeded", reply
        direct[name] = reply["output"]
        same_scores(local[name]["top3"], direct[name]["top3"])
        assert direct[name]["class"] == local[name]["predicted_class"]
        assert abs(direct[name]["score"] - local[name]["probability"]) <= 1e-7
        before_logs[name] = command("docker", "compose", "--env-file", "/dev/null", "exec", "-T", name,
                                    "cat", f"/var/log/ee471/cifar10-{name}.log")
    code, website = upload(image.read_bytes())
    assert code == 200 and website["status"] == "succeeded", website
    for name in MODELS:
        result = website["results"][name]
        assert result["status"] == "succeeded" and result["output"]["class"] == local[name]["predicted_class"]
        same_scores(local[name]["top3"], result["output"]["top3"])
        assert abs(result["output"]["score"] - local[name]["probability"]) <= 1e-7
        after = command("docker", "compose", "--env-file", "/dev/null", "exec", "-T", name,
                        "cat", f"/var/log/ee471/cifar10-{name}.log")
        assert after.count("Prediction completed") == before_logs[name].count("Prediction completed")+1
        assert f"model=cifar10-{name}" in after and "base64" not in after and "data:image" not in after
        assert "class="+result["output"]["class"] in after.splitlines()[-1]
        print("LOG_EVIDENCE", name, after.splitlines()[-1])
    for data in (b"", b"broken PNG"):
        code, failure = upload(data)
        assert code == 400 and failure.get("error")
    code, failure = request(5074, "/api/classify", b"", "multipart/form-data; boundary=empty")
    assert code == 400 and failure.get("error")
    invalid = json.dumps({"input": {"image": "data:image/png;base64,"+base64.b64encode(b"broken PNG").decode()}}).encode()
    for _, (port, _, _) in MODELS.items():
        code, failure = request(port, "/predictions", invalid)
        assert code == 200 and failure["status"] == "failed" and not failure.get("output")
        code, recovery = request(port, "/predictions", body)
        assert code == 200 and recovery["status"] == "succeeded"
    code, recovery = upload(image.read_bytes())
    assert code == 200 and recovery["status"] == "succeeded"
    # Exercise real JPEG separately: lossy JPEG need not match the original PNG.
    command("docker", "run", "--rm", "--network", "none", "--entrypoint", "python",
            "--mount", f"type=bind,source={ROOT},target=/work", "--workdir", "/work", "ee471-week7-cifar10-baseline",
            "-B", "-c", "from PIL import Image; Image.open('demo_samples/test_00000_label_3_cat.png').convert('RGB').save('outputs/demo-converted.jpg',quality=95)")
    jpeg = (ROOT / "outputs/demo-converted.jpg").read_bytes()
    jpeg_body = json.dumps({"input": {"image": "data:image/jpeg;base64,"+base64.b64encode(jpeg).decode()}}).encode()
    code, jpeg_site = upload(jpeg)
    assert code == 200 and jpeg_site["status"] == "succeeded"
    for name, (port, _, _) in MODELS.items():
        code, reply = request(port, "/predictions", jpeg_body)
        assert code == 200 and reply["status"] == "succeeded"
        same_scores(reply["output"]["top3"], jpeg_site["results"][name]["output"]["top3"])
    report = {"image": image.name, "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
              "python": local, "cog": direct, "website": website["results"], "scores_match": True,
              "absolute_tolerance": 1e-7, "offline_image_checks": True, "logs_verified": list(MODELS),
              "invalid_recovery": True, "real_jpeg_cog_and_website": True, "training_or_dataset_download": False,
              "real_postman_desktop": False}
    (ROOT / "outputs/stage8-comparison.json").write_text(json.dumps(report, indent=2)+"\n")
    print("REAL_COMPARISON", json.dumps(report))


if __name__ == "__main__":
    main()
