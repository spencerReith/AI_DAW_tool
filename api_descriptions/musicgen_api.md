et the REPLICATE_API_TOKEN environment variable

export REPLICATE_API_TOKEN=r8_RKi**********************************

Visibility

Copy
Learn more about authentication

Install Replicate’s Python client library

pip install replicate

Copy
Learn more about setup
Run meta/musicgen using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

import replicate

input = {
    "prompt": "Edo25 major g melodies that sound triumphant and cinematic. Leading up to a crescendo that resolves in a 9th harmonic",
    "model_version": "stereo-large",
    "output_format": "mp3",
    "normalization_strategy": "peak"
}

output = replicate.run(
    "meta/musicgen:671ac645ce5e552cc63a54a2bbff63fcf798043055d2dac5fc9e36a837eedcfb",
    input=input
)

# To access the file URL:
print(output.url)
#=> "https://replicate.delivery/.../output.mp3"

# To write the file to disk:
with open("output.mp3", "wb") as file:
    file.write(output.read())
#=> output.mp3 written to disk