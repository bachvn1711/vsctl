import subprocess


subprocess.run(
    [
        "vspec2json",
        "generated/company.vspec",
        "generated/vss_release_6.0.json",
    ],
    check=True,
)