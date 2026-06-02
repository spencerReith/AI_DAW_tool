Use one of our client libraries to get started quickly.


Node.js

Python

HTTP
Set the REPLICATE_API_TOKEN environment variable

export REPLICATE_API_TOKEN=r8_RKi**********************************

Visibility

Copy
Learn more about authentication

Install Replicate’s Python client library

pip install replicate

Copy
Learn more about setup
Run rhelsing/basic-pitch using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

import replicate

input = {
    "audio_file": "https://replicate.delivery/pbxt/IXhQ1wH0SCc1SYrM3q8A5lrRmvrOJluvn4uuiUY2VcEQHVxv/86bpm_G_piano_epic_phmMpU.wav"
}

output = replicate.run(
    "rhelsing/basic-pitch:a7cf33cf63fca9c71f2235332af5a9fdfb7d23c459a0dc429daa203ff8e80c78",
    input=input
)

# To access the file URL:
print(output.url)
#=> "https://replicate.delivery/.../output.mid"

# To write the file to disk:
with open("output.mid", "wb") as file:
    file.write(output.read())
#=> output.mid written to disk