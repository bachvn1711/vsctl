import subprocess

subprocess.run(

    [

        "podman",
        "build",

        "-t",

        "ghcr.io/bachvn1711/databroker:v1.0.0",

        ".",

    ],

    check=True,

)